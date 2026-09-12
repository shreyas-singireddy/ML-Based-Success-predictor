"""
Tests for Prediction Service (Inference, Metadata Loading, Compatibility, Feature Handling).
"""

import pytest
from backend.app.schemas.prediction import CGPAPredictionRequest
from backend.app.services.prediction_service import prediction_service


@pytest.mark.asyncio
async def test_prediction_service_adhoc_payload():
    req = CGPAPredictionRequest(
        attendance_percentage=82.0,
        previous_cgpa=7.40,
        mid_1=72.0,
        mid_2=76.0,
        internal_marks=78.0,
        backlogs=0,
        department_code="CS",
        semester=4,
        gender="MALE",
        age=20,
    )

    response = await prediction_service.predict_cgpa(req)

    assert response.status == "success"
    assert isinstance(response.predicted_cgpa, float)
    assert 0.0 <= response.predicted_cgpa <= 10.0
    assert response.model_name in ["LinearRegression", "RandomForestRegressor", "XGBRegressor"]
    assert response.model_version == "cgpa_v1.0.0"
    
    # Verify feature summary contents
    fs = response.feature_summary
    assert fs.academic_average == round((72.0 + 76.0 + 78.0) / 3.0, 2)
    assert fs.attendance_risk_category == "NORMAL"
    assert fs.backlog_severity_category == "NONE"


@pytest.mark.asyncio
async def test_prediction_service_extreme_inputs():
    # Test high performer
    req_high = CGPAPredictionRequest(
        attendance_percentage=98.0,
        previous_cgpa=9.50,
        mid_1=95.0,
        mid_2=98.0,
        internal_marks=96.0,
        backlogs=0,
    )
    res_high = await prediction_service.predict_cgpa(req_high)

    # Test struggling performer with backlogs
    req_low = CGPAPredictionRequest(
        attendance_percentage=55.0,
        previous_cgpa=5.20,
        mid_1=45.0,
        mid_2=48.0,
        internal_marks=50.0,
        backlogs=3,
    )
    res_low = await prediction_service.predict_cgpa(req_low)

    # Assert model produces logically distinct predictions
    assert res_high.predicted_cgpa > res_low.predicted_cgpa
    assert res_high.predicted_cgpa >= 8.0
    assert res_low.predicted_cgpa <= 7.0
