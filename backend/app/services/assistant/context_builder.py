"""
Strict RBAC-grounded context assembly for the GenAI Academic Assistant.

The context builder is the ONLY funnel through which verified academic
intelligence reaches the LLM. It resolves the authenticated student profile,
runs the authorised Phase 3-8 engines, and formats a compact context payload.

Data flows in one direction only (DB -> engines -> context -> LLM). The LLM
is never given raw access to other students' records, API credentials, or
system internals.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.student import StudentProfile
from backend.app.models.academic_record import SemesterAcademicRecord
from backend.app.schemas.assistant import AssistantIntent, EvidenceSourceRef
from backend.app.schemas.prediction import CGPAPredictionRequest
from backend.app.schemas.risk_prediction import RiskPredictionRequest
from backend.app.schemas.recommendation import RecommendationRequest
from backend.app.schemas.what_if import WhatIfSimulationRequest, WhatIfHypotheticalInputs
from backend.app.services.prediction_service import prediction_service
from backend.app.services.risk_service import academic_risk_service
from backend.app.services.what_if_service import what_if_simulation_service
from backend.app.services.recommendation_service import recommendation_service
from ml.explainability.explanation_service import explanation_service

logger = logging.getLogger("student_predictor.assistant.context_builder")


class ContextUnavailableError(Exception):
    """Raised when the verified context cannot be assembled."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass
class BuildContextResult:
    """Verified, authorized academic intelligence for the assistant pipeline."""

    student: Dict[str, Any]
    latest_record: Dict[str, Any]
    academic_history: List[Dict[str, Any]]
    prediction: Optional[Dict[str, Any]]
    risk: Optional[Dict[str, Any]]
    shap: Optional[Dict[str, Any]]
    recommendations: Optional[Dict[str, Any]]
    simulation: Optional[Dict[str, Any]]
    sources_used: List[str] = field(default_factory=list)
    evidence_references: List[EvidenceSourceRef] = field(default_factory=list)
    verified_numbers: set = field(default_factory=set)

    @property
    def has_prediction(self) -> bool:
        return self.prediction is not None

    @property
    def has_risk(self) -> bool:
        return self.risk is not None


# Numeric suffixes/labels for verified numbers - used only for introspection.
_PHASE_LABELS = {
    3: ("Phase 3", "CGPA Prediction Engine", "Predicted CGPA and feature summary from the champion regression model.", {"predicted_cgpa", "feature_summary"}),
    4: ("Phase 4", "Academic Risk Engine", "Risk level, normalized risk score, and transparent 5-factor breakdown.", {"risk_level", "risk_score", "risk_factors"}),
    5: ("Phase 5", "SHAP Explainability Engine", "Local factor attributions explaining why the prediction is what it is.", {"top_factors"}),
    7: ("Phase 7", "What-If Simulator", "Hypothetical scenario outcomes computed by the production models.", {"delta", "simulation"}),
    8: ("Phase 8", "Recommendation Engine", "Prioritized evidence-backed action plan and targets.", {"recommendations", "action_plan"}),
    2: ("Phase 2", "Feature Engineering", "Verified historical semester indicators from the student record.", {"academic_history", "latest_record"}),
}


@dataclass(frozen=True)
class ContextPolicy:
    """Which verified slices a given intent needs assembled into context."""

    history: bool = False
    prediction: bool = False
    risk: bool = False
    shap: bool = False
    recommendations: bool = False
    simulation: bool = False


_FULL_POLICY = ContextPolicy(
    history=True,
    prediction=True,
    risk=True,
    shap=True,
    recommendations=True,
)

