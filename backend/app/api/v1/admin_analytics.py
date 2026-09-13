"""
FastAPI Router for Phase 13: System-wide Analytics & Admin Intelligence.

Endpoints:
- GET /api/v1/admin/analytics/overview         Institution-wide overview KPI statistics
- GET /api/v1/admin/analytics/risk             Risk intelligence, breakdown & correlation
- GET /api/v1/admin/analytics/performance      CGPA distributions, attendance, backlogs
- GET /api/v1/admin/analytics/departments      Department-level comparative intelligence
- GET /api/v1/admin/analytics/semesters        Semester-level metrics
- GET /api/v1/admin/analytics/interventions    Intervention distributions & outcome analytics
"""

import logging
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import require_roles
from backend.app.models.user import User, UserRole
from backend.app.schemas.admin_analytics import (
    AdminAcademicPerformanceAnalytics,
    AdminDepartmentAnalyticsResponse,
    AdminInterventionsAnalytics,
    AdminOverviewAnalytics,
    AdminRiskAnalytics,
    AdminSemesterAnalyticsResponse,
)
from backend.app.services.admin_analytics_service import AdminAnalyticsService

logger = logging.getLogger("student_predictor.api.admin_analytics")

router = APIRouter(prefix="/admin/analytics", tags=["System-wide Admin Analytics"])


@router.get(
    "/overview",
    response_model=AdminOverviewAnalytics,
    status_code=status.HTTP_200_OK,
    summary="Get System Overview Analytics (Admin Only)",
    description="Returns institution-wide KPI counts, risk distributions, alert volumes, and intervention summaries.",
)
async def get_admin_overview(
    department_id: Optional[uuid.UUID] = Query(None, description="Optional department filter"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Optional semester filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminOverviewAnalytics:
    try:
        return await AdminAnalyticsService.get_overview(
            db=db, department_id=department_id, semester=semester
        )
    except Exception as e:
        logger.error(f"Failed to fetch admin overview analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch system overview analytics.",
        )


@router.get(
    "/risk",
    response_model=AdminRiskAnalytics,
    status_code=status.HTTP_200_OK,
    summary="Get Risk Intelligence Analytics (Admin Only)",
    description="Returns institution-wide risk distribution, department/semester risk breakdowns, and attendance-risk correlations.",
)
async def get_admin_risk(
    department_id: Optional[uuid.UUID] = Query(None, description="Optional department filter"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Optional semester filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminRiskAnalytics:
    try:
        return await AdminAnalyticsService.get_risk_analytics(
            db=db, department_id=department_id, semester=semester
        )
    except Exception as e:
        logger.error(f"Failed to fetch admin risk analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch risk intelligence analytics.",
        )


@router.get(
    "/performance",
    response_model=AdminAcademicPerformanceAnalytics,
    status_code=status.HTTP_200_OK,
    summary="Get Academic Performance Analytics (Admin Only)",
    description="Returns institution-level CGPA distributions, attendance rates, backlog metrics, and department performances.",
)
async def get_admin_performance(
    department_id: Optional[uuid.UUID] = Query(None, description="Optional department filter"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Optional semester filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminAcademicPerformanceAnalytics:
    try:
        return await AdminAnalyticsService.get_performance_analytics(
            db=db, department_id=department_id, semester=semester
        )
    except Exception as e:
        logger.error(f"Failed to fetch admin performance analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch academic performance analytics.",
        )


@router.get(
    "/departments",
    response_model=AdminDepartmentAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Department Analytics (Admin Only)",
    description="Returns cross-department comparative metrics.",
)
async def get_admin_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminDepartmentAnalyticsResponse:
    try:
        return await AdminAnalyticsService.get_department_analytics(db=db)
    except Exception as e:
        logger.error(f"Failed to fetch department analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch department analytics.",
        )


@router.get(
    "/semesters",
    response_model=AdminSemesterAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Semester Analytics (Admin Only)",
    description="Returns semester-level comparative metrics across semesters 1 to 8.",
)
async def get_admin_semesters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminSemesterAnalyticsResponse:
    try:
        return await AdminAnalyticsService.get_semester_analytics(db=db)
    except Exception as e:
        logger.error(f"Failed to fetch semester analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch semester analytics.",
        )


@router.get(
    "/interventions",
    response_model=AdminInterventionsAnalytics,
    status_code=status.HTTP_200_OK,
    summary="Get Intervention Analytics (Admin Only)",
    description="Returns institution-wide intervention completion rates, categories, and observational outcome distributions.",
)
async def get_admin_interventions(
    department_id: Optional[uuid.UUID] = Query(None, description="Optional department filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> AdminInterventionsAnalytics:
    try:
        return await AdminAnalyticsService.get_interventions_analytics(
            db=db, department_id=department_id
        )
    except Exception as e:
        logger.error(f"Failed to fetch admin intervention analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch intervention analytics.",
        )
