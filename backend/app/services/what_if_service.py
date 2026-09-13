"""
What-If Academic Simulator Service for Phase 7.

Orchestrates:
1. Baseline academic state resolution (from DB or explicit inputs).
2. Hypothetical override application.
3. Phase 2 Preprocessing reuse.
4. Phase 3 CGPA Prediction Service reuse.
5. Phase 4 Academic Risk Service reuse.
6. Delta calculation and structured comparison output.

Strictly side-effect free: does NOT persist hypothetical values.
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.what_if import (
    WhatIfSimulationRequest,
    WhatIfSimulationResponse,
    WhatIfHypotheticalInputs,
    AcademicState,
    SimulationOutcome,
    FactorDelta,
    SimulationDelta,
)
from backend.app.schemas.prediction import CGPAPredictionRequest
from backend.app.schemas.risk_prediction import RiskPredictionRequest
from backend.app.services.prediction_service import prediction_service
from backend.app.services.risk_service import academic_risk_service
from backend.app.models.student import StudentProfile
from backend.app.models.academic_record import SemesterAcademicRecord
from sqlalchemy import select

logger = logging.getLogger("student_predictor.what_if_service")


class WhatIfSimulationService:
    """Service for running hypothetical academic simulations."""

    def __init__(self):
        pass

    def _apply_overrides(
        self,
        baseline: CGPAPredictionRequest,
        overrides: WhatIfHypotheticalInputs,
    ) -> CGPAPredictionRequest:
        """Apply hypothetical overrides to baseline request, returning new request."""
        baseline_dict = baseline.model_dump()
        overrides_dict = overrides.model_dump(exclude_unset=True, exclude_none=True)

        for key, value in overrides_dict.items():
            if value is not None:
                baseline_dict[key] = value

        return CGPAPredictionRequest(**baseline_dict)

    def _create_academic_state(self, request: CGPAPredictionRequest) -> AcademicState:
        """Create AcademicState snapshot from request."""
        return AcademicState(
            attendance_percentage=request.attendance_percentage,
            mid_1=request.mid_1,
            mid_2=request.mid_2,
            internal_marks=request.internal_marks,
            backlogs=request.backlogs,
            previous_cgpa=request.previous_cgpa,
            semester=request.semester,
            department_code=request.department_code,
        )

    def _create_factor_deltas(
        self,
        baseline: CGPAPredictionRequest,
        simulated: CGPAPredictionRequest,
    ) -> List[FactorDelta]:
        """Calculate per-factor deltas between baseline and simulated requests."""
        factor_map = {
            "attendance_percentage": ("attendance_percentage", "Attendance", "%"),
            "mid_1": ("mid_1", "Mid-Term 1", "marks"),
            "mid_2": ("mid_2", "Mid-Term 2", "marks"),
            "internal_marks": ("internal_marks", "Internal Marks", "marks"),
            "backlogs": ("backlogs", "Backlogs", "count"),
            "previous_cgpa": ("previous_cgpa", "Previous CGPA", "/10"),
        }

        deltas = []
        for field_key, (attr_key, display_name, unit) in factor_map.items():
            baseline_val = getattr(baseline, field_key)
            simulated_val = getattr(simulated, field_key)
            if baseline_val != simulated_val:
                deltas.append(
                    FactorDelta(
                        factor=field_key,
                        display_name=display_name,
                        baseline_value=float(baseline_val),
                        simulated_value=float(simulated_val),
                        delta=float(simulated_val - baseline_val),
                        unit=unit,
                    )
                )
        return deltas

    def _determine_trend(self, delta: float) -> str:
        """Determine trend direction from delta."""
        if delta > 0.001:
            return "IMPROVED"
        elif delta < -0.001:
            return "WORSENED"
        return "UNCHANGED"

    def _determine_overall_impact(
        self,
        cgpa_trend: str,
        risk_trend: str,
    ) -> str:
        """Determine overall impact from CGPA and risk trends."""
        if cgpa_trend == "IMPROVED" and risk_trend == "IMPROVED":
            return "IMPROVED"
        if cgpa_trend == "WORSENED" or risk_trend == "WORSENED":
            return "WORSENED"
        return "UNCHANGED"

    async def _resolve_baseline(
        self,
        request: WhatIfSimulationRequest,
        db: AsyncSession,
        current_user: Optional[Any],
    ) -> CGPAPredictionRequest:
        """Resolve baseline CGPA request from DB or explicit inputs."""
        if request.baseline_inputs:
            return request.baseline_inputs

        if not request.student_number:
            raise ValueError("Either baseline_inputs or student_number must be provided")

        stmt = select(StudentProfile).where(StudentProfile.student_number == request.student_number)
        result = await db.execute(stmt)
        student = result.scalar_one_or_none()

        if not student:
            raise ValueError(f"Student with number {request.student_number} not found")

        stmt = (
            select(SemesterAcademicRecord)
            .where(SemesterAcademicRecord.student_id == student.id)
            .order_by(SemesterAcademicRecord.semester.desc())
        )
        result = await db.execute(stmt)
        latest_record = result.scalars().first()

        if not latest_record:
            raise ValueError(f"No academic records found for student {request.student_number}")

        semester = request.semester or latest_record.semester

        return CGPAPredictionRequest(
            student_number=student.student_number,
            gender=student.gender,
            age=student.age,
            department_code=student.department_code,
            semester=semester,
            attendance_percentage=float(latest_record.attendance_percentage or 75.0),
            previous_cgpa=float(latest_record.previous_cgpa or student.cumulative_gpa or 7.0),
            mid_1=float(latest_record.mid_1 or 70.0),
            mid_2=float(latest_record.mid_2 or 70.0),
            internal_marks=float(latest_record.internal_marks or 70.0),
            backlogs=int(latest_record.backlogs or 0),
        )

    async def _run_cgpa_prediction(
        self,
        request: CGPAPredictionRequest,
        db: AsyncSession,
        current_user: Optional[Any],
    ):
        """Run CGPA prediction using existing service."""
        return await prediction_service.predict_cgpa(request, db, current_user)

    async def _run_risk_prediction(
        self,
        request: CGPAPredictionRequest,
        db: AsyncSession,
        current_user: Optional[Any],
    ):
        """Run risk prediction using existing service."""
        risk_request = RiskPredictionRequest(
            student_number=request.student_number,
            gender=request.gender,
            age=request.age,
            department_code=request.department_code,
            semester=request.semester,
            attendance_percentage=request.attendance_percentage,
            previous_cgpa=request.previous_cgpa,
            mid_1=request.mid_1,
            mid_2=request.mid_2,
            internal_marks=request.internal_marks,
            backlogs=request.backlogs,
        )
        return await academic_risk_service.predict_risk(risk_request, db, current_user)

    async def simulate(
        self,
        request: WhatIfSimulationRequest,
        db: AsyncSession,
        current_user: Optional[Any] = None,
    ) -> WhatIfSimulationResponse:
        """
        Execute complete What-If simulation.
        
        Flow:
        1. Resolve baseline academic state
        2. Apply hypothetical overrides to create simulated state
        3. Run CGPA + Risk predictions for both states
        4. Calculate deltas and build response
        """
        logger.info(f"What-If simulation requested for student: {request.student_number}")

        # 1. Resolve baseline
        baseline_request = await self._resolve_baseline(request, db, current_user)

        # 2. Apply overrides
        simulated_request = self._apply_overrides(baseline_request, request.hypothetical_inputs)

        # 3. Run predictions for baseline
        baseline_cgpa = await self._run_cgpa_prediction(baseline_request, db, current_user)
        baseline_risk = await self._run_risk_prediction(baseline_request, db, current_user)

        # 4. Run predictions for simulated
        simulated_cgpa = await self._run_cgpa_prediction(simulated_request, db, current_user)
        simulated_risk = await self._run_risk_prediction(simulated_request, db, current_user)

        # 5. Build outcomes
        baseline_outcome = SimulationOutcome(
            predicted_cgpa=baseline_cgpa.predicted_cgpa,
            grade=baseline_risk.grade,
            performance_category=baseline_risk.performance_category,
            risk_level=baseline_risk.risk_level,
            risk_score=baseline_risk.risk_score,
            risk_probabilities=baseline_risk.risk_probabilities,
            academic_state=self._create_academic_state(baseline_request),
        )

        simulated_outcome = SimulationOutcome(
            predicted_cgpa=simulated_cgpa.predicted_cgpa,
            grade=simulated_risk.grade,
            performance_category=simulated_risk.performance_category,
            risk_level=simulated_risk.risk_level,
            risk_score=simulated_risk.risk_score,
            risk_probabilities=simulated_risk.risk_probabilities,
            academic_state=self._create_academic_state(simulated_request),
        )

        # 6. Calculate deltas
        factor_deltas = self._create_factor_deltas(baseline_request, simulated_request)
        cgpa_delta = simulated_cgpa.predicted_cgpa - baseline_cgpa.predicted_cgpa
        risk_score_delta = simulated_risk.risk_score - baseline_risk.risk_score

        delta = SimulationDelta(
            cgpa_delta=round(cgpa_delta, 2),
            cgpa_trend=self._determine_trend(cgpa_delta),
            risk_score_delta=round(risk_score_delta, 1),
            risk_transition=f"{baseline_risk.risk_level} \u2192 {simulated_risk.risk_level}",
            risk_trend=self._determine_trend(-risk_score_delta),  # Lower risk score = better
            performance_category_transition=f"{baseline_risk.performance_category} \u2192 {simulated_risk.performance_category}",
            modified_factors=factor_deltas,
            overall_impact=self._determine_overall_impact(
                self._determine_trend(cgpa_delta),
                self._determine_trend(-risk_score_delta),
            ),
        )

        return WhatIfSimulationResponse(
            baseline=baseline_outcome,
            simulation=simulated_outcome,
            delta=delta,
            model_name=baseline_cgpa.model_name,
            model_version=baseline_cgpa.model_version,
            risk_model_name=baseline_risk.model_name,
            risk_model_version=baseline_risk.model_version,
            status="success",
        )


what_if_simulation_service = WhatIfSimulationService()