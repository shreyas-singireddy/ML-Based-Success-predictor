"""
FastAPI Router for Phase 12: Intervention Tracking & Outcome Management.

Endpoints:
- POST  /api/v1/interventions                          Create an intervention for an authorized student
- GET   /api/v1/interventions                          List interventions with pagination & filtering
- GET   /api/v1/interventions/dashboard-stats          Summary counts for dashboard
- GET   /api/v1/interventions/{id}                     Get intervention detail
- PATCH /api/v1/interventions/{id}                     Update an intervention
- POST  /api/v1/interventions/{id}/complete            Mark intervention completed
- POST  /api/v1/interventions/{id}/follow-up           Record follow-up notes
- POST  /api/v1/interventions/{id}/outcome             Record outcome measurement
- GET   /api/v1/interventions/{id}/comparison          Get before/after comparison
- GET   /api/v1/students/{student_id}/interventions    Get student-specific interventions
"""

import logging
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import require_roles
from backend.app.models.intervention import (
    InterventionCategory,
    InterventionPriority,
    InterventionStatus,
)
from backend.app.models.user import User, UserRole
from backend.app.schemas.intervention import (
    BeforeAfterComparisonResponse,
    InterventionCompleteRequest,
    InterventionCreate,
    InterventionDashboardStats,
    InterventionDetailResponse,
    InterventionFollowUpRequest,
    InterventionListResponse,
    InterventionOutcomeCreate,
    InterventionOutcomeResponse,
    InterventionResponse,
    InterventionUpdate,
)
from backend.app.services.intervention_service import InterventionService

logger = logging.getLogger("student_predictor.api.interventions")

router = APIRouter(tags=["Intervention Tracking & Outcome Management"])


@router.post(
    "/interventions",
    response_model=InterventionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Faculty Intervention",
    description="Creates a new academic intervention for an authorized student, capturing baseline indicator snapshots.",
)
async def create_intervention(
    payload: InterventionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> InterventionResponse:
    try:
        intervention = await InterventionService.create_intervention(
            db=db, current_user=current_user, data=payload
        )
        loaded = await InterventionService.get_intervention_by_id(
            db=db, current_user=current_user, intervention_id=intervention.id
        )
        return InterventionService.to_intervention_response(loaded)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except LookupError as le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(le))
    except Exception as e:
        logger.error(f"Failed to create intervention: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create intervention: {str(e)}",
        )


