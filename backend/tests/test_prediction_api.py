"""
Tests for Prediction API Endpoint (POST /api/v1/predictions/cgpa).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_predict_cgpa_api_valid_adhoc_request(client: AsyncClient):
    payload = {
        "attendance_percentage": 82.0,
        "previous_cgpa": 7.40,
        "mid_1": 72.0,
        "mid_2": 76.0,
        "internal_marks": 78.0,
        "backlogs": 0,
        "department_code": "CS",
        "semester": 4,
        "gender": "MALE",
        "age": 20,
    }

    response = await client.post("/api/v1/predictions/cgpa", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "predicted_cgpa" in data
    assert isinstance(data["predicted_cgpa"], float)
    assert 0.0 <= data["predicted_cgpa"] <= 10.0
    assert data["model_name"] == "LinearRegression"
    assert data["model_version"] == "cgpa_v1.0.0"
    assert data["prediction_context"] == "adhoc_student"
    assert "feature_summary" in data
    assert data["feature_summary"]["academic_average"] == 75.33


@pytest.mark.asyncio
async def test_predict_cgpa_api_invalid_boundaries(client: AsyncClient):
    # Attendance > 100
    bad_payload_att = {
        "attendance_percentage": 115.0,
        "previous_cgpa": 7.40,
        "mid_1": 72.0,
        "mid_2": 76.0,
        "internal_marks": 78.0,
        "backlogs": 0,
    }
    res_att = await client.post("/api/v1/predictions/cgpa", json=bad_payload_att)
    assert res_att.status_code == 422

    # Negative Marks
    bad_payload_marks = {
        "attendance_percentage": 80.0,
        "previous_cgpa": 7.40,
        "mid_1": -10.0,
        "mid_2": 76.0,
        "internal_marks": 78.0,
        "backlogs": 0,
    }
    res_marks = await client.post("/api/v1/predictions/cgpa", json=bad_payload_marks)
    assert res_marks.status_code == 422

    # Negative Backlogs
    bad_payload_backlogs = {
        "attendance_percentage": 80.0,
        "previous_cgpa": 7.40,
        "mid_1": 72.0,
        "mid_2": 76.0,
        "internal_marks": 78.0,
        "backlogs": -2,
    }
    res_backlogs = await client.post("/api/v1/predictions/cgpa", json=bad_payload_backlogs)
    assert res_backlogs.status_code == 422
