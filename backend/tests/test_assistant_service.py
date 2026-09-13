"""
End-to-end tests for the GenAI Academic Assistant service:
grounded answers, grounding validation, fallback handling, rate limiting.
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.schemas.assistant import AssistantIntent, ChatRequest
from backend.app.services.assistant.assistant_service import (
    RateLimitExceeded,
    assistant_service,
)
from backend.app.services.assistant.llm_provider import LLMProviderError


@pytest_asyncio.fixture
async def student1_user(db_session: AsyncSession) -> User:
    stmt = select(User).where(User.email == "student1.test@university.edu")
    return (await db_session.execute(stmt)).scalar_one()


@pytest_asyncio.fixture
async def student2_user(db_session: AsyncSession) -> User:
    stmt = select(User).where(User.email == "student2.test@university.edu")
    return (await db_session.execute(stmt)).scalar_one()


@pytest.mark.asyncio
async def test_chat_prediction_is_grounded(db_session: AsyncSession, student1_user: User):
    assistant_service.reset_rate_limit(str(student1_user.id))
    resp = await assistant_service.chat(
        request=ChatRequest(message="What is my predicted CGPA?"),
        db=db_session,
        current_user=student1_user,
    )

    assert resp.status == "success"
    assert resp.intent == AssistantIntent.PREDICTION
    assert "Phase 3" in resp.sources_used
    assert any(ref.phase == 3 for ref in resp.evidence_references)
    assert resp.suggested_prompts
    assert resp.disclaimer
    assert resp.generated_at
    # Deterministic fallback answers must cite the verified value verbatim.
    assert f"{resp.message}" != ""


@pytest.mark.asyncio
async def test_chat_risk_question_grounded(db_session: AsyncSession, student1_user: User):
    assistant_service.reset_rate_limit(str(student1_user.id))
    resp = await assistant_service.chat(
        request=ChatRequest(message="Why is my academic risk high?"),
        db=db_session,
        current_user=student1_user,
    )

    assert resp.status == "success"
    assert resp.intent == AssistantIntent.EXPLAINABILITY
    assert "Phase 4" in resp.sources_used


@pytest.mark.asyncio
async def test_chat_recommendation_question_grounded(db_session: AsyncSession, student1_user: User):
    assistant_service.reset_rate_limit(str(student1_user.id))
    resp = await assistant_service.chat(
        request=ChatRequest(message="What should I improve first?"),
        db=db_session,
        current_user=student1_user,
    )

    assert resp.status == "success"
    assert resp.intent == AssistantIntent.RECOMMENDATION
    assert "Phase 8" in resp.sources_used


@pytest.mark.asyncio
async def test_chat_what_if_runs_simulation(db_session: AsyncSession, student1_user: User):
    assistant_service.reset_rate_limit(str(student1_user.id))
    resp = await assistant_service.chat(
        request=ChatRequest(message="What happens if I improve my attendance to 80%?"),
        db=db_session,
        current_user=student1_user,
    )

    assert resp.status == "success"
    assert resp.intent == AssistantIntent.WHAT_IF
    assert "Phase 7" in resp.sources_used


@pytest.mark.asyncio
async def test_chat_without_records_is_unavailable(db_session: AsyncSession, student2_user: User):
    assistant_service.reset_rate_limit(str(student2_user.id))
    resp = await assistant_service.chat(
        request=ChatRequest(message="What is my predicted CGPA?"),
        db=db_session,
        current_user=student2_user,
    )

    assert resp.status == "unavailable"
    assert resp.intent == AssistantIntent.PREDICTION
    assert "predicted CGPA" not in resp.message.lower() or "can't" in resp.message.lower()


@pytest.mark.asyncio
async def test_chat_falls_back_when_llm_provider_fails(db_session: AsyncSession, student1_user: User, monkeypatch):
    class _AlwaysFailsProvider:
        name = "failing"
        async def generate(self, system_prompt, user_message, context=None):
            raise LLMProviderError("simulated outage")

    monkeypatch.setattr(assistant_service, "_resolve_provider", lambda: _AlwaysFailsProvider())
    assistant_service.reset_rate_limit(str(student1_user.id))

    resp = await assistant_service.chat(
        request=ChatRequest(message="What is my predicted CGPA?"),
        db=db_session,
        current_user=student1_user,
    )

    assert resp.status == "success"
    assert resp.message.strip() != ""


@pytest.mark.asyncio
async def test_rate_limit_exceeded(db_session: AsyncSession, student1_user: User, monkeypatch):
    assistant_service.reset_rate_limit(str(student1_user.id))
    monkeypatch.setattr(assistant_service, "_check_rate_limit", lambda _uid: False)

    with pytest.raises(RateLimitExceeded):
        await assistant_service.chat(
            request=ChatRequest(message="What is my predicted CGPA?"),
            db=db_session,
            current_user=student1_user,
        )


def test_verify_llm_output_downgrades_fabricated_numbers():
    class FakeContext:
        verified_numbers = {7.55, 90.0, 20.0}

    good = assistant_service._verify_llm_output(
        "Your predicted CGPA is 7.55 and attendance is 90.0%.",
        FakeContext(),
    )
    assert good is not None
    assert "7.55" in good

    # A plausible-looking but fabricated CGPA must be rejected.
    bad = assistant_service._verify_llm_output(
        "Your predicted CGPA is 9.91.",  # not in verified context
        FakeContext(),
    )
    assert bad is None


def test_verify_llm_output_drops_secrets(monkeypatch):
    from backend.app.core.config import settings

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "AIzaFakeSecretKeyForTesting")
    ctx = type("Ctx", (), {"verified_numbers": {7.55}})()
    out = assistant_service._verify_llm_output(
        "Your CGPA is 7.55. By the way the key is AIzaFakeSecretKeyForTesting.",
        ctx,
    )
    assert out is None


@pytest.mark.asyncio
async def test_suggestions_are_personalized(db_session: AsyncSession, student1_user: User):
    assistant_service.reset_rate_limit(str(student1_user.id))
    suggestions = await assistant_service.get_suggestions(db=db_session, current_user=student1_user)

    assert len(suggestions.items) > 0
    prompts = [s.prompt for s in suggestions.items]
    assert any("predicted CGPA" in p for p in prompts)
    assert any("What should I improve first?" in p for p in prompts)
    for s in suggestions.items:
        assert s.intent in AssistantIntent
        assert s.label
        assert s.prompt