"""
FastAPI Router for Phase 9 GenAI Academic Assistant.

Endpoints:
- POST   /api/v1/assistant/chat         Authenticated grounded chat (students only).
- GET    /api/v1/assistant/suggestions  Personalized starter prompts from real standing.

All intelligence is computed by the backend engines; the LLM only translates
verified context. RBAC and anti-injection guardrails are enforced in the
service layer.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.assistant import ChatRequest, ChatResponse, SuggestionsResponse
from backend.app.services.assistant.assistant_service import (
    RateLimitExceeded,
    assistant_service,
)

logger = logging.getLogger("student_predictor.api.assistant")

router = APIRouter(prefix="/assistant", tags=["GenAI Assistant"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask the GenAI Academic Assistant",
    description=(
        "Answers natural-language questions about the authenticated student's verified academic "
        "standing using grounded context from Phases 3-8. The LLM only translates verified "
        "intelligence; it never computes predictions or alters records."
    ),
)
async def assistant_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    try:
        return await assistant_service.chat(
            request=request,
            db=db,
            current_user=current_user,
        )
    except PermissionError as pe:
        logger.warning(f"Unauthorized assistant access: {pe}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        )
    except RateLimitExceeded as rle:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(rle),
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Assistant chat failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The academic assistant could not complete the request. Please try again.",
        )


@router.get(
    "/suggestions",
    response_model=SuggestionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Personalized Starter Suggestions",
    description=(
        "Returns deterministic starter prompts tailored to the authenticated student's real "
        "academic standing (risk level, attendance, backlogs, recommendations). No LLM is invoked."
    ),
)
async def get_suggestions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuggestionsResponse:
    try:
        return await assistant_service.get_suggestions(db=db, current_user=current_user)
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Assistant suggestions failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate starter suggestions.",
        )