"""
FastAPI Router for AI CGPA Predictions.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user_optional
from backend.app.models.user import User
from backend.app.schemas.prediction import CGPAPredictionRequest, CGPAPredictionResponse
from backend.app.services.prediction_service import prediction_service

logger = logging.getLogger("student_predictor.api.predictions")

router = APIRouter(prefix="/predictions", tags=["Predictions"])


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