# Intent -> minimal-but-sufficient engine selection (#7 / #36).
# A CGPA question never triggers SHAP, recommendations, or What-If; a general
# question triggers no model engines at all.
_INTENT_POLICIES: Dict[Optional[AssistantIntent], ContextPolicy] = {
    None: _FULL_POLICY,
    AssistantIntent.PERFORMANCE: ContextPolicy(history=True, prediction=True),
    AssistantIntent.PREDICTION: ContextPolicy(history=True, prediction=True),
    AssistantIntent.CGPA: ContextPolicy(history=True, prediction=True),
    AssistantIntent.RISK: ContextPolicy(prediction=True, risk=True),
    AssistantIntent.EXPLAINABILITY: ContextPolicy(prediction=True, risk=True, shap=True),
    AssistantIntent.RECOMMENDATION: ContextPolicy(prediction=True, risk=True, recommendations=True),
    AssistantIntent.WHAT_IF: ContextPolicy(prediction=True, risk=True, simulation=True),
    AssistantIntent.ATTENDANCE: ContextPolicy(history=True, prediction=True, risk=True),
    AssistantIntent.BACKLOG: ContextPolicy(history=True, prediction=True, risk=True, recommendations=True),
    AssistantIntent.TREND: ContextPolicy(history=True, prediction=True),
    AssistantIntent.GENERAL_ACADEMIC_GUIDANCE: ContextPolicy(),
    AssistantIntent.UNKNOWN: ContextPolicy(),
}


def policy_for_intent(intent: Optional[AssistantIntent], include_simulation: bool = False) -> ContextPolicy:
    """Resolve the assembly policy for an intent (defaults to the full context)."""
    policy = _INTENT_POLICIES.get(intent, _FULL_POLICY)
    if include_simulation and not policy.simulation:
        policy = ContextPolicy(
            history=policy.history,
            prediction=policy.prediction,
            risk=policy.risk,
            shap=policy.shap,
            recommendations=policy.recommendations,
            simulation=True,
        )
    return policy


