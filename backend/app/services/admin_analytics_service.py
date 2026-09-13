"""
Core service for Phase 13: System-wide Analytics & Admin Intelligence.

Provides institution-level aggregated metrics across:
1. System Overview (monitored counts, CGPA averages, risk distribution, alert volumes).
2. Risk Intelligence (department breakdowns, semester trends, attendance correlation).
3. Academic Performance (CGPA distributions, backlogs, attendance health).
4. Department & Semester comparative intelligence.
5. Intervention & Outcome system analytics (completion rates, measured outcome distribution with observational phrasing).
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import func, or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.academic_record import SemesterAcademicRecord
from backend.app.models.department import Department
from backend.app.models.faculty import FacultyProfile
from backend.app.models.intervention import (
    Intervention,
    InterventionCategory,
    InterventionOutcome,
    InterventionPriority,
    InterventionStatus,
    OutcomeStatus,
)
from backend.app.models.prediction import Prediction
from backend.app.models.student import StudentProfile
from backend.app.models.user import User, UserRole
from backend.app.schemas.admin_analytics import (
    AdminAcademicPerformanceAnalytics,
    AdminDepartmentAnalyticsResponse,
    AdminInterventionsAnalytics,
    AdminOverviewAnalytics,
    AdminRiskAnalytics,
    AdminSemesterAnalyticsResponse,
    AttendanceVsRiskBucket,
    DepartmentPerformanceItem,
    DepartmentRiskItem,
    SemesterRiskItem,
)

logger = logging.getLogger("student_predictor.admin_analytics_service")


class AdminAnalyticsService:
    @classmethod
    async def get_overview(
        cls,
        db: AsyncSession,
        department_id: Optional[uuid.UUID] = None,
        semester: Optional[int] = None,
    ) -> AdminOverviewAnalytics:
        """
        Gathers system-wide overview KPI metrics.
        """
        # Base student query
        student_query = (
            select(StudentProfile)
            .where(StudentProfile.is_archived == False)  # noqa: E712
            .options(
                selectinload(StudentProfile.department),
                selectinload(StudentProfile.academic_records),
            )
        )
        if department_id:
            student_query = student_query.where(StudentProfile.department_id == department_id)
        if semester:
            student_query = student_query.where(StudentProfile.current_semester == semester)

        res = await db.execute(student_query)
        students = res.scalars().all()

        total_students = len(students)
        active_students = total_students

        # Fetch all departments and faculty counts
        dept_count_res = await db.execute(select(func.count(Department.id)))
        total_departments = dept_count_res.scalar() or 0

        faculty_count_res = await db.execute(select(func.count(FacultyProfile.id)))
        total_faculty = faculty_count_res.scalar() or 0

        # Latest predictions for students
        student_ids = [s.id for s in students]
        latest_predictions = await cls._get_latest_predictions_for_students(db, student_ids)

        cgpas: List[float] = []
        pred_cgpas: List[float] = []
        risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        attention_count = 0

        for s in students:
            if s.cumulative_gpa is not None:
                cgpas.append(float(s.cumulative_gpa))

            pred = latest_predictions.get(s.id)
            if pred and pred.predicted_cgpa is not None:
                pred_cgpas.append(float(pred.predicted_cgpa))
            elif s.cumulative_gpa is not None:
                pred_cgpas.append(float(s.cumulative_gpa))

            risk = pred.risk_level if pred else "LOW"
            if risk == "MODERATE":
                risk = "MEDIUM"
            if risk not in risk_dist:
                risk_dist[risk] = 0
            risk_dist[risk] += 1

            # Determine if attention required
            records = sorted(s.academic_records, key=lambda r: r.semester, reverse=True) if s.academic_records else []
            latest_rec = records[0] if records else None
            att = float(latest_rec.attendance_percentage) if (latest_rec and latest_rec.attendance_percentage is not None) else 100.0
            backlogs = latest_rec.backlogs if latest_rec else 0


            if risk in ("HIGH", "CRITICAL") or att < 75.0 or backlogs > 0:
                attention_count += 1

        avg_cgpa = round(sum(cgpas) / len(cgpas), 2) if cgpas else None
        avg_pred_cgpa = round(sum(pred_cgpas) / len(pred_cgpas), 2) if pred_cgpas else None

        risk_pcts: Dict[str, float] = {}
        for r_key, count in risk_dist.items():
            risk_pcts[r_key] = round((count / total_students * 100.0), 1) if total_students > 0 else 0.0

        # Interventions summary
        inv_query = select(Intervention)
        if department_id:
            inv_query = inv_query.join(StudentProfile, Intervention.student_id == StudentProfile.id).where(
                StudentProfile.department_id == department_id
            )
        inv_res = await db.execute(inv_query)
        interventions = inv_res.scalars().all()

        total_inv = len(interventions)
        completed_inv = sum(1 for i in interventions if i.status == InterventionStatus.COMPLETED)
        follow_ups_due = sum(1 for i in interventions if i.status == InterventionStatus.FOLLOW_UP_REQUIRED)

        # Estimated active alert volume
        total_alerts = (risk_dist.get("HIGH", 0) + risk_dist.get("CRITICAL", 0))

        return AdminOverviewAnalytics(
            total_students=total_students,
            active_students=active_students,
            students_monitored=total_students,
            average_current_cgpa=avg_cgpa,
            average_predicted_cgpa=avg_pred_cgpa,
            risk_distribution=risk_dist,
            risk_percentages=risk_pcts,
            students_requiring_attention=attention_count,
            total_departments=total_departments,
            total_faculty=total_faculty,
            total_interventions=total_inv,
            completed_interventions=completed_inv,
            follow_ups_due=follow_ups_due,
            total_alerts=total_alerts,
        )

    @classmethod
    async def get_risk_analytics(
        cls,
        db: AsyncSession,
        department_id: Optional[uuid.UUID] = None,
        semester: Optional[int] = None,
    ) -> AdminRiskAnalytics:
        """
        Institution-level risk distribution, cross-department risk metrics, semester risk, and attendance vs risk.
        """
        student_query = (
            select(StudentProfile)
            .where(StudentProfile.is_archived == False)  # noqa: E712
            .options(
                selectinload(StudentProfile.department),
                selectinload(StudentProfile.academic_records),
            )
        )
        if department_id:
            student_query = student_query.where(StudentProfile.department_id == department_id)
        if semester:
            student_query = student_query.where(StudentProfile.current_semester == semester)

        res = await db.execute(student_query)
        students = res.scalars().all()
        student_ids = [s.id for s in students]
        latest_predictions = await cls._get_latest_predictions_for_students(db, student_ids)

        risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        total_students = len(students)

        # Attendance brackets: "<65%", "65-74%", "75-84%", ">=85%"
        att_brackets: Dict[str, Dict[str, Any]] = {
            "<65%": {"count": 0, "risk": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}},
            "65-74%": {"count": 0, "risk": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}},
            "75-84%": {"count": 0, "risk": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}},
            ">=85%": {"count": 0, "risk": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}},
        }

        # Department risk breakdown
        dept_data: Dict[uuid.UUID, Dict[str, Any]] = {}
        # Semester risk breakdown
        sem_data: Dict[int, Dict[str, Any]] = {}

        for s in students:
            pred = latest_predictions.get(s.id)
            risk = pred.risk_level if pred else "LOW"
            if risk == "MODERATE":
                risk = "MEDIUM"
            if risk not in risk_dist:
                risk_dist[risk] = 0
            risk_dist[risk] += 1

            # Attendance bracket
            records = sorted(s.academic_records, key=lambda r: r.semester, reverse=True) if s.academic_records else []
            latest_rec = records[0] if records else None
            att = float(latest_rec.attendance_percentage) if (latest_rec and latest_rec.attendance_percentage is not None) else None

            if att is not None:
                if att < 65.0:
                    b_key = "<65%"
                elif att < 75.0:
                    b_key = "65-74%"
                elif att < 85.0:
                    b_key = "75-84%"
                else:
                    b_key = ">=85%"
                att_brackets[b_key]["count"] += 1
                att_brackets[b_key]["risk"][risk] += 1

            # Department breakdown
            d_id = s.department_id
            if d_id not in dept_data:
                dept_data[d_id] = {
                    "id": d_id,
                    "name": s.department.name if s.department else "Unknown",
                    "code": s.department.code if s.department else "N/A",
                    "students": 0,
                    "risk": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
                }
            dept_data[d_id]["students"] += 1
            dept_data[d_id]["risk"][risk] += 1

            # Semester breakdown
            sem = s.current_semester
            if sem not in sem_data:
                sem_data[sem] = {
                    "semester": sem,
                    "students": 0,
                    "cgpas": [],
                    "atts": [],
                    "risk": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
                }
            sem_data[sem]["students"] += 1
            sem_data[sem]["risk"][risk] += 1
            if s.cumulative_gpa is not None:
                sem_data[sem]["cgpas"].append(float(s.cumulative_gpa))
            if att is not None:
                sem_data[sem]["atts"].append(att)

        risk_pcts: Dict[str, float] = {}
        for r_key, count in risk_dist.items():
            risk_pcts[r_key] = round((count / total_students * 100.0), 1) if total_students > 0 else 0.0

        high_crit_count = risk_dist.get("HIGH", 0) + risk_dist.get("CRITICAL", 0)
        high_crit_pct = round((high_crit_count / total_students * 100.0), 1) if total_students > 0 else 0.0

        dept_items: List[DepartmentRiskItem] = []
        for d_info in dept_data.values():
            s_cnt = d_info["students"]
            hc = d_info["risk"]["HIGH"] + d_info["risk"]["CRITICAL"]
            pct = round((hc / s_cnt * 100.0), 1) if s_cnt > 0 else 0.0
            dept_items.append(
                DepartmentRiskItem(
                    department_id=d_info["id"],
                    department_name=d_info["name"],
                    department_code=d_info["code"],
                    student_count=s_cnt,
                    risk_distribution=d_info["risk"],
                    high_or_critical_pct=pct,
                )
            )
        dept_items.sort(key=lambda d: d.high_or_critical_pct, reverse=True)

        sem_items: List[SemesterRiskItem] = []
        for sem_k in sorted(sem_data.keys()):
            s_info = sem_data[sem_k]
            avg_c = round(sum(s_info["cgpas"]) / len(s_info["cgpas"]), 2) if s_info["cgpas"] else None
            avg_a = round(sum(s_info["atts"]) / len(s_info["atts"]), 1) if s_info["atts"] else None
            sem_items.append(
                SemesterRiskItem(
                    semester=s_info["semester"],
                    student_count=s_info["students"],
                    risk_distribution=s_info["risk"],
                    average_cgpa=avg_c,
                    average_attendance=avg_a,
                )
            )

        att_risk_buckets = [
            AttendanceVsRiskBucket(
                attendance_bracket=b_name,
                student_count=b_val["count"],
                risk_distribution=b_val["risk"],
            )
            for b_name, b_val in att_brackets.items()
        ]

        return AdminRiskAnalytics(
            risk_distribution=risk_dist,
            risk_percentages=risk_pcts,
            total_high_critical_count=high_crit_count,
            high_critical_percentage=high_crit_pct,
            department_risk_breakdown=dept_items,
            semester_risk_breakdown=sem_items,
            attendance_vs_risk=att_risk_buckets,
        )

    @classmethod
    async def get_performance_analytics(
        cls,
        db: AsyncSession,
        department_id: Optional[uuid.UUID] = None,
        semester: Optional[int] = None,
    ) -> AdminAcademicPerformanceAnalytics:
        """
        Institution-level academic performance distributions, attendance, and backlog health.
        """
        student_query = (
            select(StudentProfile)
            .where(StudentProfile.is_archived == False)  # noqa: E712
            .options(
                selectinload(StudentProfile.department),
                selectinload(StudentProfile.academic_records),
            )
        )
        if department_id:
            student_query = student_query.where(StudentProfile.department_id == department_id)
        if semester:
            student_query = student_query.where(StudentProfile.current_semester == semester)

        res = await db.execute(student_query)
        students = res.scalars().all()
        student_ids = [s.id for s in students]
        latest_predictions = await cls._get_latest_predictions_for_students(db, student_ids)

        cgpa_dist = {
            "< 6.0": 0,
            "6.0 - 6.99": 0,
            "7.0 - 7.99": 0,
            "8.0 - 8.99": 0,
            ">= 9.0": 0,
        }

        cgpas: List[float] = []
        pred_cgpas: List[float] = []
        atts: List[float] = []
        below_75 = 0
        below_65 = 0
        total_backlogs = 0
        with_backlogs = 0

        # Department performance collector
        dept_map: Dict[uuid.UUID, Dict[str, Any]] = {}

        for s in students:
            # CGPA
            if s.cumulative_gpa is not None:
                val = float(s.cumulative_gpa)
                cgpas.append(val)
                if val < 6.0:
                    cgpa_dist["< 6.0"] += 1
                elif val < 7.0:
                    cgpa_dist["6.0 - 6.99"] += 1
                elif val < 8.0:
                    cgpa_dist["7.0 - 7.99"] += 1
                elif val < 9.0:
                    cgpa_dist["8.0 - 8.99"] += 1
                else:
                    cgpa_dist[">= 9.0"] += 1

            pred = latest_predictions.get(s.id)
            if pred and pred.predicted_cgpa is not None:
                pred_cgpas.append(float(pred.predicted_cgpa))
            elif s.cumulative_gpa is not None:
                pred_cgpas.append(float(s.cumulative_gpa))

            # Attendance & backlogs
            records = sorted(s.academic_records, key=lambda r: r.semester, reverse=True) if s.academic_records else []
            latest_rec = records[0] if records else None
            student_att = float(latest_rec.attendance_percentage) if (latest_rec and latest_rec.attendance_percentage is not None) else None
            student_b = latest_rec.backlogs if latest_rec else 0


            if student_att is not None:
                atts.append(student_att)
                if student_att < 65.0:
                    below_65 += 1
                if student_att < 75.0:
                    below_75 += 1

            if student_b > 0:
                with_backlogs += 1
                total_backlogs += student_b

            # Department breakdown
            d_id = s.department_id
            if d_id not in dept_map:
                dept_map[d_id] = {
                    "id": d_id,
                    "name": s.department.name if s.department else "Unknown",
                    "code": s.department.code if s.department else "N/A",
                    "students": 0,
                    "cgpas": [],
                    "pred_cgpas": [],
                    "atts": [],
                    "backlogs": 0,
                    "with_b": 0,
                }
            dept_map[d_id]["students"] += 1
            if s.cumulative_gpa is not None:
                dept_map[d_id]["cgpas"].append(float(s.cumulative_gpa))
            if pred and pred.predicted_cgpa is not None:
                dept_map[d_id]["pred_cgpas"].append(float(pred.predicted_cgpa))
            if student_att is not None:
                dept_map[d_id]["atts"].append(student_att)
            if student_b > 0:
                dept_map[d_id]["backlogs"] += student_b
                dept_map[d_id]["with_b"] += 1

        # Interventions count per department
        inv_stmt = select(StudentProfile.department_id, func.count(Intervention.id)).join(
            Intervention, StudentProfile.id == Intervention.student_id
        ).group_by(StudentProfile.department_id)
        inv_counts_res = await db.execute(inv_stmt)
        inv_by_dept = {row[0]: row[1] for row in inv_counts_res.all()}

        dept_perf_list: List[DepartmentPerformanceItem] = []
        for d_id, d_val in dept_map.items():
            avg_c = round(sum(d_val["cgpas"]) / len(d_val["cgpas"]), 2) if d_val["cgpas"] else None
            avg_p = round(sum(d_val["pred_cgpas"]) / len(d_val["pred_cgpas"]), 2) if d_val["pred_cgpas"] else None
            avg_a = round(sum(d_val["atts"]) / len(d_val["atts"]), 1) if d_val["atts"] else None
            dept_perf_list.append(
                DepartmentPerformanceItem(
                    department_id=d_val["id"],
                    department_name=d_val["name"],
                    department_code=d_val["code"],
                    student_count=d_val["students"],
                    average_current_cgpa=avg_c,
                    average_predicted_cgpa=avg_p,
                    average_attendance=avg_a,
                    total_backlogs=d_val["backlogs"],
                    students_with_backlogs=d_val["with_b"],
                    intervention_count=inv_by_dept.get(d_id, 0),
                )
            )
        dept_perf_list.sort(key=lambda d: d.student_count, reverse=True)

        total_cnt = len(students)
        avg_cgpa = round(sum(cgpas) / len(cgpas), 2) if cgpas else None
        avg_pred_cgpa = round(sum(pred_cgpas) / len(pred_cgpas), 2) if pred_cgpas else None
        avg_att = round(sum(atts) / len(atts), 1) if atts else None
        backlog_pct = round((with_backlogs / total_cnt * 100.0), 1) if total_cnt > 0 else 0.0

        return AdminAcademicPerformanceAnalytics(
            overall_cgpa_distribution=cgpa_dist,
            average_current_cgpa=avg_cgpa,
            average_predicted_cgpa=avg_pred_cgpa,
            average_attendance=avg_att,
            attendance_below_75_count=below_75,
            attendance_below_65_count=below_65,
            total_backlogs=total_backlogs,
            students_with_backlogs_count=with_backlogs,
            students_with_backlogs_pct=backlog_pct,
            department_performances=dept_perf_list,
        )

    @classmethod
    async def get_department_analytics(
        cls, db: AsyncSession
    ) -> AdminDepartmentAnalyticsResponse:
        perf = await cls.get_performance_analytics(db)
        return AdminDepartmentAnalyticsResponse(
            departments=perf.department_performances,
            total_departments=len(perf.department_performances),
        )

    @classmethod
    async def get_semester_analytics(
        cls, db: AsyncSession
    ) -> AdminSemesterAnalyticsResponse:
        risk = await cls.get_risk_analytics(db)
        return AdminSemesterAnalyticsResponse(
            semesters=risk.semester_risk_breakdown,
            total_semesters=len(risk.semester_risk_breakdown),
        )

    @classmethod
    async def get_interventions_analytics(
        cls,
        db: AsyncSession,
        department_id: Optional[uuid.UUID] = None,
    ) -> AdminInterventionsAnalytics:
        """
        Observational analytics on intervention distributions, completion rates, and measured outcomes.
        """
        query = (
            select(Intervention)
            .join(StudentProfile, Intervention.student_id == StudentProfile.id)
            .options(selectinload(Intervention.outcome))
        )
        if department_id:
            query = query.where(StudentProfile.department_id == department_id)

        res = await db.execute(query)
        interventions = res.scalars().all()

        total = len(interventions)
        by_status: Dict[str, int] = {st.value: 0 for st in InterventionStatus}
        by_category: Dict[str, int] = {cat.value: 0 for cat in InterventionCategory}
        by_priority: Dict[str, int] = {pr.value: 0 for pr in InterventionPriority}

        outcome_dist = {
            "IMPROVED": 0,
            "STABLE": 0,
            "DECLINED": 0,
            "INSUFFICIENT_DATA": 0,
        }

        completed_cnt = 0
        follow_ups_due = 0
        measured_cnt = 0

        for inv in interventions:
            st_val = inv.status.value if hasattr(inv.status, "value") else str(inv.status)
            cat_val = inv.category.value if hasattr(inv.category, "value") else str(inv.category)
            pr_val = inv.priority.value if hasattr(inv.priority, "value") else str(inv.priority)

            by_status[st_val] = by_status.get(st_val, 0) + 1
            by_category[cat_val] = by_category.get(cat_val, 0) + 1
            by_priority[pr_val] = by_priority.get(pr_val, 0) + 1

            if inv.status == InterventionStatus.COMPLETED:
                completed_cnt += 1
            if inv.status == InterventionStatus.FOLLOW_UP_REQUIRED:
                follow_ups_due += 1

            if inv.outcome:
                measured_cnt += 1
                ost = inv.outcome.outcome_status.value if hasattr(inv.outcome.outcome_status, "value") else str(inv.outcome.outcome_status)
                outcome_dist[ost] = outcome_dist.get(ost, 0) + 1
            elif inv.status in (InterventionStatus.COMPLETED, InterventionStatus.FOLLOW_UP_REQUIRED):
                outcome_dist["INSUFFICIENT_DATA"] += 1

        comp_rate = round((completed_cnt / total * 100.0), 1) if total > 0 else 0.0
        improved_pct = (
            round((outcome_dist["IMPROVED"] / measured_cnt * 100.0), 1)
            if measured_cnt > 0
            else 0.0
        )

        return AdminInterventionsAnalytics(
            total_interventions=total,
            by_status=by_status,
            by_category=by_category,
            by_priority=by_priority,
            completion_rate=comp_rate,
            follow_ups_due_count=follow_ups_due,
            outcome_distribution=outcome_dist,
            measured_students_count=measured_cnt,
            improved_percentage_of_measured=improved_pct,
        )

    @classmethod
    async def _get_latest_predictions_for_students(
        cls, db: AsyncSession, student_ids: List[uuid.UUID]
    ) -> Dict[uuid.UUID, Prediction]:
        if not student_ids:
            return {}

        stmt = (
            select(Prediction)
            .where(Prediction.student_id.in_(student_ids))
            .order_by(Prediction.created_at.desc())
        )
        res = await db.execute(stmt)
        all_preds = res.scalars().all()

        latest: Dict[uuid.UUID, Prediction] = {}
        for p in all_preds:
            if p.student_id not in latest:
                latest[p.student_id] = p
        return latest
