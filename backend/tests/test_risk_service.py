"""
Unit Tests for AI Academic Risk Prediction Service.
"""

import pytest
from backend.app.schemas.risk_prediction import RiskPredictionRequest, RiskPredictionResponse
from backend.app.services.risk_service import academic_risk_service


@pytest.mark.asyncio
async def test_predict_risk_adhoc_student():
    """Verifies end-to-end academic risk inference for an ad-hoc student."""
    req = RiskPredictionRequest(
        student_number=None,
        gender="FEMALE",
        age=21,
        department_code="CS",
        semester=4,
        attendance_percentage=68.0,
        previous_cgpa=6.2,
        mid_1=65.0,
        mid_2=62.0,
        internal_marks=60.0,
        backlogs=1,
    )

    resp = await academic_risk_service.predict_risk(req)

    assert isinstance(resp, RiskPredictionResponse)
    assert resp.status == "success"
    assert resp.prediction_context == "adhoc_student"
    assert resp.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert 0.0 <= resp.risk_score <= 100.0
    assert 0.0 <= resp.predicted_cgpa <= 10.0
    assert resp.grade in ["O", "A+", "A", "B", "C"]
    assert resp.performance_category in ["EXCELLENT", "GOOD", "AVERAGE", "AT_RISK"]
    assert len(resp.risk_factors) == 5
    assert len(resp.risk_probabilities) == 4
    assert pytest.approx(sum(resp.risk_probabilities.values()), rel=1e-3) == 1.0


@pytest.mark.asyncio
async def test_risk_and_performance_separation():
    """
    Verifies that Performance Category and Risk Level are distinct.
    A student with CGPA 6.2 (AVERAGE) but attendance 62% and 1 backlog can have HIGH/CRITICAL risk.
    """
    req = RiskPredictionRequest(
        student_number=None,
        attendance_percentage=60.0,
        previous_cgpa=6.4,
        mid_1=65.0,
        mid_2=65.0,
        internal_marks=65.0,
        backlogs=2,
    )

    resp = await academic_risk_service.predict_risk(req)
    assert resp.risk_level in ["HIGH", "CRITICAL"]
    assert resp.performance_category in ["AVERAGE", "GOOD"]
