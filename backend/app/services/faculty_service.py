"""
Core service for Phase 10: Faculty Intelligence & Academic Intervention Dashboard.

Provides:
1. Faculty authorization scoping (department scope for faculty, global for admin, blocked for students).
2. KPI overview aggregation across authorized student groups.
3. Priority student queue computation with documented transparent priority formula.
4. Comprehensive student intelligence dossiers (Phase 3 + Phase 4 + Phase 5 + Phase 8 + Trend).
5. Aggregate analytics and non-invasive academic alerts.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
import numpy as np
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.academic_record import SemesterAcademicRecord
from backend.app.models.department import Department
from backend.app.models.faculty import FacultyProfile
from backend.app.models.student import StudentProfile
from backend.app.models.user import User, UserRole
from backend.app.schemas.academic_record import AcademicRecordResponse
from backend.app.schemas.explanation import (
    ExplanationSchema,
    FeatureContributionSchema,
)
from backend.app.schemas.faculty import (
    FacultyAcademicAlert,
    FacultyAnalyticsResponse,
    FacultyOverviewResponse,
    FacultyStudentDossier,
    FacultyStudentListResponse,
    FacultyStudentSummary,
    FacultyTopRiskFactor,
    GroupedFacultyRecommendations,
    HistoricalVsPredictedTrend,
)
from backend.app.schemas.prediction import CGPAPredictionRequest
from backend.app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationItemSchema,
    ActionPlanSchema,
)
from backend.app.schemas.risk_prediction import RiskFactorDetail, RiskPredictionRequest
from backend.app.services.prediction_service import prediction_service
from backend.app.services.recommendation_service import recommendation_service
from backend.app.services.risk_service import academic_risk_service
from ml.classification.risk_policy import (
    map_cgpa_to_performance_category,
)
from ml.explainability.explanation_service import explanation_service

logger = logging.getLogger("student_predictor.faculty_service")


class FacultyService:
    @staticmethod
    def resolve_faculty_scope(current_user: User) -> Tuple[Optional[uuid.UUID], Optional[str]]:
        """
        Determines the department scope for the current user.
        - ADMIN: Unrestricted (None), can view all.
        - FACULTY: Scoped to their department_id.
        - STUDENT: Raises PermissionError.
        """
        if current_user.role == UserRole.STUDENT:
            raise PermissionError("Access denied: Student accounts cannot access faculty intelligence.")

        if current_user.role == UserRole.ADMIN:
            return None, "ALL_DEPARTMENTS"

        if current_user.role == UserRole.FACULTY:
            if current_user.faculty_profile and current_user.faculty_profile.department_id:
                dept_id = current_user.faculty_profile.department_id
                dept_code = current_user.faculty_profile.department.code if current_user.faculty_profile.department else None
                return dept_id, dept_code
            return None, "UNASSIGNED"

        raise PermissionError("Unauthorized role for faculty intelligence.")

    @classmethod
    async def verify_faculty_student_access(
        cls, db: AsyncSession, current_user: User, student_id: uuid.UUID
    ) -> StudentProfile:
        """
        Ensures a faculty user can only access students in their authorized department.
        Admins can access any student.
        """
        stmt = (
            select(StudentProfile)
            .where(StudentProfile.id == student_id, StudentProfile.is_archived == False)  # noqa: E712
            .options(
                selectinload(StudentProfile.department),
                selectinload(StudentProfile.academic_records),
            )
        )
        res = await db.execute(stmt)
        student = res.scalar_one_or_none()

        if not student:
            raise ValueError(f"Student with ID '{student_id}' not found or is archived.")

        scope_dept_id, _ = cls.resolve_faculty_scope(current_user)
        if scope_dept_id is not None and student.department_id != scope_dept_id:
            raise PermissionError("Access denied: You are not authorized to view students outside your department.")

        return student

    @classmethod
    def calculate_cgpa_trend(
        cls,
        academic_records: List[SemesterAcademicRecord],
        current_cgpa: Optional[float],
        predicted_cgpa: Optional[float],
    ) -> Tuple[str, Optional[float], str]:
        """
        Evaluates the academic trajectory.
        Returns:
            (trend_direction, delta_cgpa, trend_description)
            trend_direction in ("IMPROVING", "STABLE", "DECLINING", "INSUFFICIENT_DATA")
        """
        if not academic_records and current_cgpa is None:
            return "INSUFFICIENT_DATA", None, "Insufficient recorded semester history to determine trajectory."

        sorted_records = sorted(academic_records, key=lambda r: r.semester)
        
        # Determine baseline for comparison
        prev_sem_cgpa: Optional[float] = None
        if len(sorted_records) >= 2:
            prev_sem_cgpa = float(sorted_records[-2].semester_cgpa or sorted_records[-2].previous_cgpa or 0)
        elif len(sorted_records) == 1 and sorted_records[0].previous_cgpa is not None:
            prev_sem_cgpa = float(sorted_records[0].previous_cgpa)

        eff_current = current_cgpa if current_cgpa is not None else (
            float(sorted_records[-1].semester_cgpa) if sorted_records and sorted_records[-1].semester_cgpa is not None else None
        )

        if eff_current is None:
            return "INSUFFICIENT_DATA", None, "No cumulative or term GPA on record."

        # Calculate delta
        delta = None
        if predicted_cgpa is not None:
            delta = round(predicted_cgpa - eff_current, 2)
            if delta <= -0.4:
                return "DECLINING", delta, f"Predicted semester CGPA ({predicted_cgpa:.2f}) indicates a notable decline (-{abs(delta):.2f}) from current standing ({eff_current:.2f})."
            elif delta >= 0.4:
                return "IMPROVING", delta, f"Predicted semester CGPA ({predicted_cgpa:.2f}) indicates positive momentum (+{delta:.2f}) over current standing ({eff_current:.2f})."

        if prev_sem_cgpa is not None and prev_sem_cgpa > 0:
            hist_delta = round(eff_current - prev_sem_cgpa, 2)
            if hist_delta <= -0.4:
                return "DECLINING", hist_delta, f"Current CGPA ({eff_current:.2f}) reflects a downward shift (-{abs(hist_delta):.2f}) compared to prior term ({prev_sem_cgpa:.2f})."
            elif hist_delta >= 0.4:
                return "IMPROVING", hist_delta, f"Current CGPA ({eff_current:.2f}) reflects improvement (+{hist_delta:.2f}) over prior term ({prev_sem_cgpa:.2f})."

        return "STABLE", delta or 0.0, "Academic performance exhibits stable consistency within ±0.30 CGPA margin."

    @classmethod
    def calculate_priority_score(
        cls,
        risk_level: str,
        risk_score: float,
        attendance_percentage: Optional[float],
        backlogs: int,
        cgpa_trend: str,
    ) -> Tuple[float, str]:
        """
        Documented Transparent Composite Prioritization Formula:
        Priority Score = (0.50 * Risk Score) + (0.25 * Attendance Deficit) + (0.15 * Backlog Penalty) + (0.10 * Trend Penalty)
        
        Inputs:
        - normalized_risk_score: 0.0 - 100.0 from Phase 4 Risk Classifier.
        - attendance_deficit: max(0, (75.0 - attendance) / 75.0 * 100.0) -> heavily flags sub-75% attendance.
        - backlog_penalty: min(100.0, backlogs * 25.0) -> scales with pending failed courses.
        - trend_penalty: 100.0 if DECLINING, 0.0 otherwise.
        
        Range: 0.0 - 100.0
        Tiers:
        - CRITICAL: >= 75.0 or risk_level == 'CRITICAL'
        - HIGH: >= 50.0 or risk_level == 'HIGH'
        - MEDIUM: >= 25.0 or risk_level == 'MEDIUM'
        - LOW: < 25.0
        """
        # Attendance deficit
        att = attendance_percentage if attendance_percentage is not None else 75.0
        att_deficit = max(0.0, (75.0 - att) / 75.0 * 100.0)

        # Backlog penalty
        backlog_penalty = min(100.0, backlogs * 25.0)

        # Trend penalty
        trend_penalty = 100.0 if cgpa_trend == "DECLINING" else (25.0 if cgpa_trend == "INSUFFICIENT_DATA" else 0.0)

        # Weighted calculation
        raw_score = (
            (0.50 * float(risk_score))
            + (0.25 * att_deficit)
            + (0.15 * backlog_penalty)
            + (0.10 * trend_penalty)
        )
        priority_score = round(min(100.0, max(0.0, raw_score)), 1)

        # Categorize tier
        if priority_score >= 75.0 or risk_level == "CRITICAL":
            tier = "CRITICAL"
        elif priority_score >= 50.0 or risk_level == "HIGH":
            tier = "HIGH"
        elif priority_score >= 25.0 or risk_level == "MEDIUM":
            tier = "MEDIUM"
        else:
            tier = "LOW"

        return priority_score, tier

    @classmethod
    async def evaluate_single_student_summary(
        cls,
        student: StudentProfile,
        db: AsyncSession,
    ) -> FacultyStudentSummary:
        """
        Runs ML prediction & risk pipeline on a student profile and builds a FacultyStudentSummary.
        """
        prediction_service.load_artifacts()
        academic_risk_service.load_artifacts()

        records = student.academic_records or []
        latest_rec: Optional[SemesterAcademicRecord] = None
        if records:
            latest_rec = max(records, key=lambda r: r.semester)

        # Build feature vector
        att = float(latest_rec.attendance_percentage) if latest_rec else 75.0
        prev_cgpa = (
            float(latest_rec.previous_cgpa)
            if latest_rec and latest_rec.previous_cgpa is not None
            else (float(student.cumulative_gpa) if student.cumulative_gpa is not None else 7.0)
        )
        mid_1 = float(latest_rec.mid_1) if latest_rec and latest_rec.mid_1 is not None else 70.0
        mid_2 = float(latest_rec.mid_2) if latest_rec and latest_rec.mid_2 is not None else 70.0
        internal = float(latest_rec.internal_marks) if latest_rec and latest_rec.internal_marks is not None else 70.0
        backlogs = latest_rec.backlogs if latest_rec else 0
        current_cgpa = float(student.cumulative_gpa) if student.cumulative_gpa is not None else (
            float(latest_rec.semester_cgpa) if latest_rec and latest_rec.semester_cgpa is not None else None
        )

        dept_code = student.department.code if student.department else "CSE"
        dept_name = student.department.name if student.department else None

        # Predict CGPA
        pred_cgpa: Optional[float] = None
        conf: Optional[float] = None
        conf_cat = "MODERATE"
        try:
            req_cgpa = CGPAPredictionRequest(
                student_number=student.student_number,
                gender=student.gender.value if hasattr(student.gender, "value") else str(student.gender),
                age=student.age,
                department_code=dept_code,
                semester=student.current_semester,
                attendance_percentage=att,
                previous_cgpa=prev_cgpa,
                mid_1=mid_1,
                mid_2=mid_2,
                internal_marks=internal,
                backlogs=backlogs,
            )
            res_cgpa = await prediction_service.predict_cgpa(req_cgpa, db=db, current_user=None)
            pred_cgpa = res_cgpa.predicted_cgpa
            conf = res_cgpa.confidence_score
            conf_cat = res_cgpa.confidence_category
        except Exception as e:
            logger.debug(f"CGPA prediction skipped for {student.student_number}: {e}")

        # Predict Risk
        risk_level = "LOW"
        risk_score = 0.0
        top_factors = []
        try:
            req_risk = RiskPredictionRequest(
                student_number=student.student_number,
                gender=student.gender.value if hasattr(student.gender, "value") else str(student.gender),
                age=student.age,
                department_code=dept_code,
                semester=student.current_semester,
                attendance_percentage=att,
                previous_cgpa=prev_cgpa,
                mid_1=mid_1,
                mid_2=mid_2,
                internal_marks=internal,
                backlogs=backlogs,
            )
            res_risk = await academic_risk_service.predict_risk(req_risk, db=db, current_user=None)
            risk_level = res_risk.risk_level
            risk_score = res_risk.risk_score
            # Extract top contributing factor names
            if res_risk.risk_factors:
                for rf in res_risk.risk_factors:
                    if getattr(rf, "level", "") in ("HIGH", "CRITICAL"):
                        top_factors.append(getattr(rf, "factor", ""))
        except Exception as e:

            logger.debug(f"Risk prediction skipped for {student.student_number}: {e}")

        # Trend & Priority
        trend_dir, _, _ = cls.calculate_cgpa_trend(records, current_cgpa, pred_cgpa)
        p_score, p_tier = cls.calculate_priority_score(risk_level, risk_score, att, backlogs, trend_dir)

        return FacultyStudentSummary(
            id=student.id,
            student_number=student.student_number,
            name=student.name,
            department_id=student.department_id,
            department_code=dept_code,
            department_name=dept_name,
            current_semester=student.current_semester,
            gender=student.gender.value if hasattr(student.gender, "value") else str(student.gender),
            current_cgpa=current_cgpa,
            predicted_cgpa=pred_cgpa,
            risk_level=risk_level,
            risk_score=risk_score,
            priority_score=p_score,
            priority_tier=p_tier,
            attendance_percentage=att if latest_rec else None,
            backlogs=backlogs,
            cgpa_trend=trend_dir,
            top_risk_factors=top_factors[:3],
            prediction_confidence=conf,
            confidence_category=conf_cat,
            last_evaluated_at=datetime.now(timezone.utc),
        )

    @classmethod
    async def get_faculty_overview(
        cls,
        db: AsyncSession,
        current_user: User,
        department_id: Optional[uuid.UUID] = None,
    ) -> FacultyOverviewResponse:
        """
        Aggregates KPI metrics, risk distributions, performance categories,
        top common risk factors, and actionable academic alerts across authorized students.
        """
        scope_dept_id, scope_code = cls.resolve_faculty_scope(current_user)
        target_dept_id = scope_dept_id or department_id

        # Query active authorized students with records & department
        query = (
            select(StudentProfile)
            .where(StudentProfile.is_archived == False)  # noqa: E712
            .options(
                selectinload(StudentProfile.department),
                selectinload(StudentProfile.academic_records),
            )
        )
        if target_dept_id:
            query = query.where(StudentProfile.department_id == target_dept_id)

        res = await db.execute(query)
        students = list(res.scalars().all())

        if not students:
            dept_name = None
            if target_dept_id:
                dept = await db.get(Department, target_dept_id)
                dept_name = dept.name if dept else None
            return FacultyOverviewResponse(
                students_monitored=0,
                average_current_cgpa=None,
                average_predicted_cgpa=None,
                risk_distribution={"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
                attendance_overview={"average_attendance": None, "below_75_count": 0, "below_65_count": 0},
                backlog_overview={"total_backlogs": 0, "students_with_backlogs": 0, "students_with_backlogs_pct": 0.0},
                performance_categories={"EXCELLENT": 0, "GOOD": 0, "AVERAGE": 0, "AT_RISK": 0},
                top_risk_factors=[],
                recent_alerts=[],
                department_scope=scope_code or (str(target_dept_id) if target_dept_id else "ALL_DEPARTMENTS"),
                department_name=dept_name,
                last_analysis_timestamp=datetime.now(timezone.utc),
            )

        # Batch summarize students
        summaries: List[FacultyStudentSummary] = []
        for s in students:
            summary = await cls.evaluate_single_student_summary(s, db)
            summaries.append(summary)

        total_monitored = len(summaries)
        
        # Calculate CGPA metrics
        valid_cgpas = [s.current_cgpa for s in summaries if s.current_cgpa is not None]
        avg_cgpa = round(float(np.mean(valid_cgpas)), 2) if valid_cgpas else None

        valid_pred_cgpas = [s.predicted_cgpa for s in summaries if s.predicted_cgpa is not None]
        avg_pred_cgpa = round(float(np.mean(valid_pred_cgpas)), 2) if valid_pred_cgpas else None

        # Risk distribution
        risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for s in summaries:
            if s.risk_level in risk_dist:
                risk_dist[s.risk_level] += 1
            else:
                risk_dist["LOW"] += 1

        # Attendance metrics
        valid_atts = [s.attendance_percentage for s in summaries if s.attendance_percentage is not None]
        avg_att = round(float(np.mean(valid_atts)), 1) if valid_atts else None
        below_75 = sum(1 for a in valid_atts if a < 75.0)
        below_65 = sum(1 for a in valid_atts if a < 65.0)

        # Backlog metrics
        total_backlogs = sum(s.backlogs for s in summaries)
        students_with_backlogs = sum(1 for s in summaries if s.backlogs > 0)
        backlog_pct = round((students_with_backlogs / total_monitored) * 100.0, 1) if total_monitored > 0 else 0.0

        # Performance categories
        perf_cats = {"EXCELLENT": 0, "GOOD": 0, "AVERAGE": 0, "AT_RISK": 0}
        for s in summaries:
            eff_cgpa = s.current_cgpa or s.predicted_cgpa or 7.0
            cat = map_cgpa_to_performance_category(eff_cgpa)
            if cat in perf_cats:
                perf_cats[cat] += 1

        # Aggregate top risk factors across student population
        factor_counts: Dict[str, Dict[str, Any]] = {
            "Attendance Deficit": {
                "feature_code": "attendance_percentage",
                "count": below_75,
                "severity": "CRITICAL" if below_65 > 0 else "HIGH",
                "desc": "Attendance falling below institutional 75% examination eligibility minimum.",
            },
            "Active Course Backlogs": {
                "feature_code": "backlogs",
                "count": students_with_backlogs,
                "severity": "CRITICAL" if any(s.backlogs >= 3 for s in summaries) else "HIGH",
                "desc": "Pending backlog courses creating compounding credit & prerequisite pressure.",
            },
            "Declining Performance Trajectory": {
                "feature_code": "cgpa_trend",
                "count": sum(1 for s in summaries if s.cgpa_trend == "DECLINING"),
                "severity": "HIGH",
                "desc": "Semester GPA indicating downward shift compared to prior academic standing.",
            },
            "Sub-6.0 CGPA Performance": {
                "feature_code": "previous_cgpa",
                "count": sum(1 for s in summaries if s.current_cgpa is not None and s.current_cgpa < 6.0),
                "severity": "HIGH",
                "desc": "Cumulative standing in lower quartile requiring targeted academic support.",
            },
        }
        top_factors = [
            FacultyTopRiskFactor(
                factor_name=name,
                feature_code=info["feature_code"],
                affected_students_count=info["count"],
                severity=info["severity"],
                description=info["desc"],
            )
            for name, info in factor_counts.items()
            if info["count"] > 0
        ]
        top_factors.sort(key=lambda x: x.affected_students_count, reverse=True)

        # Generate evidence-grounded non-invasive alerts
        alerts: List[FacultyAcademicAlert] = []
        if risk_dist["CRITICAL"] > 0:
            crit_students = [s.student_number for s in summaries if s.risk_level == "CRITICAL"]
            alerts.append(
                FacultyAcademicAlert(
                    id="ALERT_CRITICAL_RISK",
                    alert_type="RISK_ELEVATED",
                    severity="CRITICAL",
                    title="Critical Risk Threshold Reached",
                    description=f"{risk_dist['CRITICAL']} student(s) exhibit severe multi-factor academic risk requiring priority advising.",
                    affected_count=risk_dist["CRITICAL"],
                    student_ids=crit_students[:5],
                    recommended_action="Initiate one-on-one academic counseling and review individual SHAP dossiers.",
                )
            )

        if below_65 > 0:
            att_crit_students = [s.student_number for s in summaries if (s.attendance_percentage or 100) < 65.0]
            alerts.append(
                FacultyAcademicAlert(
                    id="ALERT_ATTENDANCE_CRITICAL",
                    alert_type="ATTENDANCE_CRITICAL",
                    severity="HIGH",
                    title="Severe Attendance Deficit (<65%)",
                    description=f"{below_65} student(s) have attendance below 65%, jeopardizing course completion prerequisites.",
                    affected_count=below_65,
                    student_ids=att_crit_students[:5],
                    recommended_action="Issue attendance advisory notices and verify underlying medical or personal circumstances.",
                )
            )

        high_backlogs_count = sum(1 for s in summaries if s.backlogs >= 2)
        if high_backlogs_count > 0:
            bl_students = [s.student_number for s in summaries if s.backlogs >= 2]
            alerts.append(
                FacultyAcademicAlert(
                    id="ALERT_HIGH_BACKLOGS",
                    alert_type="HIGH_BACKLOGS",
                    severity="HIGH",
                    title="Multiple Active Backlogs (≥2)",
                    description=f"{high_backlogs_count} student(s) have 2 or more pending backlogs impacting course progression.",
                    affected_count=high_backlogs_count,
                    student_ids=bl_students[:5],
                    recommended_action="Structure remedial course schedules and recommend peer tutoring sessions.",
                )
            )

        declining_count = sum(1 for s in summaries if s.cgpa_trend == "DECLINING")
        if declining_count > 0:
            dec_students = [s.student_number for s in summaries if s.cgpa_trend == "DECLINING"]
            alerts.append(
                FacultyAcademicAlert(
                    id="ALERT_CGPA_DROP",
                    alert_type="CGPA_DROP",
                    severity="MEDIUM",
                    title="Declining Performance Trajectory",
                    description=f"{declining_count} student(s) show a downward trajectory in predicted or semester CGPA.",
                    affected_count=declining_count,
                    student_ids=dec_students[:5],
                    recommended_action="Review midterm assessments and offer targeted subject tutorials before final exams.",
                )
            )

        dept_name = None
        if target_dept_id and students and students[0].department:
            dept_name = students[0].department.name

        return FacultyOverviewResponse(
            students_monitored=total_monitored,
            average_current_cgpa=avg_cgpa,
            average_predicted_cgpa=avg_pred_cgpa,
            risk_distribution=risk_dist,
            attendance_overview={
                "average_attendance": avg_att,
                "below_75_count": below_75,
                "below_65_count": below_65,
            },
            backlog_overview={
                "total_backlogs": total_backlogs,
                "students_with_backlogs": students_with_backlogs,
                "students_with_backlogs_pct": backlog_pct,
            },
            performance_categories=perf_cats,
            top_risk_factors=top_factors,
            recent_alerts=alerts,
            department_scope=scope_code or (str(target_dept_id) if target_dept_id else "ALL_DEPARTMENTS"),
            department_name=dept_name,
            last_analysis_timestamp=datetime.now(timezone.utc),
        )

    @classmethod
    async def get_faculty_students(
        cls,
        db: AsyncSession,
        current_user: User,
        search: Optional[str] = None,
        risk_level: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        semester: Optional[int] = None,
        min_attendance: Optional[float] = None,
        max_attendance: Optional[float] = None,
        min_cgpa: Optional[float] = None,
        max_cgpa: Optional[float] = None,
        has_backlogs: Optional[bool] = None,
        sort_by: str = "priority",
        page: int = 1,
        limit: int = 20,
    ) -> FacultyStudentListResponse:
        """
        Returns a paginated list of students in the priority queue with rich multi-filter support.
        Default sorting prioritizes students with the highest composite intervention urgency.
        """
        scope_dept_id, _ = cls.resolve_faculty_scope(current_user)
        target_dept_id = scope_dept_id or department_id

        # Base DB query
        query = (
            select(StudentProfile)
            .where(StudentProfile.is_archived == False)  # noqa: E712
            .options(
                selectinload(StudentProfile.department),
                selectinload(StudentProfile.academic_records),
            )
        )
        if target_dept_id:
            query = query.where(StudentProfile.department_id == target_dept_id)
        if semester:
            query = query.where(StudentProfile.current_semester == semester)
        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    StudentProfile.name.ilike(term),
                    StudentProfile.student_number.ilike(term),
                )
            )

        res = await db.execute(query)
        all_students = list(res.scalars().all())

        # Evaluate summaries
        summaries: List[FacultyStudentSummary] = []
        for s in all_students:
            summary = await cls.evaluate_single_student_summary(s, db)
            summaries.append(summary)

        # Count risk categories across total matching scope before filtering by risk
        risk_counts = {
            "ALL": len(summaries),
            "CRITICAL": sum(1 for s in summaries if s.risk_level == "CRITICAL"),
            "HIGH": sum(1 for s in summaries if s.risk_level == "HIGH"),
            "MEDIUM": sum(1 for s in summaries if s.risk_level == "MEDIUM"),
            "LOW": sum(1 for s in summaries if s.risk_level == "LOW"),
        }

        # Apply in-memory intelligence filters
        filtered = summaries
        if risk_level and risk_level.upper() != "ALL":
            filtered = [s for s in filtered if s.risk_level.upper() == risk_level.upper()]

        if min_attendance is not None:
            filtered = [s for s in filtered if s.attendance_percentage is not None and s.attendance_percentage >= min_attendance]
        if max_attendance is not None:
            filtered = [s for s in filtered if s.attendance_percentage is not None and s.attendance_percentage <= max_attendance]

        if min_cgpa is not None:
            filtered = [s for s in filtered if s.current_cgpa is not None and s.current_cgpa >= min_cgpa]
        if max_cgpa is not None:
            filtered = [s for s in filtered if s.current_cgpa is not None and s.current_cgpa <= max_cgpa]

        if has_backlogs is not None:
            if has_backlogs:
                filtered = [s for s in filtered if s.backlogs > 0]
            else:
                filtered = [s for s in filtered if s.backlogs == 0]

        # Sorting logic
        if sort_by == "priority":
            filtered.sort(key=lambda s: (s.priority_score, s.risk_score), reverse=True)
        elif sort_by == "risk_score_desc":
            filtered.sort(key=lambda s: s.risk_score, reverse=True)
        elif sort_by == "risk_score_asc":
            filtered.sort(key=lambda s: s.risk_score, reverse=False)
        elif sort_by == "cgpa_asc":
            filtered.sort(key=lambda s: (s.current_cgpa if s.current_cgpa is not None else 999.0))
        elif sort_by == "cgpa_desc":
            filtered.sort(key=lambda s: (s.current_cgpa if s.current_cgpa is not None else -1.0), reverse=True)
        elif sort_by == "attendance_asc":
            filtered.sort(key=lambda s: (s.attendance_percentage if s.attendance_percentage is not None else 999.0))
        elif sort_by == "backlogs_desc":
            filtered.sort(key=lambda s: s.backlogs, reverse=True)
        elif sort_by == "name_asc":
            filtered.sort(key=lambda s: s.name.lower())
        elif sort_by == "student_number_asc":
            filtered.sort(key=lambda s: s.student_number)
        else:
            filtered.sort(key=lambda s: s.priority_score, reverse=True)

        total = len(filtered)
        pages = (total + limit - 1) // limit if total > 0 else 1
        offset = (page - 1) * limit
        paginated_items = filtered[offset : offset + limit]

        return FacultyStudentListResponse(
            items=paginated_items,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            risk_counts=risk_counts,
        )

    @classmethod
    async def get_faculty_student_dossier(
        cls,
        db: AsyncSession,
        current_user: User,
        student_id: uuid.UUID,
    ) -> FacultyStudentDossier:
        """
        Assembles comprehensive academic intelligence for a selected student:
        1. Profile & historical semester records.
        2. Longitudinal trend analysis.
        3. Phase 3 CGPA prediction with confidence and intervals.
        4. Phase 4 Risk prediction with normalized score and 5-factor breakdown.
        5. Phase 5 SHAP local factor attributions with professional faculty framing.
        6. Phase 8 Action Recommendations grouped for faculty intervention (Immediate / Short-Term / Monitor).
        """
        student = await cls.verify_faculty_student_access(db, current_user, student_id)
        summary = await cls.evaluate_single_student_summary(student, db)

        records = student.academic_records or []
        sorted_records = sorted(records, key=lambda r: r.semester)
        
        # Build academic history response
        history_response = [
            AcademicRecordResponse(
                id=r.id,
                student_id=r.student_id,
                academic_year=r.academic_year,
                semester=r.semester,
                attendance_percentage=float(r.attendance_percentage),
                previous_cgpa=float(r.previous_cgpa) if r.previous_cgpa is not None else None,
                mid_1=float(r.mid_1) if r.mid_1 is not None else None,
                mid_2=float(r.mid_2) if r.mid_2 is not None else None,
                internal_marks=float(r.internal_marks) if r.internal_marks is not None else None,
                backlogs=r.backlogs,
                semester_cgpa=float(r.semester_cgpa) if r.semester_cgpa is not None else None,
                grade=r.grade,
                historical_risk_level=r.historical_risk_level,
                notes=r.notes,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in sorted_records
        ]

        # Trend analysis
        trend_dir, delta, trend_desc = cls.calculate_cgpa_trend(
            sorted_records, summary.current_cgpa, summary.predicted_cgpa
        )
        semester_history_summary = [
            {
                "semester": r.semester,
                "academic_year": r.academic_year,
                "semester_cgpa": float(r.semester_cgpa) if r.semester_cgpa is not None else None,
                "attendance": float(r.attendance_percentage),
                "backlogs": r.backlogs,
            }
            for r in sorted_records
        ]
        trend_obj = HistoricalVsPredictedTrend(
            semester_history=semester_history_summary,
            current_cgpa=summary.current_cgpa,
            predicted_cgpa=summary.predicted_cgpa,
            trend_direction=trend_dir,
            delta_cgpa=delta,
            trend_description=trend_desc,
        )

        # Run Phase 4 & Phase 5 with detailed breakdown
        risk_breakdown: Optional[List[RiskFactorDetail]] = None

        explanation_schema: Optional[ExplanationSchema] = None
        faculty_explanation_summary = (
            "Model analysis indicates standard academic performance within established parameters."
        )

        latest_rec = sorted_records[-1] if sorted_records else None
        att = float(latest_rec.attendance_percentage) if latest_rec else 75.0
        prev_cgpa = (
            float(latest_rec.previous_cgpa)
            if latest_rec and latest_rec.previous_cgpa is not None
            else (float(student.cumulative_gpa) if student.cumulative_gpa is not None else 7.0)
        )
        mid_1 = float(latest_rec.mid_1) if latest_rec and latest_rec.mid_1 is not None else 70.0
        mid_2 = float(latest_rec.mid_2) if latest_rec and latest_rec.mid_2 is not None else 70.0
        internal = float(latest_rec.internal_marks) if latest_rec and latest_rec.internal_marks is not None else 70.0
        backlogs = latest_rec.backlogs if latest_rec else 0
        dept_code = student.department.code if student.department else "CSE"

        try:
            req_risk = RiskPredictionRequest(
                student_number=student.student_number,
                gender=student.gender.value if hasattr(student.gender, "value") else str(student.gender),
                age=student.age,
                department_code=dept_code,
                semester=student.current_semester,
                attendance_percentage=att,
                previous_cgpa=prev_cgpa,
                mid_1=mid_1,
                mid_2=mid_2,
                internal_marks=internal,
                backlogs=backlogs,
            )
            res_risk = await academic_risk_service.predict_risk(req_risk, db=db, current_user=None)
            risk_breakdown = res_risk.risk_factors

            # Run SHAP Explainability
            req_cgpa = CGPAPredictionRequest(
                student_number=student.student_number,
                gender=student.gender.value if hasattr(student.gender, "value") else str(student.gender),
                age=student.age,
                department_code=dept_code,
                semester=student.current_semester,
                attendance_percentage=att,
                previous_cgpa=prev_cgpa,
                mid_1=mid_1,
                mid_2=mid_2,
                internal_marks=internal,
                backlogs=backlogs,
            )
            raw_df, _ = await prediction_service.prepare_input_dataframe(req_cgpa, db, None)
            featured_df = prediction_service._feature_engineer.transform(raw_df)
            current_features = featured_df.iloc[[-1]].copy()
            transformed_matrix = academic_risk_service._preprocessor.transform(current_features)
            if hasattr(transformed_matrix, "values"):
                transformed_matrix = transformed_matrix.values
            transformed_matrix = np.array(transformed_matrix, dtype=float)

            feature_values_raw = {
                "attendance_percentage": att,
                "previous_cgpa": prev_cgpa,
                "mid_1": mid_1,
                "mid_2": mid_2,
                "internal_marks": internal,
                "backlogs": float(backlogs),
                "age": float(student.age),
                "semester": float(student.current_semester),
                "academic_average": float(current_features["academic_average"].iloc[0]) if "academic_average" in current_features.columns else 0.0,
                "attendance_risk_score": float(current_features["attendance_risk_score"].iloc[0]) if "attendance_risk_score" in current_features.columns else 0.0,
                "mid_term_average": (mid_1 + mid_2) / 2.0,
                "backlog_severity_score": float(current_features["backlog_severity_score"].iloc[0]) if "backlog_severity_score" in current_features.columns else 0.0,
            }

            ml_exp = explanation_service.explain_risk_prediction(
                transformed_X=transformed_matrix,
                feature_values_raw=feature_values_raw,
                predicted_risk_level=res_risk.risk_level,
            )
            explanation_schema = ExplanationSchema(
                model_name=ml_exp.model_name,
                model_version=ml_exp.model_version,
                model_type=ml_exp.model_type,
                explainer_type=ml_exp.explainer_type,
                explanation_available=ml_exp.explanation_available,
                task_type=ml_exp.task_type,
                explained_class=ml_exp.explained_class,
                top_factors=[FeatureContributionSchema(**f.model_dump()) for f in ml_exp.top_factors],
                positive_factors=[FeatureContributionSchema(**f.model_dump()) for f in ml_exp.positive_factors],
                negative_factors=[FeatureContributionSchema(**f.model_dump()) for f in ml_exp.negative_factors],
                base_value=ml_exp.base_value,
                shap_sum=ml_exp.shap_sum,
                top_global_features=ml_exp.top_global_features,
                fairness_note=ml_exp.fairness_note,
                contains_demographic_factors=ml_exp.contains_demographic_factors,
            )

            # Professional faculty framing
            top_names = [f.feature_name for f in ml_exp.top_factors[:2]]
            if top_names:
                faculty_explanation_summary = (
                    f"The risk model identifies {', '.join(top_names)} as the strongest contributing "
                    f"features for this student's current '{res_risk.risk_level}' classification."
                )
        except Exception as e:
            logger.warning(f"Error computing XAI for student dossier {student.student_number}: {e}")

        # Run Phase 8 Recommendations
        rec_grouped = GroupedFacultyRecommendations()
        action_plan: Optional[ActionPlanTimeline] = None
        try:
            req_rec = RecommendationRequest(
                student_number=student.student_number,
                gender=student.gender.value if hasattr(student.gender, "value") else str(student.gender),
                age=student.age,
                department_code=dept_code,
                semester=student.current_semester,
                attendance_percentage=att,
                previous_cgpa=prev_cgpa,
                mid_1=mid_1,
                mid_2=mid_2,
                internal_marks=internal,
                backlogs=backlogs,
            )
            res_rec = await recommendation_service.generate_recommendations(req_rec, db=db, current_user=None)
            
            # Group recommendations into Immediate Attention, Short Term, and Monitor
            all_recs = res_rec.recommendations or []
            for r in all_recs:
                if r.time_horizon == "THIS_WEEK" or r.priority in ("CRITICAL", "HIGH"):
                    rec_grouped.immediate_attention.append(r)
                elif r.time_horizon == "NEXT_30_DAYS":
                    rec_grouped.short_term.append(r)
                else:
                    rec_grouped.monitor.append(r)

            action_plan = res_rec.action_plan
        except Exception as e:
            logger.warning(f"Error computing recommendations for student dossier {student.student_number}: {e}")


        return FacultyStudentDossier(
            student=summary,
            academic_history=history_response,
            trend_analysis=trend_obj,
            predicted_cgpa=summary.predicted_cgpa,
            prediction_confidence=summary.prediction_confidence,
            feature_summary={
                "attendance": att,
                "previous_cgpa": prev_cgpa,
                "mid_terms_avg": (mid_1 + mid_2) / 2.0,
                "internal_marks": internal,
                "backlogs": backlogs,
            },
            risk_level=summary.risk_level,
            risk_score=summary.risk_score,
            risk_factors_breakdown=risk_breakdown,
            explanation=explanation_schema,
            faculty_explanation_summary=faculty_explanation_summary,
            grouped_recommendations=rec_grouped,
            action_plan=action_plan,
            model_version="cgpa_v1.0.0",
            risk_model_version="risk_v1.0.0",
            evaluated_at=datetime.now(timezone.utc),
        )

    @classmethod
    async def get_faculty_analytics(
        cls,
        db: AsyncSession,
        current_user: User,
        department_id: Optional[uuid.UUID] = None,
    ) -> FacultyAnalyticsResponse:
        """
        Aggregate analytical breakdown of student distributions across CGPA tiers,
        attendance bands, backlog counts, semester risk hotspots, and model features.
        """
        scope_dept_id, scope_code = cls.resolve_faculty_scope(current_user)
        target_dept_id = scope_dept_id or department_id

        query = (
            select(StudentProfile)
            .where(StudentProfile.is_archived == False)  # noqa: E712
            .options(
                selectinload(StudentProfile.department),
                selectinload(StudentProfile.academic_records),
            )
        )
        if target_dept_id:
            query = query.where(StudentProfile.department_id == target_dept_id)

        res = await db.execute(query)
        students = list(res.scalars().all())

        summaries: List[FacultyStudentSummary] = []
        for s in students:
            summary = await cls.evaluate_single_student_summary(s, db)
            summaries.append(summary)

        total = len(summaries)
        risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        perf_dist = {"EXCELLENT": 0, "GOOD": 0, "AVERAGE": 0, "AT_RISK": 0}
        cgpa_dist = {"<6.0": 0, "6.0-7.0": 0, "7.0-8.0": 0, "8.0-9.0": 0, ">=9.0": 0}
        att_dist = {"<65%": 0, "65%-75%": 0, "75%-85%": 0, ">=85%": 0}
        backlog_dist = {"0": 0, "1-2": 0, "3-4": 0, ">=5": 0}

        semester_groups: Dict[int, Dict[str, Any]] = {}

        for s in summaries:
            # Risk
            risk_dist[s.risk_level] = risk_dist.get(s.risk_level, 0) + 1

            # Performance
            eff_cgpa = s.current_cgpa or s.predicted_cgpa or 7.0
            cat = map_cgpa_to_performance_category(eff_cgpa)
            perf_dist[cat] = perf_dist.get(cat, 0) + 1

            # CGPA bands
            if eff_cgpa < 6.0:
                cgpa_dist["<6.0"] += 1
            elif eff_cgpa < 7.0:
                cgpa_dist["6.0-7.0"] += 1
            elif eff_cgpa < 8.0:
                cgpa_dist["7.0-8.0"] += 1
            elif eff_cgpa < 9.0:
                cgpa_dist["8.0-9.0"] += 1
            else:
                cgpa_dist[">=9.0"] += 1

            # Attendance bands
            att = s.attendance_percentage or 75.0
            if att < 65.0:
                att_dist["<65%"] += 1
            elif att < 75.0:
                att_dist["65%-75%"] += 1
            elif att < 85.0:
                att_dist["75%-85%"] += 1
            else:
                att_dist[">=85%"] += 1

            # Backlog bands
            if s.backlogs == 0:
                backlog_dist["0"] += 1
            elif s.backlogs <= 2:
                backlog_dist["1-2"] += 1
            elif s.backlogs <= 4:
                backlog_dist["3-4"] += 1
            else:
                backlog_dist[">=5"] += 1

            # Semester hotspots
            sem = s.current_semester
            if sem not in semester_groups:
                semester_groups[sem] = {
                    "semester": sem,
                    "student_count": 0,
                    "high_critical_count": 0,
                    "average_cgpa": [],
                    "average_attendance": [],
                }
            semester_groups[sem]["student_count"] += 1
            if s.risk_level in ("HIGH", "CRITICAL"):
                semester_groups[sem]["high_critical_count"] += 1
            if s.current_cgpa is not None:
                semester_groups[sem]["average_cgpa"].append(s.current_cgpa)
            if s.attendance_percentage is not None:
                semester_groups[sem]["average_attendance"].append(s.attendance_percentage)

        hotspots = []
        for sem, data in sorted(semester_groups.items()):
            avg_c = round(float(np.mean(data["average_cgpa"])), 2) if data["average_cgpa"] else None
            avg_a = round(float(np.mean(data["average_attendance"])), 1) if data["average_attendance"] else None
            hotspots.append({
                "semester": sem,
                "student_count": data["student_count"],
                "high_critical_count": data["high_critical_count"],
                "high_critical_pct": round((data["high_critical_count"] / data["student_count"]) * 100.0, 1) if data["student_count"] > 0 else 0.0,
                "average_cgpa": avg_c,
                "average_attendance": avg_a,
            })

        top_model_factors = [
            FacultyTopRiskFactor(
                factor_name="Attendance Deficit",
                feature_code="attendance_percentage",
                affected_students_count=att_dist["<65%"] + att_dist["65%-75%"],
                severity="HIGH",
                description="Low attendance rate directly affecting continuous internal evaluation and eligibility.",
            ),
            FacultyTopRiskFactor(
                factor_name="Pending Backlogs",
                feature_code="backlogs",
                affected_students_count=backlog_dist["1-2"] + backlog_dist["3-4"] + backlog_dist[">=5"],
                severity="HIGH",
                description="Active backlog subjects increasing workload and academic stress.",
            ),
            FacultyTopRiskFactor(
                factor_name="Sub-6.0 CGPA Performance",
                feature_code="previous_cgpa",
                affected_students_count=cgpa_dist["<6.0"],
                severity="HIGH",
                description="Cumulative GPA in at-risk band requiring foundational academic reinforcement.",
            ),
        ]

        return FacultyAnalyticsResponse(
            department_scope=scope_code or (str(target_dept_id) if target_dept_id else "ALL_DEPARTMENTS"),
            total_students=total,
            risk_distribution=risk_dist,
            performance_distribution=perf_dist,
            cgpa_distribution=cgpa_dist,
            attendance_distribution=att_dist,
            backlog_distribution=backlog_dist,
            top_model_risk_factors=top_model_factors,
            semester_risk_hotspots=hotspots,
            generated_at=datetime.now(timezone.utc),
        )


faculty_service = FacultyService()
