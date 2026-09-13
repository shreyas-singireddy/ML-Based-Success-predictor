"""
Tests for the verified context builder of the GenAI Academic Assistant.

Confirms that context is assembled ONLY from the authenticated student's own
profile/records plus the authorised Phase 3-8 engines, and that all relevant
verified numeric values are collected for the grounding guard.
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.services.assistant.context_builder import (
    ContextUnavailableError,
    context_builder,
    format_context,
)


@pytest_asyncio.fixture
async def student1_user(db_session: AsyncSession) -> User:
    stmt = select(User).where(User.email == "student1.test@university.edu")
    return (await db_session.execute(stmt)).scalar_one()


@pytest_asyncio.fixture
async def student2_user(db_session: AsyncSession) -> User:
    stmt = select(User).where(User.email == "student2.test@university.edu")
    return (await db_session.execute(stmt)).scalar_one()


@pytest.mark.asyncio
async def test_context_build_full_for_student_with_record(db_session: AsyncSession, student1_user: User):
    ctx = await context_builder.build(current_user=student1_user, db=db_session)

    assert ctx.student["student_number"] == "STU-TEST-001"
    assert ctx.student["name"] == "Student One"
    assert ctx.latest_record["semester"] == 1
    assert ctx.latest_record["attendance_percentage"] == 90.0
    assert ctx.latest_record["backlogs"] == 0

    assert ctx.has_prediction
    assert 0.0 <= ctx.prediction["predicted_cgpa"] <= 10.0
    assert ctx.has_risk
    assert ctx.risk["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert 0.0 <= ctx.risk["risk_score"] <= 100.0

    assert "Phase 2" in ctx.sources_used
    assert "Phase 3" in ctx.sources_used
    assert "Phase 4" in ctx.sources_used
    assert "Phase 5" in ctx.sources_used
    assert "Phase 8" in ctx.sources_used

    for ref in ctx.evidence_references:
        assert ref.phase in (2, 3, 4, 5, 7, 8)
        assert ref.title
        assert ref.description

    # Grounding numbers must cover the key verified values.
    assert ctx.prediction["predicted_cgpa"] in ctx.verified_numbers
    assert ctx.latest_record["attendance_percentage"] in ctx.verified_numbers
    assert ctx.risk["risk_score"] in ctx.verified_numbers

    rendered = format_context(ctx)
    assert "PREDICTED CGPA" in rendered
    assert "ACADEMIC RISK" in rendered
    assert isinstance(rendered, str) and len(rendered) > 0


@pytest.mark.asyncio
async def test_context_build_includes_phase7_simulation(db_session: AsyncSession, student1_user: User):
    ctx = await context_builder.build(
        current_user=student1_user,
        db=db_session,
        what_if_overrides={"attendance_percentage": 80.0},
        include_simulation=True,
    )

    assert ctx.simulation is not None
    assert ctx.simulation["baseline_predicted_cgpa"] in ctx.verified_numbers
    assert ctx.simulation["simulated_predicted_cgpa"] in ctx.verified_numbers
    assert "Phase 7" in ctx.sources_used

    rendered = format_context(ctx)
    assert "WHAT-IF SIMULATION" in rendered


@pytest.mark.asyncio
async def test_context_build_without_simulation_by_default(db_session: AsyncSession, student1_user: User):
    ctx = await context_builder.build(
        current_user=student1_user,
        db=db_session,
        what_if_overrides={"attendance_percentage": 80.0},
        include_simulation=False,
    )
    assert ctx.simulation is None
    assert "Phase 7" not in ctx.sources_used


@pytest.mark.asyncio
async def test_context_build_student_without_records_has_no_prediction(db_session: AsyncSession, student2_user: User):
    ctx = await context_builder.build(current_user=student2_user, db=db_session)

    assert ctx.student["student_number"] == "STU-TEST-002"
    assert ctx.latest_record == {}
    assert not ctx.has_prediction
    assert ctx.prediction is None
    assert ctx.risk is None


@pytest.mark.asyncio
async def test_context_build_without_profile_raises_unavailable(db_session: AsyncSession):
    from backend.app.models.user import UserRole

    ghost = User(
        email="ghost.test@university.edu",
        hashed_password="x",
        full_name="Ghost",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(ghost)
    await db_session.flush()

    with pytest.raises(ContextUnavailableError):
        await context_builder.build(current_user=ghost, db=db_session)


@pytest.mark.asyncio
async def test_context_build_collects_shap_scores_when_available(db_session: AsyncSession, student1_user: User):
    ctx = await context_builder.build(current_user=student1_user, db=db_session)

    if ctx.shap:
        for factor in ctx.shap.get("positive_factors", []) + ctx.shap.get("negative_factors", []):
            assert round(float(factor["shap_value"]), 3) in ctx.verified_numbers
    else:
        # SHAP may be gracefully unavailable; context must still be usable.
        assert ctx.has_prediction