@router.get(
    "/interventions/dashboard-stats",
    response_model=InterventionDashboardStats,
    status_code=status.HTTP_200_OK,
    summary="Get Intervention Dashboard Stats",
    description="Returns aggregate counts of active, pending follow-ups, completed, and measured outcome statuses.",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> InterventionDashboardStats:
    try:
        return await InterventionService.get_dashboard_stats(db=db, current_user=current_user)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        logger.error(f"Failed to fetch intervention dashboard stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch intervention stats.",
        )


@router.get(
    "/interventions",
    response_model=InterventionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Interventions",
    description="Retrieves a paginated list of interventions scoped to user permissions with multi-criteria filtering.",
)
async def list_interventions(
    student_id: Optional[uuid.UUID] = Query(None, description="Filter by student ID"),
    status: Optional[InterventionStatus] = Query(None, description="Filter by status"),
    category: Optional[InterventionCategory] = Query(None, description="Filter by category"),
    priority: Optional[InterventionPriority] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search keyword"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> InterventionListResponse:
    try:
        return await InterventionService.list_interventions(
            db=db,
            current_user=current_user,
            student_id=student_id,
            status=status,
            category=category,
            priority=priority,
            search=search,
            page=page,
            page_size=page_size,
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        logger.error(f"Failed to list interventions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list interventions.",
        )


@router.get(
    "/interventions/{intervention_id}",
    response_model=InterventionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Intervention Details",
    description="Retrieves single intervention details including before/after comparison if outcome exists.",
)
async def get_intervention_detail(
    intervention_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> InterventionDetailResponse:
    try:
        intervention = await InterventionService.get_intervention_by_id(
            db=db, current_user=current_user, intervention_id=intervention_id
        )
        base_resp = InterventionService.to_intervention_response(intervention)
        comparison = InterventionService.build_comparison(intervention)
        return InterventionDetailResponse(
            **base_resp.model_dump(),
            comparison=comparison,
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except LookupError as le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(le))
    except Exception as e:
        logger.error(f"Failed to get intervention detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get intervention detail.",
        )


@router.patch(
    "/interventions/{intervention_id}",
    response_model=InterventionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Intervention",
    description="Updates intervention fields, notes, status, or dates.",
)
async def update_intervention(
    intervention_id: uuid.UUID,
    payload: InterventionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> InterventionResponse:
    try:
        updated = await InterventionService.update_intervention(
            db=db, current_user=current_user, intervention_id=intervention_id, data=payload
        )
        loaded = await InterventionService.get_intervention_by_id(
            db=db, current_user=current_user, intervention_id=updated.id
        )
        return InterventionService.to_intervention_response(loaded)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except LookupError as le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(le))
    except Exception as e:
        logger.error(f"Failed to update intervention: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update intervention.",
        )


@router.post(
    "/interventions/{intervention_id}/complete",
    response_model=InterventionResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete Intervention",
    description="Marks an intervention as completed, records completion notes, and optionally schedules a follow-up.",
)
async def complete_intervention(
    intervention_id: uuid.UUID,
    payload: InterventionCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> InterventionResponse:
    try:
        completed = await InterventionService.complete_intervention(
            db=db, current_user=current_user, intervention_id=intervention_id, data=payload
        )
        loaded = await InterventionService.get_intervention_by_id(
            db=db, current_user=current_user, intervention_id=completed.id
        )
        return InterventionService.to_intervention_response(loaded)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except LookupError as le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(le))
    except Exception as e:
        logger.error(f"Failed to complete intervention: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete intervention.",
        )


@router.post(
    "/interventions/{intervention_id}/follow-up",
    response_model=InterventionResponse,
    status_code=status.HTTP_200_OK,
    summary="Record Follow-up",
    description="Appends follow-up progress notes and updates follow-up schedule.",
)
async def record_follow_up(
    intervention_id: uuid.UUID,
    payload: InterventionFollowUpRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> InterventionResponse:
    try:
        updated = await InterventionService.record_follow_up(
            db=db, current_user=current_user, intervention_id=intervention_id, data=payload
        )
        loaded = await InterventionService.get_intervention_by_id(
            db=db, current_user=current_user, intervention_id=updated.id
        )
        return InterventionService.to_intervention_response(loaded)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except LookupError as le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(le))
    except Exception as e:
        logger.error(f"Failed to record follow-up: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record follow-up.",
        )


@router.post(
    "/interventions/{intervention_id}/outcome",
    response_model=InterventionOutcomeResponse,
    status_code=status.HTTP_200_OK,
    summary="Record Intervention Outcome",
    description="Records observational outcome measurements comparing baseline indicators with current follow-up metrics.",
)
async def record_outcome(
    intervention_id: uuid.UUID,
    payload: InterventionOutcomeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> InterventionOutcomeResponse:
    try:
        outcome = await InterventionService.record_outcome(
            db=db, current_user=current_user, intervention_id=intervention_id, data=payload
        )
        return InterventionOutcomeResponse.model_validate(outcome)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except LookupError as le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(le))
    except Exception as e:
        logger.error(f"Failed to record outcome: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record outcome.",
        )


@router.get(
    "/interventions/{intervention_id}/comparison",
    response_model=BeforeAfterComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Before/After Comparison",
    description="Provides observational Before/After delta comparison across risk, CGPA, attendance, and backlogs.",
)
async def get_intervention_comparison(
    intervention_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> BeforeAfterComparisonResponse:
    try:
        intervention = await InterventionService.get_intervention_by_id(
            db=db, current_user=current_user, intervention_id=intervention_id
        )
        return InterventionService.build_comparison(intervention)
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except LookupError as le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(le))
    except Exception as e:
        logger.error(f"Failed to get comparison: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get before/after comparison.",
        )


@router.get(
    "/students/{student_id}/interventions",
    response_model=InterventionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Student Interventions",
    description="Lists all interventions and history for a specific student.",
)
async def get_student_interventions(
    student_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> InterventionListResponse:
    try:
        return await InterventionService.list_interventions(
            db=db,
            current_user=current_user,
            student_id=student_id,
            page=page,
            page_size=page_size,
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        logger.error(f"Failed to get student interventions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get student interventions.",
        )
