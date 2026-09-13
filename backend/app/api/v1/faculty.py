"""
FastAPI Router for Phase 10: Faculty Intelligence & Academic Intervention Dashboard.

Endpoints:
- GET  /api/v1/faculty/overview               High-level KPI metrics & academic alerts.
- GET  /api/v1/faculty/students               Prioritized student queue with multi-filter & search.
- GET  /api/v1/faculty/students/{student_id}  Comprehensive single-student dossier.
- GET  /api/v1/faculty/analytics              Class/department aggregate risk analytics.
- POST /api/v1/faculty/assistant/chat         Grounded faculty GenAI decision-support chat.
- GET  /api/v1/faculty/assistant/suggestions  Starter prompts for faculty decision support.
"""

import logging
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_roles
from backend.app.models.user import User, UserRole
from backend.app.schemas.faculty import (
    FacultyAnalyticsResponse,
    FacultyAssistantChatRequest,
    FacultyAssistantChatResponse,
    FacultyOverviewResponse,
    FacultyStudentDossier,
    FacultyStudentListResponse,
    FacultySuggestionsResponse,
)
from backend.app.services.assistant.faculty_context_builder import faculty_assistant_service
from backend.app.services.faculty_service import faculty_service

logger = logging.getLogger("student_predictor.api.faculty")

router = APIRouter(prefix="/faculty", tags=["Faculty Intelligence"])


@router.get(
    "/overview",
    response_model=FacultyOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Faculty Intelligence KPI Overview",
    description="Returns aggregate KPI metrics, risk distributions, performance categories, top risk factors, and non-invasive academic alerts.",
)
async def get_faculty_overview(
    department_id: Optional[uuid.UUID] = Query(None, description="Optional department filter (Admins only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> FacultyOverviewResponse:
    try:
        return await faculty_service.get_faculty_overview(
            db=db, current_user=current_user, department_id=department_id
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        logger.error(f"Failed to generate faculty overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve faculty intelligence overview.",
        )


@router.get(
    "/students",
    response_model=FacultyStudentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Prioritized Student Queue",
    description="Returns a paginated list of students in the priority queue with multi-filter and ranking support.",
)
async def get_faculty_students(
    search: Optional[str] = Query(None, description="Search by student ID or name"),
    risk_level: Optional[str] = Query(None, description="Filter by risk tier (ALL, CRITICAL, HIGH, MEDIUM, LOW)"),
    department_id: Optional[uuid.UUID] = Query(None, description="Filter by department"),
    semester: Optional[int] = Query(None, ge=1, le=12, description="Filter by current semester"),
    min_attendance: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum attendance %"),
    max_attendance: Optional[float] = Query(None, ge=0.0, le=100.0, description="Maximum attendance %"),
    min_cgpa: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum CGPA"),
    max_cgpa: Optional[float] = Query(None, ge=0.0, le=10.0, description="Maximum CGPA"),
    has_backlogs: Optional[bool] = Query(None, description="Filter students with active backlogs"),
    sort_by: str = Query("priority", description="Sort order: priority | risk_score_desc | cgpa_asc | attendance_asc | backlogs_desc | name_asc"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> FacultyStudentListResponse:
    try:
        return await faculty_service.get_faculty_students(
            db=db,
            current_user=current_user,
            search=search,
            risk_level=risk_level,
            department_id=department_id,
            semester=semester,
            min_attendance=min_attendance,
            max_attendance=max_attendance,
            min_cgpa=min_cgpa,
            max_cgpa=max_cgpa,
            has_backlogs=has_backlogs,
            sort_by=sort_by,
            page=page,
            limit=limit,
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        logger.error(f"Failed to fetch faculty students queue: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student priority queue.",
        )


@router.get(
    "/students/{student_id}",
    response_model=FacultyStudentDossier,
    status_code=status.HTTP_200_OK,
    summary="Get Student Intelligence Dossier",
    description="Retrieves a comprehensive academic dossier for an authorized student including Phase 3 predictions, Phase 4 risk, Phase 5 XAI, and Phase 8 recommendations.",
)
async def get_student_dossier(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> FacultyStudentDossier:
    try:
        return await faculty_service.get_faculty_student_dossier(
            db=db, current_user=current_user, student_id=student_id
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        logger.error(f"Failed to load student dossier for {student_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load comprehensive student intelligence dossier.",
        )


@router.get(
    "/analytics",
    response_model=FacultyAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Faculty Class Analytics",
    description="Returns aggregate statistical distributions across CGPA tiers, attendance bands, backlog counts, semester hotspots, and model features.",
)
async def get_faculty_analytics(
    department_id: Optional[uuid.UUID] = Query(None, description="Optional department filter (Admins only)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> FacultyAnalyticsResponse:
    try:
        return await faculty_service.get_faculty_analytics(
            db=db, current_user=current_user, department_id=department_id
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        logger.error(f"Failed to generate class analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve class analytics.",
        )


@router.post(
    "/assistant/chat",
    response_model=FacultyAssistantChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask Faculty Decision-Support Assistant",
    description="Answers natural-language faculty inquiries grounded in verified student group performance and individual dossiers.",
)
async def faculty_assistant_chat(
    request: FacultyAssistantChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> FacultyAssistantChatResponse:
    try:
        return await faculty_assistant_service.chat(
            request=request, db=db, current_user=current_user
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        logger.error(f"Faculty assistant chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Faculty Assistant encountered an error processing the request.",
        )


@router.get(
    "/assistant/suggestions",
    response_model=FacultySuggestionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Faculty Assistant Suggestions",
    description="Returns starter questions tailored for faculty academic decision support.",
)
async def get_faculty_suggestions(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.FACULTY)),
) -> FacultySuggestionsResponse:
    suggestions = faculty_assistant_service.get_suggestions(current_user)
    return FacultySuggestionsResponse(suggestions=suggestions)
