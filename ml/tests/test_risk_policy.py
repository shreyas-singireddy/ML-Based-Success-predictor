"""
Unit Tests for Deterministic Risk Policy Engine, Factor Breakdown, and Grading Rules.
"""

import pytest
import pandas as pd
from ml.classification.risk_policy import (
    RiskLevel,
    PerformanceCategory,
    RiskPolicyEngine,
    calculate_normalized_risk_score,
    map_cgpa_to_grade,
    map_cgpa_to_performance_category,
)


def test_risk_level_boundaries():
    """Tests deterministic boundary conditions for LOW, MEDIUM, HIGH, and CRITICAL."""
    # Strong academic record -> LOW
    assert RiskPolicyEngine.evaluate_risk_level(attendance=85.0, backlogs=0, cgpa=8.2, trend=0.1) == RiskLevel.LOW

    # Moderate CGPA, clean backlogs, good attendance -> MEDIUM
    assert RiskPolicyEngine.evaluate_risk_level(attendance=78.0, backlogs=0, cgpa=7.0, trend=0.0) == RiskLevel.MEDIUM

    # Low attendance (70%) or 1 backlog -> HIGH
    assert RiskPolicyEngine.evaluate_risk_level(attendance=70.0, backlogs=0, cgpa=8.0, trend=0.0) == RiskLevel.HIGH
    assert RiskPolicyEngine.evaluate_risk_level(attendance=85.0, backlogs=1, cgpa=8.0, trend=0.0) == RiskLevel.HIGH

    # Critical attendance (<65%), 3+ backlogs, or CGPA < 5.5 -> CRITICAL
    assert RiskPolicyEngine.evaluate_risk_level(attendance=60.0, backlogs=0, cgpa=8.0, trend=0.0) == RiskLevel.CRITICAL
    assert RiskPolicyEngine.evaluate_risk_level(attendance=85.0, backlogs=3, cgpa=8.0, trend=0.0) == RiskLevel.CRITICAL
    assert RiskPolicyEngine.evaluate_risk_level(attendance=85.0, backlogs=0, cgpa=5.2, trend=0.0) == RiskLevel.CRITICAL


def test_conflicting_conditions_severity_precedence():
    """
    Verifies that when conflicting indicators trigger, the highest severity always wins:
    LOW < MEDIUM < HIGH < CRITICAL
    """
    # High CGPA (8.5 -> LOW), but critically low attendance (60.0% -> CRITICAL) -> Must be CRITICAL
    res1 = RiskPolicyEngine.evaluate_risk_level(attendance=60.0, backlogs=0, cgpa=8.5, trend=0.2)
    assert res1 == RiskLevel.CRITICAL

    # High CGPA (8.0 -> LOW), good attendance (85% -> LOW), but 2 backlogs (HIGH) -> Must be HIGH
    res2 = RiskPolicyEngine.evaluate_risk_level(attendance=85.0, backlogs=2, cgpa=8.0, trend=0.0)
    assert res2 == RiskLevel.HIGH

    # High CGPA (8.0 -> LOW), good attendance (85% -> LOW), but sharp negative trend (-0.8 -> HIGH) -> Must be HIGH
    res3 = RiskPolicyEngine.evaluate_risk_level(attendance=85.0, backlogs=0, cgpa=8.0, trend=-0.8)
    assert res3 == RiskLevel.HIGH


def test_normalized_risk_score_calculation():
    """Tests probability-weighted continuous normalized risk score."""
    # 100% LOW -> 0.0
    assert calculate_normalized_risk_score({"LOW": 1.0, "MEDIUM": 0.0, "HIGH": 0.0, "CRITICAL": 0.0}) == 0.0

    # 100% CRITICAL -> 100.0
    assert calculate_normalized_risk_score({"LOW": 0.0, "MEDIUM": 0.0, "HIGH": 0.0, "CRITICAL": 1.0}) == 100.0

    # 50% HIGH, 50% CRITICAL -> 100 * (0.67*0.5 + 1.0*0.5) = 83.5
    score = calculate_normalized_risk_score({"LOW": 0.0, "MEDIUM": 0.0, "HIGH": 0.5, "CRITICAL": 0.5})
    assert score == pytest.approx(83.5, rel=1e-2)


def test_performance_category_and_grade_mappings():
    """Tests institutional grading and performance categories."""
    assert map_cgpa_to_performance_category(9.2) == PerformanceCategory.EXCELLENT.value
    assert map_cgpa_to_performance_category(7.5) == PerformanceCategory.GOOD.value
    assert map_cgpa_to_performance_category(6.2) == PerformanceCategory.AVERAGE.value
    assert map_cgpa_to_performance_category(4.8) == PerformanceCategory.AT_RISK.value

    assert map_cgpa_to_grade(9.5) == "O"
    assert map_cgpa_to_grade(8.4) == "A+"
    assert map_cgpa_to_grade(7.2) == "A"
    assert map_cgpa_to_grade(6.0) == "B"
    assert map_cgpa_to_grade(5.0) == "C"


def test_risk_factor_breakdown_generation():
    """Tests transparent 5-factor breakdown generation."""
    factors = RiskPolicyEngine.generate_risk_factor_breakdown(
        attendance=62.0,
        backlogs=2,
        mid_terms=55.0,
        previous_cgpa=6.0,
        academic_trend=-0.6,
    )
    assert len(factors) == 5
    factor_names = [f["factor"] for f in factors]
    assert "Attendance" in factor_names
    assert "Backlogs" in factor_names
    assert "Mid-Term Performance" in factor_names
    assert "Cumulative/Previous CGPA" in factor_names
    assert "Academic Trend" in factor_names

    # Check attendance factor detail
    att_f = next(f for f in factors if f["factor"] == "Attendance")
    assert att_f["level"] == "CRITICAL"
    assert att_f["value"] == 62.0
