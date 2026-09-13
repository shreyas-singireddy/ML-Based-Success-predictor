"""
Personalized Recommendation Service for Phase 8.

Orchestrates:
1. Student context & academic state resolution (from DB or explicit payload).
2. Phase 3 CGPA Prediction Engine execution.
3. Phase 4 Academic Risk Engine & 5-factor breakdown execution.
4. Phase 5 SHAP Explainability Engine integration.
5. Phase 7 What-If Simulator execution for candidate improvement levers.
6. Deterministic Rule evaluation, evidence attachment, and ranking.
7. Deduplication and temporal action plan compilation.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItemSchema,
    RecommendationEvidenceSchema,
    ActionPlanSchema,
)
from backend.app.schemas.prediction import CGPAPredictionRequest, CGPAPredictionResponse
from backend.app.schemas.risk_prediction import RiskPredictionRequest, RiskPredictionResponse
from backend.app.schemas.what_if import WhatIfSimulationRequest, WhatIfHypotheticalInputs
from backend.app.services.prediction_service import prediction_service
from backend.app.services.risk_service import academic_risk_service
from backend.app.services.what_if_service import what_if_simulation_service
from ml.explainability.explanation_service import explanation_service
from ml.recommendations.recommendation_config import (
    RecommendationPolicyConfig,
    PRIORITY_SEVERITY_ORDER,
    TimeHorizon,
)
from ml.recommendations.rules import (
    DEFAULT_RULES,
    CandidateRecommendation,
)
from backend.app.models.student import StudentProfile
from backend.app.models.academic_record import SemesterAcademicRecord

logger = logging.getLogger("student_predictor.recommendation_service")


class RecommendationService:
    """Service for generating evidence-based personalized academic recommendations."""

    def __init__(self):
        self.rules = list(DEFAULT_RULES)

    async def _resolve_baseline_data(
        self,
        request: RecommendationRequest,
        db: Optional[AsyncSession],
        current_user: Optional[Any],
    ) -> Dict[str, Any]:
        """
        Resolves raw academic indicators either from database records or explicit request payload.
        """
        if request.student_number and db is not None:
            stmt = select(StudentProfile).where(StudentProfile.student_number == request.student_number).options(selectinload(StudentProfile.department))
            result = await db.execute(stmt)
            student = result.scalar_one_or_none()

            if student:
                # Authorization check
                if current_user and current_user.role == "STUDENT" and student.user_id != current_user.id:
                    raise PermissionError("Access denied: You can only view recommendations for your own profile.")

                records_stmt = (
                    select(SemesterAcademicRecord)
                    .where(SemesterAcademicRecord.student_id == student.id)
                    .order_by(SemesterAcademicRecord.semester.desc())
                )
                rec_res = await db.execute(records_stmt)
                latest_rec = rec_res.scalars().first()

                if latest_rec:
                    return {
                        "student_number": student.student_number,
                        "student_name": student.name,
                        "gender": student.gender.value if hasattr(student.gender, "value") else str(student.gender),
                        "age": student.age,
                        "department_code": student.department.code if student.department else None,
                        "semester": request.semester or latest_rec.semester,
                        "attendance_percentage": float(request.attendance_percentage if request.attendance_percentage is not None else latest_rec.attendance_percentage or 75.0),
                        "previous_cgpa": float(request.previous_cgpa if request.previous_cgpa is not None else (latest_rec.previous_cgpa or student.cumulative_gpa or 7.0)),
                        "mid_1": float(request.mid_1 if request.mid_1 is not None else (latest_rec.mid_1 or 70.0)),
                        "mid_2": float(request.mid_2 if request.mid_2 is not None else (latest_rec.mid_2 or 70.0)),
                        "internal_marks": float(request.internal_marks if request.internal_marks is not None else (latest_rec.internal_marks or 70.0)),
                        "backlogs": int(request.backlogs if request.backlogs is not None else (latest_rec.backlogs or 0)),
                    }

        # Explicit fallback
        missing = []
        for field in ["attendance_percentage", "previous_cgpa", "mid_1", "mid_2", "internal_marks", "backlogs"]:
            if getattr(request, field) is None:
                missing.append(field)

        if missing:
            raise ValueError(f"Insufficient academic data to generate recommendations. Missing fields: {', '.join(missing)}")

        return {
            "student_number": request.student_number,
            "student_name": None,
            "gender": request.gender or "MALE",
            "age": request.age or 20,
            "department_code": request.department_code or "CS",
            "semester": request.semester or 4,
            "attendance_percentage": float(request.attendance_percentage),
            "previous_cgpa": float(request.previous_cgpa),
            "mid_1": float(request.mid_1),
            "mid_2": float(request.mid_2),
            "internal_marks": float(request.internal_marks),
            "backlogs": int(request.backlogs),
        }

    async def _evaluate_simulation_levers(
        self,
        base_request: CGPAPredictionRequest,
        raw_data: Dict[str, Any],
        db: Optional[AsyncSession],
        current_user: Optional[Any],
    ) -> Dict[str, Any]:
        """
        Executes real What-If simulations for actionable levers without modifying any models.
        """
        simulation_data: Dict[str, Any] = {}
        att = float(raw_data.get("attendance_percentage", 80.0))
        bl = int(raw_data.get("backlogs", 0))
        m1 = float(raw_data.get("mid_1", 70.0))
        m2 = float(raw_data.get("mid_2", 70.0))
        mid_avg = (m1 + m2) / 2.0
        internal = float(raw_data.get("internal_marks", 70.0))

        # 1. Attendance Lever Simulation
        if att < RecommendationPolicyConfig.ATTENDANCE_SAFE_TARGET:
            target_att = RecommendationPolicyConfig.ATTENDANCE_SAFE_TARGET
            sim_req = WhatIfSimulationRequest(
                baseline_inputs=base_request,
                hypothetical_inputs=WhatIfHypotheticalInputs(attendance_percentage=target_att),
            )
            try:
                sim_res = await what_if_simulation_service.simulate(sim_req, db, current_user)
                simulation_data["attendance"] = {
                    "simulated_value": target_att,
                    "cgpa_delta": sim_res.delta.cgpa_delta,
                    "risk_score_delta": sim_res.delta.risk_score_delta,
                    "risk_transition": sim_res.delta.risk_transition,
                }
            except Exception as e:
                logger.warning(f"What-If attendance simulation skipped: {e}")

        # 2. Backlogs Lever Simulation
        if bl > 0:
            sim_req = WhatIfSimulationRequest(
                baseline_inputs=base_request,
                hypothetical_inputs=WhatIfHypotheticalInputs(backlogs=0),
            )
            try:
                sim_res = await what_if_simulation_service.simulate(sim_req, db, current_user)
                simulation_data["backlogs"] = {
                    "simulated_value": 0,
                    "cgpa_delta": sim_res.delta.cgpa_delta,
                    "risk_score_delta": sim_res.delta.risk_score_delta,
                    "risk_transition": sim_res.delta.risk_transition,
                }
            except Exception as e:
                logger.warning(f"What-If backlogs simulation skipped: {e}")

        # 3. Mid-Terms Lever Simulation
        if mid_avg < RecommendationPolicyConfig.MIDTERM_TARGET:
            boost = min(100.0, mid_avg + 15.0)
            sim_req = WhatIfSimulationRequest(
                baseline_inputs=base_request,
                hypothetical_inputs=WhatIfHypotheticalInputs(mid_1=boost, mid_2=boost),
            )
            try:
                sim_res = await what_if_simulation_service.simulate(sim_req, db, current_user)
                simulation_data["mid_terms"] = {
                    "simulated_value": round(boost, 1),
                    "cgpa_delta": sim_res.delta.cgpa_delta,
                    "risk_score_delta": sim_res.delta.risk_score_delta,
                    "risk_transition": sim_res.delta.risk_transition,
                }
            except Exception as e:
                logger.warning(f"What-If mid-terms simulation skipped: {e}")

        # 4. Internal Marks Lever Simulation
        if internal < RecommendationPolicyConfig.INTERNAL_TARGET:
            target_int = min(100.0, internal + 15.0)
            sim_req = WhatIfSimulationRequest(
                baseline_inputs=base_request,
                hypothetical_inputs=WhatIfHypotheticalInputs(internal_marks=target_int),
            )
            try:
                sim_res = await what_if_simulation_service.simulate(sim_req, db, current_user)
                simulation_data["internal_marks"] = {
                    "simulated_value": round(target_int, 1),
                    "cgpa_delta": sim_res.delta.cgpa_delta,
                    "risk_score_delta": sim_res.delta.risk_score_delta,
                    "risk_transition": sim_res.delta.risk_transition,
                }
            except Exception as e:
                logger.warning(f"What-If internal marks simulation skipped: {e}")

        # 5. Aggregate Comprehensive Improvement Simulation (for action plan summary)
        comprehensive_overrides = {}
        if att < RecommendationPolicyConfig.ATTENDANCE_SAFE_TARGET:
            comprehensive_overrides["attendance_percentage"] = RecommendationPolicyConfig.ATTENDANCE_SAFE_TARGET
        if bl > 0:
            comprehensive_overrides["backlogs"] = 0
        if mid_avg < RecommendationPolicyConfig.MIDTERM_TARGET:
            comprehensive_overrides["mid_1"] = min(100.0, m1 + 10.0)
            comprehensive_overrides["mid_2"] = min(100.0, m2 + 10.0)
        if internal < RecommendationPolicyConfig.INTERNAL_TARGET:
            comprehensive_overrides["internal_marks"] = min(100.0, internal + 10.0)

        if comprehensive_overrides:
            sim_req = WhatIfSimulationRequest(
                baseline_inputs=base_request,
                hypothetical_inputs=WhatIfHypotheticalInputs(**comprehensive_overrides),
            )
            try:
                comp_res = await what_if_simulation_service.simulate(sim_req, db, current_user)
                simulation_data["_aggregate_plan"] = {
                    "baseline_predicted_cgpa": comp_res.baseline.predicted_cgpa,
                    "simulated_predicted_cgpa": comp_res.simulation.predicted_cgpa,
                    "cgpa_delta": comp_res.delta.cgpa_delta,
                    "baseline_risk_level": comp_res.baseline.risk_level,
                    "simulated_risk_level": comp_res.simulation.risk_level,
                    "risk_score_delta": comp_res.delta.risk_score_delta,
                    "risk_transition": comp_res.delta.risk_transition,
                    "overall_impact": comp_res.delta.overall_impact,
                    "overrides_evaluated": comprehensive_overrides,
                }
            except Exception as e:
                logger.warning(f"What-If aggregate simulation skipped: {e}")

        return simulation_data

    async def generate_recommendations(
        self,
        request: RecommendationRequest,
        db: Optional[AsyncSession] = None,
        current_user: Optional[Any] = None,
        max_recommendations: int = RecommendationPolicyConfig.MAX_RECOMMENDATIONS_DEFAULT,
    ) -> RecommendationResponse:
        """
        Generates personalized, evidence-first academic recommendations.
        """
        prediction_service.load_artifacts()
        academic_risk_service.load_artifacts()

        # 1. Resolve raw baseline data
        raw_data = await self._resolve_baseline_data(request, db, current_user)

        # 2. Build standard CGPA & Risk requests
        cgpa_req = CGPAPredictionRequest(
            student_number=raw_data.get("student_number"),
            gender=raw_data.get("gender"),
            age=raw_data.get("age"),
            department_code=raw_data.get("department_code"),
            semester=raw_data.get("semester"),
            attendance_percentage=raw_data["attendance_percentage"],
            previous_cgpa=raw_data["previous_cgpa"],
            mid_1=raw_data["mid_1"],
            mid_2=raw_data["mid_2"],
            internal_marks=raw_data["internal_marks"],
            backlogs=raw_data["backlogs"],
        )
        risk_req = RiskPredictionRequest(
            student_number=raw_data.get("student_number"),
            gender=raw_data.get("gender"),
            age=raw_data.get("age"),
            department_code=raw_data.get("department_code"),
            semester=raw_data.get("semester"),
            attendance_percentage=raw_data["attendance_percentage"],
            previous_cgpa=raw_data["previous_cgpa"],
            mid_1=raw_data["mid_1"],
            mid_2=raw_data["mid_2"],
            internal_marks=raw_data["internal_marks"],
            backlogs=raw_data["backlogs"],
        )

        # 3. Execute Phase 3 CGPA Prediction & Phase 4 Risk Engine
        cgpa_resp: CGPAPredictionResponse = await prediction_service.predict_cgpa(cgpa_req, db, current_user)
        risk_resp: RiskPredictionResponse = await academic_risk_service.predict_risk(risk_req, db, current_user)

        # 4. Compute Phase 5 SHAP Explanations
        shap_explanation = None
        try:
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
            shap_explanation = explanation_service.explain_cgpa_prediction(
                transformed_X=transformed_matrix,
                feature_values_raw=feature_values_raw,
            )
        except Exception as e:
            logger.warning(f"SHAP explanation generation skipped during recommendation: {e}")

        # 5. Evaluate Phase 7 What-If simulation levers
        simulation_data = await self._evaluate_simulation_levers(cgpa_req, raw_data, db, current_user)

        # 6. Evaluate all registered recommendation rules
        candidates: List[CandidateRecommendation] = []
        for rule in self.rules:
            try:
                candidate = rule.evaluate(
                    raw_data=raw_data,
                    cgpa_prediction=cgpa_resp,
                    risk_prediction=risk_resp,
                    explanation=shap_explanation,
                    simulation_data=simulation_data,
                )
                if candidate:
                    candidates.append(candidate)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.__class__.__name__}: {e}", exc_info=True)

        # 7. Deduplicate candidates by category / factor
        seen_categories = set()
        deduped_candidates: List[CandidateRecommendation] = []
        for cand in candidates:
            if cand.category not in seen_categories:
                seen_categories.add(cand.category)
                deduped_candidates.append(cand)

        # 8. Sort/Rank candidates by priority severity then ranking_score
        deduped_candidates.sort(
            key=lambda c: (
                PRIORITY_SEVERITY_ORDER.get(c.priority, 0),
                c.ranking_score,
            ),
            reverse=True,
        )

        # 9. Cap at configured maximum
        final_candidates = deduped_candidates[:max_recommendations]

        # 10. Map to Pydantic items
        rec_items: List[RecommendationItemSchema] = []
        for c in final_candidates:
            evidence_items = [
                RecommendationEvidenceSchema(
                    factor=ev.factor,
                    display_name=ev.display_name,
                    current_value=ev.current_value,
                    target_or_threshold=ev.target_or_threshold,
                    unit=ev.unit,
                    source=ev.source.value,
                    simulated_value=ev.simulated_value,
                    shap_contribution=ev.shap_contribution,
                    impact_detail=ev.impact_detail,
                )
                for ev in c.evidence
            ]
            rec_items.append(
                RecommendationItemSchema(
                    id=c.id,
                    title=c.title,
                    priority=c.priority.value,
                    category=c.category.value,
                    evidence=evidence_items,
                    action=c.action,
                    expected_impact=c.expected_impact.value,
                    source=c.source.value,
                    time_horizon=c.time_horizon.value,
                    risk_factor=c.risk_factor,
                    technical_details=c.technical_details,
                )
            )

        # 11. Organize Temporal Action Plan
        this_week = [r for r in rec_items if r.time_horizon == TimeHorizon.THIS_WEEK.value]
        next_30_days = [r for r in rec_items if r.time_horizon == TimeHorizon.NEXT_30_DAYS.value]
        longer_term = [r for r in rec_items if r.time_horizon == TimeHorizon.LONGER_TERM.value]

        action_plan = ActionPlanSchema(
            this_week=this_week,
            next_30_days=next_30_days,
            longer_term=longer_term,
            simulation_summary=simulation_data.get("_aggregate_plan"),
        )

        # 12. Build evidence summary metadata
        evidence_summary = {
            "factors_analyzed": len(raw_data),
            "rules_evaluated": len(self.rules),
            "candidates_generated": len(candidates),
            "recommendations_returned": len(rec_items),
            "simulation_levers_tested": len([k for k in simulation_data.keys() if not k.startswith("_")]),
            "shap_evidence_attached": shap_explanation is not None,
        }

        model_version_info = {
            "cgpa_model": f"{cgpa_resp.model_name} ({cgpa_resp.model_version})",
            "risk_model": f"{risk_resp.model_name} ({risk_resp.model_version})",
            "policy_version": RecommendationPolicyConfig.POLICY_VERSION,
        }

        return RecommendationResponse(
            student_number=raw_data.get("student_number"),
            student_name=raw_data.get("student_name"),
            predicted_cgpa=cgpa_resp.predicted_cgpa,
            grade=risk_resp.grade,
            performance_category=risk_resp.performance_category,
            risk_level=risk_resp.risk_level,
            risk_score=risk_resp.risk_score,
            recommendations=rec_items,
            action_plan=action_plan,
            evidence_summary=evidence_summary,
            model_version_info=model_version_info,
            policy_version=RecommendationPolicyConfig.POLICY_VERSION,
            generated_at=datetime.now(timezone.utc).isoformat(),
            status="success",
        )


recommendation_service = RecommendationService()
