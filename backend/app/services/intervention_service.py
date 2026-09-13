"""
Core service for Phase 12: Intervention Tracking & Outcome Management.

Provides:
1. Faculty/Admin authorization scoping for student interventions.
2. Snapshot baseline metric capture at intervention creation.
3. Intervention lifecycle transitions (PLANNED -> SCHEDULED -> IN_PROGRESS -> COMPLETED / CANCELLED / FOLLOW_UP_REQUIRED).
4. Evidence linking (Alerts, Recommendations, Reasons).
5. Observational outcome measurement and Before/After comparison intelligence.
6. Dashboard statistics and filtering.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import func, or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.academic_record import SemesterAcademicRecord
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
from backend.app.schemas.intervention import (
    BeforeAfterComparisonResponse,
    IndicatorDelta,
    InterventionCompleteRequest,
    InterventionCreate,
    InterventionDashboardStats,
    InterventionFollowUpRequest,
    InterventionListResponse,
    InterventionOutcomeCreate,
    InterventionOutcomeResponse,
    InterventionResponse,
    InterventionUpdate,
)
from backend.app.services.faculty_service import FacultyService

logger = logging.getLogger("student_predictor.intervention_service")

# Risk ordering for comparison
RISK_ORDER = {"LOW": 1, "MODERATE": 2, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


class InterventionService:
    @staticmethod
    async def get_student_baseline_metrics(
        db: AsyncSession, student: StudentProfile
    ) -> Dict[str, Any]:
        """
        Gathers baseline metrics (risk level, predicted CGPA, attendance, backlogs)
        for a student from their latest academic record and prediction.
        """
        baseline: Dict[str, Any] = {
            "risk_level": "LOW",
            "predicted_cgpa": float(student.cumulative_gpa) if student.cumulative_gpa is not None else None,
            "attendance": None,
            "backlogs": 0,
        }

        # Latest academic record
        records = sorted(student.academic_records, key=lambda r: r.semester, reverse=True) if student.academic_records else []
        if records:
            latest_rec = records[0]
            baseline["attendance"] = float(latest_rec.attendance_percentage) if latest_rec.attendance_percentage is not None else None
            baseline["backlogs"] = latest_rec.backlogs or 0


        # Latest prediction
        pred_stmt = (
            select(Prediction)
            .where(Prediction.student_id == student.id)
            .order_by(Prediction.created_at.desc())
            .limit(1)
        )
        pred_res = await db.execute(pred_stmt)
        latest_pred = pred_res.scalar_one_or_none()
        if latest_pred:
            baseline["risk_level"] = latest_pred.risk_level
            if latest_pred.predicted_cgpa is not None:
                baseline["predicted_cgpa"] = float(latest_pred.predicted_cgpa)

        return baseline

    @classmethod
    async def create_intervention(
        cls,
        db: AsyncSession,
        current_user: User,
        data: InterventionCreate,
    ) -> Intervention:
        """
        Creates an intervention for an authorized student with baseline metric snapshots.
        """
        student = await FacultyService.verify_faculty_student_access(db, current_user, data.student_id)

        # Baseline snapshot
        baseline = await cls.get_student_baseline_metrics(db, student)

        faculty_id = None
        if current_user.role == UserRole.FACULTY and current_user.faculty_profile:
            faculty_id = current_user.faculty_profile.id

        intervention = Intervention(
            student_id=student.id,
            faculty_id=faculty_id,
            category=data.category,
            title=data.title,
            description=data.description,
            reason=data.reason,
            priority=data.priority,
            status=data.status,
            notes=data.notes,
            source=data.source or "FACULTY_MANUAL",
            related_alert_id=data.related_alert_id,
            related_recommendation_id=data.related_recommendation_id,
            scheduled_at=data.scheduled_at,
            follow_up_date=data.follow_up_date,
            baseline_risk_level=baseline.get("risk_level"),
            baseline_predicted_cgpa=baseline.get("predicted_cgpa"),
            baseline_attendance=baseline.get("attendance"),
            baseline_backlogs=baseline.get("backlogs"),
            created_by=current_user.id,
        )

        db.add(intervention)
        await db.commit()
        await db.refresh(intervention)
        return intervention

    @classmethod
    async def get_intervention_by_id(
        cls,
        db: AsyncSession,
        current_user: User,
        intervention_id: uuid.UUID,
    ) -> Intervention:
        """
        Retrieves an intervention and verifies that the current user has access to its student.
        """
        stmt = (
            select(Intervention)
            .where(Intervention.id == intervention_id)
            .options(
                selectinload(Intervention.student).selectinload(StudentProfile.department),
                selectinload(Intervention.student).selectinload(StudentProfile.academic_records),
                selectinload(Intervention.faculty).selectinload(FacultyProfile.user),
                selectinload(Intervention.outcome),
            )
        )
        res = await db.execute(stmt)
        intervention = res.scalar_one_or_none()
        if not intervention:
            raise LookupError(f"Intervention with id '{intervention_id}' was not found.")

        # Authorize access to this student
        await FacultyService.verify_faculty_student_access(db, current_user, intervention.student_id)
        return intervention

    @classmethod
    async def update_intervention(
        cls,
        db: AsyncSession,
        current_user: User,
        intervention_id: uuid.UUID,
        data: InterventionUpdate,
    ) -> Intervention:
        """
        Updates an existing intervention.
        """
        intervention = await cls.get_intervention_by_id(db, current_user, intervention_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, val in update_data.items():
            setattr(intervention, field, val)

        await db.commit()
        await db.refresh(intervention)
        return intervention

    @classmethod
    async def complete_intervention(
        cls,
        db: AsyncSession,
        current_user: User,
        intervention_id: uuid.UUID,
        data: InterventionCompleteRequest,
    ) -> Intervention:
        """
        Marks an intervention as COMPLETED, records completion timestamp and notes,
        and optionally schedules a follow-up.
        """
        intervention = await cls.get_intervention_by_id(db, current_user, intervention_id)

        intervention.status = (
            InterventionStatus.FOLLOW_UP_REQUIRED
            if data.follow_up_date
            else InterventionStatus.COMPLETED
        )
        intervention.completed_at = data.completed_at or datetime.now(timezone.utc)
        if data.completion_notes:
            existing = intervention.notes or ""
            intervention.notes = f"{existing}\n[Completion Note]: {data.completion_notes}".strip()
        if data.follow_up_date:
            intervention.follow_up_date = data.follow_up_date

        await db.commit()
        await db.refresh(intervention)
        return intervention

    @classmethod
    async def record_follow_up(
        cls,
        db: AsyncSession,
        current_user: User,
        intervention_id: uuid.UUID,
        data: InterventionFollowUpRequest,
    ) -> Intervention:
        """
        Records follow-up notes and updates status.
        """
        intervention = await cls.get_intervention_by_id(db, current_user, intervention_id)

        existing_follow_up = intervention.follow_up_notes or ""
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        intervention.follow_up_notes = f"{existing_follow_up}\n[{timestamp_str}]: {data.follow_up_notes}".strip()

        if data.status:
            intervention.status = data.status
        if data.new_follow_up_date:
            intervention.follow_up_date = data.new_follow_up_date

        await db.commit()
        await db.refresh(intervention)
        return intervention

    @classmethod
    async def record_outcome(
        cls,
        db: AsyncSession,
        current_user: User,
        intervention_id: uuid.UUID,
        data: InterventionOutcomeCreate,
    ) -> InterventionOutcome:
        """
        Records or updates an outcome measurement for an intervention.
        If values are not provided in data, current student metrics are dynamically measured.
        """
        intervention = await cls.get_intervention_by_id(db, current_user, intervention_id)
        student = intervention.student

        current_metrics = await cls.get_student_baseline_metrics(db, student)

        curr_risk = data.current_risk or current_metrics.get("risk_level")
        curr_cgpa = (
            data.current_predicted_cgpa
            if data.current_predicted_cgpa is not None
            else current_metrics.get("predicted_cgpa")
        )
        curr_att = (
            data.current_attendance
            if data.current_attendance is not None
            else current_metrics.get("attendance")
        )
        curr_backlogs = (
            data.current_backlogs
            if data.current_backlogs is not None
            else current_metrics.get("backlogs")
        )

        prev_risk = intervention.baseline_risk_level
        prev_cgpa = float(intervention.baseline_predicted_cgpa) if intervention.baseline_predicted_cgpa is not None else None
        prev_att = float(intervention.baseline_attendance) if intervention.baseline_attendance is not None else None
        prev_backlogs = intervention.baseline_backlogs

        # Calculate outcome status objectively if not explicitly forced
        outcome_status = data.outcome_status or cls._compute_outcome_status(
            prev_risk=prev_risk,
            curr_risk=curr_risk,
            prev_cgpa=prev_cgpa,
            curr_cgpa=curr_cgpa,
            prev_att=prev_att,
            curr_att=curr_att,
            prev_backlogs=prev_backlogs,
            curr_backlogs=curr_backlogs,
        )

        # Check if outcome already exists
        outcome = intervention.outcome
        if not outcome:
            outcome = InterventionOutcome(
                intervention_id=intervention.id,
                measured_at=datetime.now(timezone.utc),
                previous_risk=prev_risk,
                current_risk=curr_risk,
                previous_predicted_cgpa=prev_cgpa,
                current_predicted_cgpa=curr_cgpa,
                previous_attendance=prev_att,
                current_attendance=curr_att,
                previous_backlogs=prev_backlogs,
                current_backlogs=curr_backlogs,
                outcome_status=outcome_status,
                notes=data.notes,
                measured_by=current_user.id,
            )
            db.add(outcome)
        else:
            outcome.measured_at = datetime.now(timezone.utc)
            outcome.previous_risk = prev_risk
            outcome.current_risk = curr_risk
            outcome.previous_predicted_cgpa = prev_cgpa
            outcome.current_predicted_cgpa = curr_cgpa
            outcome.previous_attendance = prev_att
            outcome.current_attendance = curr_att
            outcome.previous_backlogs = prev_backlogs
            outcome.current_backlogs = curr_backlogs
            outcome.outcome_status = outcome_status
            if data.notes:
                outcome.notes = data.notes
            outcome.measured_by = current_user.id

        await db.commit()
        await db.refresh(outcome)
        return outcome

    @classmethod
    def _compute_outcome_status(
        cls,
        prev_risk: Optional[str],
        curr_risk: Optional[str],
        prev_cgpa: Optional[float],
        curr_cgpa: Optional[float],
        prev_att: Optional[float],
        curr_att: Optional[float],
        prev_backlogs: Optional[int],
        curr_backlogs: Optional[int],
    ) -> OutcomeStatus:
        """
        Pure observational indicator change evaluation without asserting causation.
        """
        if prev_risk is None and prev_cgpa is None and prev_att is None:
            return OutcomeStatus.INSUFFICIENT_DATA

        improved_signals = 0
        declined_signals = 0

        # Risk level change
        if prev_risk and curr_risk:
            prev_order = RISK_ORDER.get(prev_risk.upper(), 2)
            curr_order = RISK_ORDER.get(curr_risk.upper(), 2)
            if curr_order < prev_order:
                improved_signals += 2
            elif curr_order > prev_order:
                declined_signals += 2

        # Attendance change (>= +3% improvement vs <= -3% decline)
        if prev_att is not None and curr_att is not None:
            att_diff = curr_att - prev_att
            if att_diff >= 3.0:
                improved_signals += 1
            elif att_diff <= -3.0:
                declined_signals += 1

        # CGPA change (>= +0.15 improvement vs <= -0.15 decline)
        if prev_cgpa is not None and curr_cgpa is not None:
            cgpa_diff = curr_cgpa - prev_cgpa
            if cgpa_diff >= 0.15:
                improved_signals += 1
            elif cgpa_diff <= -0.15:
                declined_signals += 1

        # Backlogs change
        if prev_backlogs is not None and curr_backlogs is not None:
            if curr_backlogs < prev_backlogs:
                improved_signals += 1
            elif curr_backlogs > prev_backlogs:
                declined_signals += 1

        if improved_signals > declined_signals:
            return OutcomeStatus.IMPROVED
        elif declined_signals > improved_signals:
            return OutcomeStatus.DECLINED
        elif improved_signals == 0 and declined_signals == 0:
            if prev_risk is not None or prev_cgpa is not None:
                return OutcomeStatus.STABLE
            return OutcomeStatus.INSUFFICIENT_DATA
        else:
            return OutcomeStatus.STABLE

    @classmethod
    def build_comparison(
        cls, intervention: Intervention
    ) -> BeforeAfterComparisonResponse:
        """
        Builds a comprehensive before-after comparison response with observational phrasing.
        """
        student = intervention.student
        outcome = intervention.outcome

        indicators: List[IndicatorDelta] = []
        has_sufficient_data = False

        # Risk indicator
        prev_risk = (
            outcome.previous_risk
            if outcome and outcome.previous_risk
            else intervention.baseline_risk_level
        )
        curr_risk = outcome.current_risk if outcome else None
        if prev_risk or curr_risk:
            has_sufficient_data = True
            risk_status = "INSUFFICIENT_DATA"
            if prev_risk and curr_risk:
                p_ord = RISK_ORDER.get(prev_risk.upper(), 2)
                c_ord = RISK_ORDER.get(curr_risk.upper(), 2)
                if c_ord < p_ord:
                    risk_status = "IMPROVED"
                elif c_ord > p_ord:
                    risk_status = "DECLINED"
                else:
                    risk_status = "STABLE"
            indicators.append(
                IndicatorDelta(
                    indicator="Risk Category",
                    before=prev_risk or "N/A",
                    after=curr_risk or "Pending",
                    delta=f"{prev_risk} → {curr_risk}" if (prev_risk and curr_risk) else None,
                    status=risk_status,
                )
            )

        # CGPA indicator
        prev_cgpa = (
            float(outcome.previous_predicted_cgpa)
            if outcome and outcome.previous_predicted_cgpa is not None
            else (float(intervention.baseline_predicted_cgpa) if intervention.baseline_predicted_cgpa is not None else None)
        )
        curr_cgpa = float(outcome.current_predicted_cgpa) if outcome and outcome.current_predicted_cgpa is not None else None
        if prev_cgpa is not None or curr_cgpa is not None:
            has_sufficient_data = True
            cgpa_status = "INSUFFICIENT_DATA"
            delta_val = None
            if prev_cgpa is not None and curr_cgpa is not None:
                d = round(curr_cgpa - prev_cgpa, 2)
                delta_val = f"{'+' if d > 0 else ''}{d:.2f}"
                if d >= 0.1:
                    cgpa_status = "IMPROVED"
                elif d <= -0.1:
                    cgpa_status = "DECLINED"
                else:
                    cgpa_status = "STABLE"
            indicators.append(
                IndicatorDelta(
                    indicator="Predicted CGPA",
                    before=f"{prev_cgpa:.2f}" if prev_cgpa is not None else "N/A",
                    after=f"{curr_cgpa:.2f}" if curr_cgpa is not None else "Pending",
                    delta=delta_val,
                    status=cgpa_status,
                )
            )

        # Attendance indicator
        prev_att = (
            float(outcome.previous_attendance)
            if outcome and outcome.previous_attendance is not None
            else (float(intervention.baseline_attendance) if intervention.baseline_attendance is not None else None)
        )
        curr_att = float(outcome.current_attendance) if outcome and outcome.current_attendance is not None else None
        if prev_att is not None or curr_att is not None:
            has_sufficient_data = True
            att_status = "INSUFFICIENT_DATA"
            delta_val = None
            if prev_att is not None and curr_att is not None:
                d = round(curr_att - prev_att, 1)
                delta_val = f"{'+' if d > 0 else ''}{d:.1f}%"
                if d >= 2.0:
                    att_status = "IMPROVED"
                elif d <= -2.0:
                    att_status = "DECLINED"
                else:
                    att_status = "STABLE"
            indicators.append(
                IndicatorDelta(
                    indicator="Attendance Rate",
                    before=f"{prev_att:.1f}%" if prev_att is not None else "N/A",
                    after=f"{curr_att:.1f}%" if curr_att is not None else "Pending",
                    delta=delta_val,
                    status=att_status,
                )
            )

        # Backlogs indicator
        prev_b = (
            outcome.previous_backlogs
            if outcome and outcome.previous_backlogs is not None
            else intervention.baseline_backlogs
        )
        curr_b = outcome.current_backlogs if outcome and outcome.current_backlogs is not None else None
        if prev_b is not None or curr_b is not None:
            has_sufficient_data = True
            b_status = "INSUFFICIENT_DATA"
            delta_val = None
            if prev_b is not None and curr_b is not None:
                d = curr_b - prev_b
                delta_val = f"{'+' if d > 0 else ''}{d}"
                if d < 0:
                    b_status = "IMPROVED"
                elif d > 0:
                    b_status = "DECLINED"
                else:
                    b_status = "STABLE"
            indicators.append(
                IndicatorDelta(
                    indicator="Backlogs Count",
                    before=str(prev_b) if prev_b is not None else "N/A",
                    after=str(curr_b) if curr_b is not None else "Pending",
                    delta=delta_val,
                    status=b_status,
                )
            )

        outcome_status = outcome.outcome_status if outcome else OutcomeStatus.INSUFFICIENT_DATA
        measured_at = outcome.measured_at if outcome else None

        if outcome_status == OutcomeStatus.IMPROVED:
            statement = "Academic indicators improved after the intervention was recorded."
        elif outcome_status == OutcomeStatus.DECLINED:
            statement = "Academic indicators declined in the follow-up evaluation period."
        elif outcome_status == OutcomeStatus.STABLE:
            statement = "Academic indicators remained stable following the intervention."
        else:
            statement = "Insufficient historical follow-up data to evaluate indicator trajectory."

        return BeforeAfterComparisonResponse(
            intervention_id=intervention.id,
            student_id=student.id if student else intervention.student_id,
            student_name=student.name if student else "Unknown Student",
            student_number=student.student_number if student else "N/A",
            measured_at=measured_at,
            outcome_status=outcome_status,
            observational_statement=statement,
            indicators=indicators,
            has_sufficient_data=has_sufficient_data,
        )

    @classmethod
    def to_intervention_response(cls, intervention: Intervention) -> InterventionResponse:
        student = intervention.student
        dept_name = student.department.name if (student and student.department) else None
        faculty_user = (
            intervention.faculty.user
            if (intervention.faculty and intervention.faculty.user)
            else None
        )
        faculty_name = faculty_user.full_name if faculty_user else None

        outcome_resp = None
        if intervention.outcome:
            o = intervention.outcome
            outcome_resp = InterventionOutcomeResponse(
                id=o.id,
                intervention_id=o.intervention_id,
                measured_at=o.measured_at,
                previous_risk=o.previous_risk,
                current_risk=o.current_risk,
                previous_predicted_cgpa=float(o.previous_predicted_cgpa) if o.previous_predicted_cgpa is not None else None,
                current_predicted_cgpa=float(o.current_predicted_cgpa) if o.current_predicted_cgpa is not None else None,
                previous_attendance=float(o.previous_attendance) if o.previous_attendance is not None else None,
                current_attendance=float(o.current_attendance) if o.current_attendance is not None else None,
                previous_backlogs=o.previous_backlogs,
                current_backlogs=o.current_backlogs,
                outcome_status=o.outcome_status,
                notes=o.notes,
                measured_by=o.measured_by,
                created_at=o.created_at,
                updated_at=o.updated_at,
            )

        return InterventionResponse(
            id=intervention.id,
            student_id=intervention.student_id,
            student_name=student.name if student else None,
            student_number=student.student_number if student else None,
            department_name=dept_name,
            faculty_id=intervention.faculty_id,
            faculty_name=faculty_name,
            category=intervention.category,
            title=intervention.title,
            description=intervention.description,
            reason=intervention.reason,
            priority=intervention.priority,
            status=intervention.status,
            notes=intervention.notes,
            source=intervention.source,
            related_alert_id=intervention.related_alert_id,
            related_recommendation_id=intervention.related_recommendation_id,
            scheduled_at=intervention.scheduled_at,
            completed_at=intervention.completed_at,
            follow_up_date=intervention.follow_up_date,
            follow_up_notes=intervention.follow_up_notes,
            baseline_risk_level=intervention.baseline_risk_level,
            baseline_predicted_cgpa=float(intervention.baseline_predicted_cgpa) if intervention.baseline_predicted_cgpa is not None else None,
            baseline_attendance=float(intervention.baseline_attendance) if intervention.baseline_attendance is not None else None,
            baseline_backlogs=intervention.baseline_backlogs,
            created_by=intervention.created_by,
            created_at=intervention.created_at,
            updated_at=intervention.updated_at,
            outcome=outcome_resp,
        )

    @classmethod
    async def list_interventions(
        cls,
        db: AsyncSession,
        current_user: User,
        student_id: Optional[uuid.UUID] = None,
        status: Optional[InterventionStatus] = None,
        category: Optional[InterventionCategory] = None,
        priority: Optional[InterventionPriority] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> InterventionListResponse:
        """
        Lists interventions with pagination, filtering, and authorization scoping.
        """
        scope_dept_id, _ = FacultyService.resolve_faculty_scope(current_user)

        query = (
            select(Intervention)
            .join(StudentProfile, Intervention.student_id == StudentProfile.id)
            .options(
                selectinload(Intervention.student).selectinload(StudentProfile.department),
                selectinload(Intervention.faculty).selectinload(FacultyProfile.user),
                selectinload(Intervention.outcome),
            )
        )

        conditions = []
        if scope_dept_id:
            conditions.append(StudentProfile.department_id == scope_dept_id)

        if student_id:
            conditions.append(Intervention.student_id == student_id)

        if status:
            conditions.append(Intervention.status == status)

        if category:
            conditions.append(Intervention.category == category)

        if priority:
            conditions.append(Intervention.priority == priority)

        if search:
            search_pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    Intervention.title.ilike(search_pattern),
                    Intervention.description.ilike(search_pattern),
                    StudentProfile.name.ilike(search_pattern),
                    StudentProfile.student_number.ilike(search_pattern),
                )
            )

        if conditions:
            query = query.where(and_(*conditions))

        # Total count query
        count_query = (
            select(func.count(Intervention.id))
            .join(StudentProfile, Intervention.student_id == StudentProfile.id)
        )
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_res = await db.execute(count_query)
        total = total_res.scalar() or 0

        # Pagination & sorting
        offset = (max(page, 1) - 1) * page_size
        query = query.order_by(Intervention.created_at.desc()).offset(offset).limit(page_size)

        res = await db.execute(query)
        interventions = res.scalars().all()

        items = [cls.to_intervention_response(item) for item in interventions]

        return InterventionListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + len(items)) < total,
        )

    @classmethod
    async def get_dashboard_stats(
        cls, db: AsyncSession, current_user: User
    ) -> InterventionDashboardStats:
        """
        Computes summary statistics for faculty/admin intervention dashboard based on real stored records.
        """
        scope_dept_id, _ = FacultyService.resolve_faculty_scope(current_user)

        base_query = select(Intervention).join(StudentProfile, Intervention.student_id == StudentProfile.id)
        if scope_dept_id:
            base_query = base_query.where(StudentProfile.department_id == scope_dept_id)

        # Interventions and outcomes
        stmt = base_query.options(selectinload(Intervention.outcome))
        res = await db.execute(stmt)
        interventions = res.scalars().all()

        total = len(interventions)
        active = 0
        follow_ups = 0
        completed = 0
        improved = 0
        stable = 0
        declined = 0
        insufficient = 0

        now = datetime.now(timezone.utc)
        for inv in interventions:
            if inv.status in (InterventionStatus.PLANNED, InterventionStatus.SCHEDULED, InterventionStatus.IN_PROGRESS):
                active += 1
            if inv.status == InterventionStatus.FOLLOW_UP_REQUIRED:
                follow_ups += 1
            if inv.status == InterventionStatus.COMPLETED:
                completed += 1

            if inv.outcome:
                st = inv.outcome.outcome_status
                if st == OutcomeStatus.IMPROVED:
                    improved += 1
                elif st == OutcomeStatus.STABLE:
                    stable += 1
                elif st == OutcomeStatus.DECLINED:
                    declined += 1
                else:
                    insufficient += 1
            elif inv.status in (InterventionStatus.COMPLETED, InterventionStatus.FOLLOW_UP_REQUIRED):
                insufficient += 1

        return InterventionDashboardStats(
            total_interventions=total,
            active_interventions=active,
            follow_ups_due=follow_ups,
            completed_interventions=completed,
            improved_count=improved,
            stable_count=stable,
            declined_count=declined,
            insufficient_data_count=insufficient,
        )
