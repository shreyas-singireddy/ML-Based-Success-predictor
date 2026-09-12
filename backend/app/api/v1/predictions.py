"""
FastAPI Router for AI CGPA and Academic Risk Predictions.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user_optional
from backend.app.models.user import User
from backend.app.schemas.prediction import CGPAPredictionRequest, CGPAPredictionResponse
from backend.app.schemas.risk_prediction import RiskPredictionRequest, RiskPredictionResponse
from backend.app.schemas.explanation import (
    CGPAExplainedResponse,
    RiskExplainedResponse,
    ExplanationSchema,
    FeatureContributionSchema,
    GlobalImportanceResponse,
)
from backend.app.services.prediction_service import prediction_service
from backend.app.services.risk_service import academic_risk_service
from ml.explainability.explanation_service import explanation_service
from ml.explainability.feature_catalog import GLOBAL_FAIRNESS_NOTE

logger = logging.getLogger("student_predictor.api.predictions")

router = APIRouter(prefix="/predictions", tags=["Predictions"])


# ---------------------------------------------------------------------------
# Phase 3: CGPA Prediction
# ---------------------------------------------------------------------------

@router.post(
    "/cgpa",
    response_model=CGPAPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Semester CGPA",
    description="Predicts future/current semester CGPA using pre-exam academic indicators and the champion regression model.",
)
async def predict_student_cgpa(
    request: CGPAPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> CGPAPredictionResponse:
    try:
        response = await prediction_service.predict_cgpa(request, db, current_user)
        return response
    except PermissionError as pe:
        logger.warning(f"Unauthorized prediction access: {pe}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        )
    except FileNotFoundError as fnf:
        logger.error(f"Prediction artifact missing: {fnf}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Prediction service is currently unavailable. Trained model artifacts are missing.",
        )
    except Exception as e:
        logger.error(f"Inference execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate CGPA prediction. Please verify input data.",
        )


# ---------------------------------------------------------------------------
# Phase 5: CGPA Prediction + Explanation
# ---------------------------------------------------------------------------

@router.post(
    "/cgpa/explain",
    response_model=CGPAExplainedResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict CGPA with SHAP Explanation",
    description=(
        "Predicts semester CGPA and provides a SHAP-based local explanation: "
        "top contributing features, positive/negative factors, and model-level global importance. "
        "All explanations describe model behavior — not causality."
    ),
)
async def predict_cgpa_with_explanation(
    request: CGPAPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> CGPAExplainedResponse:
    try:
        # Step 1: Run standard CGPA prediction
        prediction_service.load_artifacts()
        cgpa_response = await prediction_service.predict_cgpa(request, db, current_user)

        # Step 2: Rebuild the transformed feature matrix for SHAP
        # (identical pipeline to predict_cgpa, but we need the numpy array)
        raw_df, _ = await prediction_service.prepare_input_dataframe(request, db, current_user)
        featured_df = prediction_service._feature_engineer.transform(raw_df)
        current_features = featured_df.iloc[[-1]].copy()
        transformed_matrix = prediction_service._preprocessor.transform(current_features)

        if hasattr(transformed_matrix, "values"):
            import numpy as np
            transformed_matrix = transformed_matrix.values
        else:
            import numpy as np
        transformed_matrix = np.array(transformed_matrix, dtype=float)

        # Step 3: Build raw feature values dict for display in explanation
        feature_values_raw = {
            "attendance_percentage": request.attendance_percentage,
            "previous_cgpa": request.previous_cgpa,
            "mid_1": request.mid_1,
            "mid_2": request.mid_2,
            "internal_marks": request.internal_marks,
            "backlogs": float(request.backlogs),
            "age": float(request.age or 20),
            "semester": float(request.semester or 4),
            "academic_average": float(current_features.get("academic_average", [0.0]).iloc[0])
                if "academic_average" in current_features.columns else 0.0,
            "attendance_risk_score": float(current_features.get("attendance_risk_score", [0.0]).iloc[0])
                if "attendance_risk_score" in current_features.columns else 0.0,
            "mid_term_average": (request.mid_1 + request.mid_2) / 2.0,
            "backlog_severity_score": float(current_features.get("backlog_severity_score", [0.0]).iloc[0])
                if "backlog_severity_score" in current_features.columns else 0.0,
        }

        # Step 4: Compute SHAP explanation
        ml_explanation = explanation_service.explain_cgpa_prediction(
            transformed_X=transformed_matrix,
            feature_values_raw=feature_values_raw,
        )

        # Step 5: Convert ML-layer ExplanationOutput → API ExplanationSchema
        explanation_schema = _convert_explanation_to_schema(ml_explanation)

        return CGPAExplainedResponse(
            **cgpa_response.model_dump(),
            explanation=explanation_schema,
        )

    except PermissionError as pe:
        logger.warning(f"Unauthorized CGPA explain access: {pe}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except FileNotFoundError as fnf:
        logger.error(f"Artifact missing for CGPA explanation: {fnf}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Explanation service is unavailable. Trained model artifacts are missing.",
        )
    except Exception as e:
        logger.error(f"CGPA explanation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate CGPA explanation. Please verify input data.",
        )


# ---------------------------------------------------------------------------
# Phase 4: Academic Risk Prediction
# ---------------------------------------------------------------------------

@router.post(
    "/risk",
    response_model=RiskPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Academic Risk & Severity",
    description="Classifies student academic risk into LOW, MEDIUM, HIGH, or CRITICAL, computes continuous risk score (0-100), and provides a transparent 5-factor breakdown.",
)
async def predict_student_academic_risk(
    request: RiskPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RiskPredictionResponse:
    try:
        response = await academic_risk_service.predict_risk(request, db, current_user)
        return response
    except PermissionError as pe:
        logger.warning(f"Unauthorized risk prediction access: {pe}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        )
    except FileNotFoundError as fnf:
        logger.error(f"Risk prediction artifact missing: {fnf}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Risk Prediction service is currently unavailable. Trained classification model artifacts are missing.",
        )
    except Exception as e:
        logger.error(f"Risk inference execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate academic risk. Please verify input data.",
        )


# ---------------------------------------------------------------------------
# Phase 5: Risk Prediction + Explanation
# ---------------------------------------------------------------------------

@router.post(
    "/risk/explain",
    response_model=RiskExplainedResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Academic Risk with SHAP Explanation",
    description=(
        "Classifies academic risk and provides a SHAP-based local explanation: "
        "top contributing features, positive/negative factors relative to predicted risk class, "
        "and model-level global importance. All explanations describe model behavior — not causality."
    ),
)
async def predict_risk_with_explanation(
    request: RiskPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RiskExplainedResponse:
    try:
        # Step 1: Run standard Risk prediction
        academic_risk_service.load_artifacts()
        prediction_service.load_artifacts()
        risk_response = await academic_risk_service.predict_risk(request, db, current_user)

        # Step 2: Rebuild the transformed feature matrix for SHAP
        from backend.app.schemas.prediction import CGPAPredictionRequest
        import numpy as np
        cgpa_request = CGPAPredictionRequest(
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
        raw_df, _ = await prediction_service.prepare_input_dataframe(cgpa_request, db, current_user)
        featured_df = prediction_service._feature_engineer.transform(raw_df)
        current_features = featured_df.iloc[[-1]].copy()
        transformed_matrix = academic_risk_service._preprocessor.transform(current_features)

        if hasattr(transformed_matrix, "values"):
            transformed_matrix = transformed_matrix.values
        transformed_matrix = np.array(transformed_matrix, dtype=float)

        # Step 3: Build raw feature values dict
        feature_values_raw = {
            "attendance_percentage": request.attendance_percentage,
            "previous_cgpa": request.previous_cgpa,
            "mid_1": request.mid_1,
            "mid_2": request.mid_2,
            "internal_marks": request.internal_marks,
            "backlogs": float(request.backlogs),
            "age": float(request.age or 20),
            "semester": float(request.semester or 4),
            "academic_average": float(current_features["academic_average"].iloc[0])
                if "academic_average" in current_features.columns else 0.0,
            "attendance_risk_score": float(current_features["attendance_risk_score"].iloc[0])
                if "attendance_risk_score" in current_features.columns else 0.0,
            "mid_term_average": (request.mid_1 + request.mid_2) / 2.0,
            "backlog_severity_score": float(current_features["backlog_severity_score"].iloc[0])
                if "backlog_severity_score" in current_features.columns else 0.0,
        }

        # Step 4: Compute SHAP explanation for predicted risk class
        ml_explanation = explanation_service.explain_risk_prediction(
            transformed_X=transformed_matrix,
            feature_values_raw=feature_values_raw,
            predicted_risk_level=risk_response.risk_level,
        )

        # Step 5: Convert to API schema
        explanation_schema = _convert_explanation_to_schema(ml_explanation)

        return RiskExplainedResponse(
            **risk_response.model_dump(),
            explanation=explanation_schema,
        )

    except PermissionError as pe:
        logger.warning(f"Unauthorized risk explain access: {pe}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except FileNotFoundError as fnf:
        logger.error(f"Artifact missing for risk explanation: {fnf}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Explanation service is unavailable. Trained model artifacts are missing.",
        )
    except Exception as e:
        logger.error(f"Risk explanation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate risk explanation. Please verify input data.",
        )


# ---------------------------------------------------------------------------
# Phase 5: Global Feature Importance Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/cgpa/importance",
    response_model=GlobalImportanceResponse,
    status_code=status.HTTP_200_OK,
    summary="CGPA Model Global Feature Importance",
    description=(
        "Returns the precomputed global feature importance for the Phase 3 CGPA champion model. "
        "Computed as mean(|SHAP|) over the training set, normalized to 100%. "
        "This reflects model-level patterns, not individual student predictions."
    ),
)
async def get_cgpa_global_importance() -> GlobalImportanceResponse:
    try:
        prediction_service.load_artifacts()
        global_imp = explanation_service.get_cgpa_global_importance()
        top_10 = dict(
            sorted(global_imp.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        meta = explanation_service._cgpa_metadata
        return GlobalImportanceResponse(
            model_name=meta.get("model_name", "LinearRegression"),
            model_version=meta.get("model_version", "cgpa_v1.0.0"),
            task_type="cgpa_regression",
            explainer_type=explanation_service._cgpa_explainer.explainer_type,
            global_feature_importance=global_imp,
            top_features=top_10,
            fairness_note=GLOBAL_FAIRNESS_NOTE,
        )
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(fnf))
    except Exception as e:
        logger.error(f"Global importance failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/risk/importance",
    response_model=GlobalImportanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Risk Model Global Feature Importance",
    description=(
        "Returns the precomputed global feature importance for the Phase 4 Risk champion model. "
        "Computed as mean(|SHAP|) averaged over all risk classes and training samples."
    ),
)
async def get_risk_global_importance() -> GlobalImportanceResponse:
    try:
        academic_risk_service.load_artifacts()
        global_imp = explanation_service.get_risk_global_importance()
        top_10 = dict(
            sorted(global_imp.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        meta = explanation_service._risk_metadata
        return GlobalImportanceResponse(
            model_name=meta.get("model_name", "DecisionTreeClassifier"),
            model_version=meta.get("model_version", "risk_v1.0.0"),
            task_type="risk_classification",
            explainer_type=explanation_service._risk_explainer.explainer_type,
            global_feature_importance=global_imp,
            top_features=top_10,
            fairness_note=GLOBAL_FAIRNESS_NOTE,
        )
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(fnf))
    except Exception as e:
        logger.error(f"Risk global importance failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ---------------------------------------------------------------------------
# Conversion helper
# ---------------------------------------------------------------------------

def _convert_explanation_to_schema(ml_explanation) -> ExplanationSchema:
    """Convert ML-layer ExplanationOutput to API ExplanationSchema."""
    return ExplanationSchema(
        model_name=ml_explanation.model_name,
        model_version=ml_explanation.model_version,
        model_type=ml_explanation.model_type,
        explainer_type=ml_explanation.explainer_type,
        explanation_available=ml_explanation.explanation_available,
        task_type=ml_explanation.task_type,
        explained_class=ml_explanation.explained_class,
        top_factors=[
            FeatureContributionSchema(**factor.model_dump())
            for factor in ml_explanation.top_factors
        ],
        positive_factors=[
            FeatureContributionSchema(**factor.model_dump())
            for factor in ml_explanation.positive_factors
        ],
        negative_factors=[
            FeatureContributionSchema(**factor.model_dump())
            for factor in ml_explanation.negative_factors
        ],
        base_value=ml_explanation.base_value,
        shap_sum=ml_explanation.shap_sum,
        top_global_features=ml_explanation.top_global_features,
        fairness_note=ml_explanation.fairness_note,
        contains_demographic_factors=ml_explanation.contains_demographic_factors,
    )
