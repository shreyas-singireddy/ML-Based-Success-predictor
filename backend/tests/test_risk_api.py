"""
Tests for AI Academic Risk Prediction API Endpoint (POST /api/v1/predictions/risk).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_predict_risk_api_valid_adhoc_request(client: AsyncClient):
    """Verifies successful 200 response with full risk structure."""
    payload = {
        "attendance_percentage": 68.0,
        "previous_cgpa": 6.20,
        "mid_1": 65.0,
        "mid_2": 62.0,
        "internal_marks": 64.0,
        "backlogs": 1,
        "department_code": "CS",
        "semester": 4,
        "gender": "FEMALE",
        "age": 20,
    }

    response = await client.post("/api/v1/predictions/risk", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "risk_level" in data
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "risk_score" in data
    assert isinstance(data["risk_score"], (int, float))
    assert 0.0 <= data["risk_score"] <= 100.0
    assert "predicted_cgpa" in data
    assert "grade" in data
    assert "performance_category" in data
    assert "risk_probabilities" in data
    assert "risk_factors" in data
    assert len(data["risk_factors"]) == 5
    assert data["model_name"] == "DecisionTreeClassifier"
    assert data["model_version"] == "risk_v1.0.0"
    assert data["prediction_context"] == "adhoc_student"


@pytest.mark.asyncio
async def test_predict_risk_api_invalid_boundaries(client: AsyncClient):
    """Verifies that invalid input values trigger HTTP 422 Unprocessable Content."""
    # Attendance > 100
    bad_payload_att = {
        "attendance_percentage": 105.0,
        "previous_cgpa": 7.0,
        "mid_1": 70.0,
        "mid_2": 70.0,
        "internal_marks": 70.0,
        "backlogs": 0,
    }
    res_att = await client.post("/api/v1/predictions/risk", json=bad_payload_att)
    assert res_att.status_code == 422

    # Negative CGPA
    bad_payload_cgpa = {
        "attendance_percentage": 80.0,
        "previous_cgpa": -1.0,
        "mid_1": 70.0,
        "mid_2": 70.0,
        "internal_marks": 70.0,
        "backlogs": 0,
    }
    res_cgpa = await client.post("/api/v1/predictions/risk", json=bad_payload_cgpa)
    assert res_cgpa.status_code == 422

    # Negative Backlogs
    bad_payload_backlogs = {
        "attendance_percentage": 80.0,
        "previous_cgpa": 7.0,
        "mid_1": 70.0,
        "mid_2": 70.0,
        "internal_marks": 70.0,
        "backlogs": -3,
    }
    res_backlogs = await client.post("/api/v1/predictions/risk", json=bad_payload_backlogs)
    assert res_backlogs.status_code == 422
