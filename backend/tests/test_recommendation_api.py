"""
API endpoint tests for Phase 8 Recommendation Engine routes.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_generate_recommendations_api_success():
    payload = {
        "attendance_percentage": 68.0,
        "previous_cgpa": 6.4,
        "mid_1": 56.0,
        "mid_2": 58.0,
        "internal_marks": 62.0,
        "backlogs": 1,
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/recommendations/generate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "predicted_cgpa" in data
    assert "risk_level" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    assert "action_plan" in data
    assert "policy_version" in data


@pytest.mark.asyncio
async def test_generate_recommendations_invalid_payload():
    # Negative attendance and invalid backlog
    payload = {
        "attendance_percentage": -10.0,
        "previous_cgpa": 12.0,
        "mid_1": 50.0,
        "mid_2": 50.0,
        "internal_marks": 50.0,
        "backlogs": -5,
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/recommendations/generate", json=payload)

    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_get_my_recommendations_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/recommendations")

    assert response.status_code in [401, 403]
