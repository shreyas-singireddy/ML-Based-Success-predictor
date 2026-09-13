"""
FastAPI Router for Phase 8 AI Personalized Recommendation Engine.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user_optional, get_current_user
from backend.app.models.user import User, UserRole
from backend.app.models.student import StudentProfile
from backend.app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from backend.app.services.recommendation_service import recommendation_service

logger = logging.getLogger("student_predictor.api.recommendations")

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post(
    "/generate",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Personalized Academic Recommendations",
    description=(
        "Synthesizes student academic profile, Phase 3 predicted CGPA, Phase 4 risk classification, "
        "Phase 5 SHAP feature contributions, and Phase 7 What-If simulations into ranked, "
        "evidence-backed, actionable recommendations and a temporal action plan."
    ),
)
async def generate_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RecommendationResponse:
    try:
        response = await recommendation_service.generate_recommendations(
            request=request,
            db=db,
            current_user=current_user,
        )
        return response
    except ValueError as ve:
        logger.warning(f"Validation error in recommendation request: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except PermissionError as pe:
        logger.warning(f"Unauthorized recommendation access: {pe}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        )
    except FileNotFoundError as fnf:
        logger.error(f"Recommendation artifact missing: {fnf}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recommendation engine is currently unavailable. Trained model artifacts are missing.",
        )
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate personalized recommendations. Please verify student data.",
        )


@router.get(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Recommendations for Current Student",
    description="Fetches personalized recommendations and action plan for the authenticated student using their latest verified academic record.",
)
async def get_my_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationResponse:
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The GET /recommendations endpoint is designated for students. Staff should use POST /recommendations/generate with a student_number.",
        )

    stmt = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    res = await db.execute(stmt)
    student = res.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No student profile linked to your user account.",
        )

    try:
        req = RecommendationRequest(student_number=student.student_number)
        return await recommendation_service.generate_recommendations(
            request=req,
            db=db,
            current_user=current_user,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to fetch student recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate personalized recommendations.",
        )
