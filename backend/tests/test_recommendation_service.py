"""
Integration tests for Phase 8 RecommendationService.
"""

import pytest
from backend.app.schemas.recommendation import RecommendationRequest
from backend.app.services.recommendation_service import recommendation_service


@pytest.mark.asyncio
async def test_recommendation_service_explicit_payload(db_session):
    req = RecommendationRequest(
        attendance_percentage=62.0,
        previous_cgpa=5.8,
        mid_1=50.0,
        mid_2=54.0,
        internal_marks=55.0,
        backlogs=2,
    )

    response = await recommendation_service.generate_recommendations(req, db=db_session)

    assert response.status == "success"
    assert response.predicted_cgpa > 0.0
    assert response.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert len(response.recommendations) > 0

    # Top recommendation should be backlog or attendance
    top_rec = response.recommendations[0]
    assert top_rec.priority in ["CRITICAL", "HIGH"]
    assert len(top_rec.evidence) > 0
    assert top_rec.evidence[0].current_value is not None

    # Check action plan grouping
    plan = response.action_plan
    assert len(plan.this_week) > 0 or len(plan.next_30_days) > 0


@pytest.mark.asyncio
async def test_recommendation_service_high_performer(db_session):
    req = RecommendationRequest(
        attendance_percentage=95.0,
        previous_cgpa=9.2,
        mid_1=90.0,
        mid_2=92.0,
        internal_marks=94.0,
        backlogs=0,
    )

    response = await recommendation_service.generate_recommendations(req, db=db_session)

    assert response.status == "success"
    assert response.risk_level == "LOW"
    # Should include maintain strength recommendation
    categories = [r.category for r in response.recommendations]
    assert "MAINTAIN_STRENGTH" in categories


@pytest.mark.asyncio
async def test_recommendation_service_missing_data_raises():
    req = RecommendationRequest(
        attendance_percentage=65.0,
        # missing other fields and no student_number
    )

    with pytest.raises(ValueError, match="Insufficient academic data"):
        await recommendation_service.generate_recommendations(req, db=None)