class ContextBuilder:
    """Assembles minimal-but-sufficient verified context under strict RBAC."""

    def __init__(self) -> None:
        self._phase_meta: Dict[object, List[str]] = {}

    # -- RBAC resolution -------------------------------------------------------

    async def _resolve_student(
        self,
        current_user: Any,
        db: AsyncSession,
    ) -> StudentProfile:
        # Always query the authoritative profile (with department) from the DB:
        # reinforces RBAC and guarantees department metadata is loaded.
        stmt = (
            select(StudentProfile)
            .where(StudentProfile.user_id == current_user.id)
            .options(selectinload(StudentProfile.department))
        )
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        if profile is None:
            raise ContextUnavailableError("Your user account has no linked student profile.")
        return profile

    @staticmethod
    def _department_code(student: StudentProfile) -> Optional[str]:
        dept = getattr(student, "department", None)
        if dept is not None:
            return getattr(dept, "code", None)
        return None

    async def _resolve_latest_record(
        self,
        student: StudentProfile,
        db: AsyncSession,
    ) -> Optional[SemesterAcademicRecord]:
        stmt = (
            select(SemesterAcademicRecord)
            .where(SemesterAcademicRecord.student_id == student.id)
            .order_by(SemesterAcademicRecord.semester.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def _resolve_history(
        self,
        student: StudentProfile,
        db: AsyncSession,
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(SemesterAcademicRecord)
            .where(SemesterAcademicRecord.student_id == student.id)
            .order_by(SemesterAcademicRecord.semester.asc())
        )
        result = await db.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "semester": r.semester,
                "attendance_percentage": float(r.attendance_percentage) if r.attendance_percentage is not None else None,
                "semester_cgpa": float(r.semester_cgpa) if r.semester_cgpa is not None else None,
                "backlogs": int(r.backlogs or 0),
            }
            for r in records
        ]

    # -- Engine integration -----------------------------------------------------

    def _build_requests(
        self,
        student: StudentProfile,
        latest: SemesterAcademicRecord,
    ) -> tuple[CGPAPredictionRequest, RiskPredictionRequest]:
        department_code = self._department_code(student)
        cgpa_req = CGPAPredictionRequest(
            student_number=student.student_number,
            gender=student.gender,
            age=student.age,
            department_code=department_code,
            semester=latest.semester,
            attendance_percentage=float(latest.attendance_percentage or 75.0),
            previous_cgpa=float(latest.previous_cgpa or student.cumulative_gpa or 7.0),
            mid_1=float(latest.mid_1 or 70.0),
            mid_2=float(latest.mid_2 or 70.0),
            internal_marks=float(latest.internal_marks or 70.0),
            backlogs=int(latest.backlogs or 0),
        )
        risk_req = RiskPredictionRequest(
            student_number=student.student_number,
            gender=student.gender,
            age=student.age,
            department_code=department_code,
            semester=latest.semester,
            attendance_percentage=cgpa_req.attendance_percentage,
            previous_cgpa=cgpa_req.previous_cgpa,
            mid_1=cgpa_req.mid_1,
            mid_2=cgpa_req.mid_2,
            internal_marks=cgpa_req.internal_marks,
            backlogs=cgpa_req.backlogs,
        )
        return cgpa_req, risk_req

    async def _run_prediction_and_risk(
        self,
        current_user: Any,
        db: AsyncSession,
        cgpa_req: CGPAPredictionRequest,
        risk_req: RiskPredictionRequest,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        prediction_service.load_artifacts()
        academic_risk_service.load_artifacts()

        cgpa_resp = await prediction_service.predict_cgpa(cgpa_req, db, current_user)
        risk_resp = await academic_risk_service.predict_risk(risk_req, db, current_user)
        return self._serialize_prediction(cgpa_resp), self._serialize_risk(risk_resp)

    async def _run_prediction(
        self,
        current_user: Any,
        db: AsyncSession,
        cgpa_req: CGPAPredictionRequest,
    ) -> Dict[str, Any]:
        prediction_service.load_artifacts()
        cgpa_resp = await prediction_service.predict_cgpa(cgpa_req, db, current_user)
        return self._serialize_prediction(cgpa_resp)

    async def _run_risk(
        self,
        current_user: Any,
        db: AsyncSession,
        risk_req: RiskPredictionRequest,
    ) -> Dict[str, Any]:
        academic_risk_service.load_artifacts()
        risk_resp = await academic_risk_service.predict_risk(risk_req, db, current_user)
        return self._serialize_risk(risk_resp)

    @staticmethod
    def _serialize_prediction(cgpa_resp: Any) -> Dict[str, Any]:
        return {
            "predicted_cgpa": cgpa_resp.predicted_cgpa,
            "prediction_context": cgpa_resp.prediction_context,
            "model_name": cgpa_resp.model_name,
            "model_version": cgpa_resp.model_version,
            "feature_summary": {
                "academic_average": round(cgpa_resp.feature_summary.academic_average, 2),
                "attendance_risk_score": round(cgpa_resp.feature_summary.attendance_risk_score, 2),
                "attendance_risk_category": cgpa_resp.feature_summary.attendance_risk_category,
                "internal_average": round(cgpa_resp.feature_summary.internal_average, 2),
                "mid_term_average": round(cgpa_resp.feature_summary.mid_term_average, 2),
                "previous_cgpa_trend": round(cgpa_resp.feature_summary.previous_cgpa_trend, 2),
                "backlog_severity_score": round(cgpa_resp.feature_summary.backlog_severity_score, 2),
                "backlog_severity_category": cgpa_resp.feature_summary.backlog_severity_category,
                "academic_stability": round(cgpa_resp.feature_summary.academic_stability, 2),
            },
        }

    @staticmethod
    def _serialize_risk(risk_resp: Any) -> Dict[str, Any]:
        return {
            "risk_level": risk_resp.risk_level,
            "risk_score": risk_resp.risk_score,
            "grade": risk_resp.grade,
            "performance_category": risk_resp.performance_category,
            "risk_probabilities": risk_resp.risk_probabilities,
            "risk_factors": [
                {
                    "factor": f.factor,
                    "level": f.level,
                    "value": f.value,
                    "detail": f.detail,
                }
                for f in risk_resp.risk_factors
            ],
            "model_name": risk_resp.model_name,
            "model_version": risk_resp.model_version,
        }

    async def _run_shap(
        self,
        cgpa_req: CGPAPredictionRequest,
        raw_data: Dict[str, Any],
        db: AsyncSession,
        current_user: Any,
    ) -> Optional[Dict[str, Any]]:
        """Reuse the Phase 5 explanation service over the authorized context."""
        try:
            import numpy as np

            prediction_service.load_artifacts()
            raw_df, _ = await prediction_service.prepare_input_dataframe(cgpa_req, db, current_user)
            featured_df = prediction_service._feature_engineer.transform(raw_df)
            current_features = featured_df.iloc[[-1]].copy()
            transformed_matrix = prediction_service._preprocessor.transform(current_features)
            if hasattr(transformed_matrix, "values"):
                transformed_matrix = transformed_matrix.values
            transformed_matrix = np.array(transformed_matrix, dtype=float)

            feature_values_raw = {
                "attendance_percentage": raw_data["attendance_percentage"],
                "previous_cgpa": raw_data["previous_cgpa"],
                "mid_1": raw_data["mid_1"],
                "mid_2": raw_data["mid_2"],
                "internal_marks": raw_data["internal_marks"],
                "backlogs": float(raw_data["backlogs"]),
                "age": float(raw_data.get("age", 20)),
                "semester": float(raw_data.get("semester", 4)),
            }
            explanation = explanation_service.explain_cgpa_prediction(
                transformed_X=transformed_matrix,
                feature_values_raw=feature_values_raw,
            )
            return {
                "base_value": explanation.base_value,
                "shap_sum": explanation.shap_sum,
                "positive_factors": [
                    {
                        "display_name": f.display_name,
                        "shap_value": f.shap_value,
                        "original_value": f.original_value,
                        "unit": f.unit,
                        "student_explanation": f.student_explanation,
                    }
                    for f in (explanation.positive_factors or [])[:3]
                ],
                "negative_factors": [
                    {
                        "display_name": f.display_name,
                        "shap_value": f.shap_value,
                        "original_value": f.original_value,
                        "unit": f.unit,
                        "student_explanation": f.student_explanation,
                    }
                    for f in (explanation.negative_factors or [])[:3]
                ],
            }
        except Exception as e:  # noqa: BLE001 - SHAP is best-effort
            logger.warning(f"SHAP explanation unavailable for assistant context: {e}")
            return None

    async def _run_recommendations(
        self,
        student: StudentProfile,
        db: AsyncSession,
        current_user: Any,
    ) -> Optional[Dict[str, Any]]:
        try:
            resp = await recommendation_service.generate_recommendations(
                request=RecommendationRequest(student_number=student.student_number),
                db=db,
                current_user=current_user,
            )
            return {
                "policy_version": resp.policy_version,
                "top_recommendations": [
                    {
                        "title": r.title,
                        "priority": r.priority,
                        "category": r.category,
                        "action": r.action,
                        "expected_impact": r.expected_impact,
                        "time_horizon": r.time_horizon,
                        "evidence": [
                            {
                                "display_name": ev.display_name,
                                "current_value": ev.current_value,
                                "target_or_threshold": ev.target_or_threshold,
                                "unit": ev.unit,
                                "source": ev.source,
                                "simulated_value": ev.simulated_value,
                                "shap_contribution": ev.shap_contribution,
                                "impact_detail": ev.impact_detail,
                            }
                            for ev in r.evidence
                        ],
                    }
                    for r in resp.recommendations[:3]
                ],
            }
        except Exception as e:  # noqa: BLE001 - recommendations are best-effort
            logger.warning(f"Recommendations unavailable for assistant context: {e}")
            return None

    async def _run_simulation(
        self,
        student: StudentProfile,
        overrides: Dict[str, object],
        db: AsyncSession,
        current_user: Any,
    ) -> Optional[Dict[str, Any]]:
        try:
            resp = await what_if_simulation_service.simulate(
                request=WhatIfSimulationRequest(
                    student_number=student.student_number,
                    hypothetical_inputs=WhatIfHypotheticalInputs(**overrides),
                ),
                db=db,
                current_user=current_user,
            )
            return {
                "baseline_predicted_cgpa": resp.baseline.predicted_cgpa,
                "baseline_risk_level": resp.baseline.risk_level,
                "baseline_risk_score": resp.baseline.risk_score,
                "simulated_predicted_cgpa": resp.simulation.predicted_cgpa,
                "simulated_risk_level": resp.simulation.risk_level,
                "simulated_risk_score": resp.simulation.risk_score,
                "cgpa_delta": resp.delta.cgpa_delta,
                "cgpa_trend": resp.delta.cgpa_trend,
                "risk_score_delta": resp.delta.risk_score_delta,
                "risk_transition": resp.delta.risk_transition,
                "overall_impact": resp.delta.overall_impact,
                "modified_factors": [
                    {
                        "display_name": f.display_name,
                        "baseline_value": f.baseline_value,
                        "simulated_value": f.simulated_value,
                        "unit": f.unit,
                    }
                    for f in resp.delta.modified_factors
                ],
            }
        except Exception as e:  # noqa: BLE001 - simulation is best-effort
            logger.warning(f"What-If simulation unavailable for assistant context: {e}")
            return None

    # -- Public API --------------------------------------------------------------

    async def build(
        self,
        current_user: Any,
        db: AsyncSession,
        intent: Optional[AssistantIntent] = None,
        what_if_overrides: Optional[Dict[str, object]] = None,
        include_simulation: bool = False,
    ) -> BuildContextResult:
        """
        Assemble the verified context for a chat turn.

        The ``intent`` parameter drives per-intent context selection (#7/36):
        only the engines actually needed for the detected intent are invoked,
        reducing latency, cost, and unnecessary private-context exposure.

        RBAC is enforced on every step: the student's own profile and records
        are the only authorized data sources. Ad-hoc student numbers are not
        accepted - identity comes from the authenticated user session.
        """
        policy = policy_for_intent(intent, include_simulation=include_simulation)
        student = await self._resolve_student(current_user, db)
        latest = await self._resolve_latest_record(student, db)

        student_meta = {
            "student_number": student.student_number,
            "name": student.name,
            "department_code": self._department_code(student),
            "current_semester": student.current_semester,
            "cumulative_gpa": float(student.cumulative_gpa) if student.cumulative_gpa is not None else None,
        }

        if latest is None:
            result = BuildContextResult(
                student=student_meta,
                latest_record={},
                academic_history=[],
                prediction=None,
                risk=None,
                shap=None,
                recommendations=None,
                simulation=None,
            )
            result.sources_used = ["Phase 2"]
            result.evidence_references = [self._ref(2)]
            return result

        raw_data = {
            "student_number": student.student_number,
            "gender": student.gender,
            "age": student.age,
            "department_code": self._department_code(student),
            "semester": latest.semester,
            "attendance_percentage": float(latest.attendance_percentage or 75.0),
            "previous_cgpa": float(latest.previous_cgpa or student.cumulative_gpa or 7.0),
            "mid_1": float(latest.mid_1 or 70.0),
            "mid_2": float(latest.mid_2 or 70.0),
            "internal_marks": float(latest.internal_marks or 70.0),
            "backlogs": int(latest.backlogs or 0),
        }

        latest_meta = {
            "semester": latest.semester,
            "academic_year": latest.academic_year,
            "attendance_percentage": raw_data["attendance_percentage"],
            "previous_cgpa": raw_data["previous_cgpa"],
            "mid_1": raw_data["mid_1"],
            "mid_2": raw_data["mid_2"],
            "internal_marks": raw_data["internal_marks"],
            "backlogs": raw_data["backlogs"],
            "semester_cgpa": float(latest.semester_cgpa) if latest.semester_cgpa is not None else None,
        }

        cgpa_req, risk_req = self._build_requests(student, latest)

        # ---- Intent-scoped engine calls ---------------------------------------
        history = await self._resolve_history(student, db) if policy.history else []

        prediction: Optional[Dict[str, Any]] = None
        risk: Optional[Dict[str, Any]] = None
        if policy.prediction or policy.risk:
            try:
                if policy.prediction and policy.risk:
                    prediction, risk = await self._run_prediction_and_risk(current_user, db, cgpa_req, risk_req)
                elif policy.prediction:
                    prediction = await self._run_prediction(current_user, db, cgpa_req)
                elif policy.risk:
                    risk = await self._run_risk(current_user, db, risk_req)
            except Exception as e:  # noqa: BLE001 - engines may be unavailable
                logger.warning(f"Requested engine(s) unavailable for assistant context: {e}")
                raise ContextUnavailableError(
                    "The prediction and risk engines are currently unavailable. "
                    "Please verify that trained model artifacts are present."
                ) from e

        shap = await self._run_shap(cgpa_req, raw_data, db, current_user) if policy.shap else None
        recommendations = await self._run_recommendations(student, db, current_user) if policy.recommendations else None
        run_simulation = policy.simulation or include_simulation
        simulation: Optional[Dict[str, Any]] = None
        if run_simulation and what_if_overrides:
            simulation = await self._run_simulation(student, what_if_overrides, db, current_user)

        # ---- Verified number collection (grounding guard) ----------------------
        verified: set = {
            raw_data["attendance_percentage"],
            raw_data["previous_cgpa"],
            raw_data["mid_1"],
            raw_data["mid_2"],
            raw_data["internal_marks"],
            float(raw_data["backlogs"]),
        }
        if prediction is not None:
            verified.add(prediction["predicted_cgpa"])
        if risk is not None:
            for f in risk["risk_factors"]:
                try:
                    verified.add(round(float(f["value"]), 3))
                except (TypeError, ValueError):
                    continue
            verified.add(risk["risk_score"])
            for prob in risk["risk_probabilities"].values():
                verified.add(prob)

        if shap is not None:
            for key in ("positive_factors", "negative_factors"):
                for f in shap[key]:
                    verified.add(round(float(f["shap_value"]), 3))
                    if f.get("original_value") is not None:
                        verified.add(round(float(f["original_value"]), 3))
            verified.add(shap["base_value"])
            verified.add(shap["shap_sum"])

        if recommendations is not None:
            for rec in recommendations["top_recommendations"]:
                for ev in rec["evidence"]:
                    for key in ("current_value", "target_or_threshold", "simulated_value", "shap_contribution"):
                        val = ev.get(key)
                        if val is not None:
                            try:
                                verified.add(round(float(val), 3))
                            except (TypeError, ValueError):
                                continue

        if simulation is not None:
            for key in (
                "baseline_predicted_cgpa",
                "simulated_predicted_cgpa",
                "cgpa_delta",
                "baseline_risk_score",
                "simulated_risk_score",
                "risk_score_delta",
            ):
                verified.add(round(float(simulation[key]), 3))

        # ---- Source telemetry ----------------------------------------------------
        sources_used = ["Phase 2"]
        refs = [self._ref(2)]

        if prediction is not None:
            sources_used.append("Phase 3")
            refs.append(self._ref(3))
        if risk is not None:
            sources_used.append("Phase 4")
            refs.append(self._ref(4))
        if shap is not None:
            sources_used.append("Phase 5")
            refs.append(self._ref(5))
        if recommendations is not None:
            sources_used.append("Phase 8")
            refs.append(self._ref(8))
        if simulation is not None:
            sources_used.append("Phase 7")
            refs.append(self._ref(7))

        return BuildContextResult(
            student=student_meta,
            latest_record=latest_meta,
            academic_history=history,
            prediction=prediction,
            risk=risk,
            shap=shap,
            recommendations=recommendations,
            simulation=simulation,
            sources_used=sources_used,
            evidence_references=refs,
            verified_numbers=verified,
        )

    @staticmethod
    def _ref(phase: int) -> EvidenceSourceRef:
        title, desc = _PHASE_LABELS[phase][1], _PHASE_LABELS[phase][2]
        return EvidenceSourceRef(phase=phase, title=title, description=desc)


context_builder = ContextBuilder()


def format_context(result: BuildContextResult) -> str:
    """Render a compact, LLM-safe context summary from the verified data."""
    lines: List[str] = []

    s = result.student
    lines.append(f"STUDENT: {s['name']} ({s['student_number']}), {s['current_semester']}th semester, {s['department_code']} dept.")

    rec = result.latest_record
    if rec:
        lines.append(
            "CURRENT VERIFIED SEMESTER INDICATORS (from official records): "
            f"attendance={rec['attendance_percentage']:.1f}%, previous_cgpa={rec['previous_cgpa']:.2f}, "
            f"mid1={rec['mid_1']:.1f}, mid2={rec['mid_2']:.1f}, internal_marks={rec['internal_marks']:.1f}, "
            f"backlogs={rec['backlogs']}."
        )

    if result.academic_history:
        trend = ", ".join(
            f"S{h['semester']}: cgpa={h['semester_cgpa'] if h['semester_cgpa'] is not None else 'n/a'}"
            for h in result.academic_history
        )
        lines.append(f"HISTORICAL SEMESTER CGPAS: {trend}.")

    if result.prediction:
        p = result.prediction
        lines.append(
            f"PREDICTED CGPA (Phase 3, {p['model_name']} v{p['model_version']}): {p['predicted_cgpa']:.2f}. "
            f"Context: {p['prediction_context']}. "
            f"Academic average={p['feature_summary']['academic_average']:.2f}, "
            f"mid-term average={p['feature_summary']['mid_term_average']:.2f}, "
            f"previous trend={p['feature_summary']['previous_cgpa_trend']:.2f}, "
            f"stability={p['feature_summary']['academic_stability']:.2f}."
        )

    if result.risk:
        r = result.risk
        lines.append(
            f"ACADEMIC RISK (Phase 4, {r['model_name']} v{r['model_version']}): level={r['risk_level']}, "
            f"score={r['risk_score']:.1f}/100, predicted grade={r['grade']}, performance={r['performance_category']}."
        )
        if r.get("risk_factors"):
            factor_lines = "; ".join(
                f"{f['factor']} ({f['level']}): value={f['value']} - {f['detail']}" for f in r["risk_factors"]
            )
            lines.append(f"RISK FACTOR BREAKDOWN: {factor_lines}.")

    if result.shap:
        sh = result.shap
        pos = sh.get("positive_factors") or []
        neg = sh.get("negative_factors") or []
        if pos or neg:
            parts: List[str] = []
            if pos:
                parts.append(
                    "positive: "
                    + "; ".join(f"{f['display_name']} (SHAP +{f['shap_value']:.3f})" for f in pos)
                )
            if neg:
                parts.append(
                    "negative: "
                    + "; ".join(f"{f['display_name']} (SHAP {f['shap_value']:.3f})" for f in neg)
                )
            lines.append("SHAP ATTRIBUTIONS (Phase 5): " + " | ".join(parts) + ".")

    if result.recommendations:
        top = result.recommendations["top_recommendations"]
        desc = "; ".join(
            f"'{r['title']}' ({r['priority']}, {r['category']}, impact {r['expected_impact']})" for r in top
        )
        lines.append(f"TOP RECOMMENDATIONS (Phase 8): {desc}.")

    if result.simulation:
        sim = result.simulation
        lines.append(
            f"WHAT-IF SIMULATION (Phase 7): baseline CGPA {sim['baseline_predicted_cgpa']:.2f} / risk {sim['baseline_risk_level']} "
            f"({sim['baseline_risk_score']:.1f}) -> simulated CGPA {sim['simulated_predicted_cgpa']:.2f} / risk {sim['simulated_risk_level']} "
            f"({sim['simulated_risk_score']:.1f}). CGPA delta {sim['cgpa_delta']:+.2f} ({sim['cgpa_trend']}), "
            f"risk delta {sim['risk_score_delta']:+.1f}, overall impact {sim['overall_impact']}."
        )

    return "\n".join(lines)