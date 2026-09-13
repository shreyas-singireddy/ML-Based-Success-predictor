"""
Unit tests for Phase 8 Deterministic Recommendation Rules.
"""

import pytest
from ml.recommendations.recommendation_config import (
    RecommendationCategory,
    RecommendationPriority,
    RecommendationSource,
    ExpectedImpact,
    TimeHorizon,
    RecommendationPolicyConfig,
)
from ml.recommendations.rules import (
    AttendanceRecommendationRule,
    BacklogRecommendationRule,
    MidtermExamRecommendationRule,
    InternalAssessmentRecommendationRule,
    AcademicTrendRecommendationRule,
    StrengthMaintenanceRule,
)


class DummyCGPAPrediction:
    def __init__(self, predicted_cgpa=6.5, trend=0.0):
        self.predicted_cgpa = predicted_cgpa
        self.feature_summary = type("FS", (), {"previous_cgpa_trend": trend})()


class DummyRiskPrediction:
    def __init__(self, risk_level="HIGH", risk_score=75.0):
        self.risk_level = risk_level
        self.risk_score = risk_score
        self.grade = "B"
        self.performance_category = "AVERAGE"


class DummyExplanation:
    def __init__(self, factors):
        self.top_factors = [
            type("Factor", (), {"feature_name": k, "shap_value": v})()
            for k, v in factors.items()
        ]


def test_attendance_rule_critical():
    rule = AttendanceRecommendationRule()
    raw_data = {"attendance_percentage": 60.0}
    rec = rule.evaluate(raw_data, None, None, None, None)

    assert rec is not None
    assert rec.id == "rec-attendance-improvement"
    assert rec.priority == RecommendationPriority.CRITICAL
    assert rec.category == RecommendationCategory.ATTENDANCE
    assert rec.time_horizon == TimeHorizon.THIS_WEEK
    assert rec.evidence[0].current_value == 60.0
    assert rec.evidence[0].target_or_threshold == RecommendationPolicyConfig.ATTENDANCE_SAFE_TARGET


def test_attendance_rule_warning():
    rule = AttendanceRecommendationRule()
    raw_data = {"attendance_percentage": 70.0}
    explanation = DummyExplanation({"attendance_percentage": -0.35})
    sim_data = {
        "attendance": {
            "simulated_value": 80.0,
            "cgpa_delta": 0.45,
            "risk_score_delta": -18.0,
            "risk_transition": "HIGH → MEDIUM",
        }
    }
    rec = rule.evaluate(raw_data, None, None, explanation, sim_data)

    assert rec is not None
    assert rec.priority == RecommendationPriority.HIGH
    assert rec.expected_impact == ExpectedImpact.HIGH
    assert rec.source == RecommendationSource.COMBINED
    assert rec.evidence[0].simulated_value == 80.0
    assert rec.evidence[0].shap_contribution == -0.35


def test_attendance_rule_satisfied():
    rule = AttendanceRecommendationRule()
    raw_data = {"attendance_percentage": 88.0}
    rec = rule.evaluate(raw_data, None, None, None, None)
    assert rec is None


def test_backlog_rule_critical():
    rule = BacklogRecommendationRule()
    raw_data = {"backlogs": 3}
    rec = rule.evaluate(raw_data, None, None, None, None)

    assert rec is not None
    assert rec.priority == RecommendationPriority.CRITICAL
    assert rec.category == RecommendationCategory.BACKLOG_RECOVERY
    assert rec.evidence[0].current_value == 3
    assert rec.time_horizon == TimeHorizon.THIS_WEEK


def test_backlog_rule_zero_backlogs():
    rule = BacklogRecommendationRule()
    raw_data = {"backlogs": 0}
    rec = rule.evaluate(raw_data, None, None, None, None)
    assert rec is None


def test_midterm_rule_evaluation():
    rule = MidtermExamRecommendationRule()
    raw_data = {"mid_1": 40.0, "mid_2": 44.0}
    rec = rule.evaluate(raw_data, None, None, None, None)

    assert rec is not None
    assert rec.priority == RecommendationPriority.CRITICAL
    assert rec.category == RecommendationCategory.EXAM_PREPARATION
    assert rec.evidence[0].current_value == 42.0


def test_midterm_rule_high_scores():
    rule = MidtermExamRecommendationRule()
    raw_data = {"mid_1": 85.0, "mid_2": 90.0}
    rec = rule.evaluate(raw_data, None, None, None, None)
    assert rec is None


def test_internal_marks_rule():
    rule = InternalAssessmentRecommendationRule()
    raw_data = {"internal_marks": 48.0}
    rec = rule.evaluate(raw_data, None, None, None, None)

    assert rec is not None
    assert rec.priority == RecommendationPriority.HIGH
    assert rec.category == RecommendationCategory.INTERNAL_ASSESSMENT
    assert rec.evidence[0].current_value == 48.0


def test_trend_rule_negative():
    rule = AcademicTrendRecommendationRule()
    raw_data = {"previous_cgpa": 5.2}
    cgpa_pred = DummyCGPAPrediction(predicted_cgpa=5.0, trend=-0.8)
    rec = rule.evaluate(raw_data, cgpa_pred, None, None, None)

    assert rec is not None
    assert rec.priority == RecommendationPriority.HIGH
    assert rec.evidence[0].current_value == 5.2


def test_strength_maintenance_rule():
    rule = StrengthMaintenanceRule()
    raw_data = {"attendance_percentage": 92.0, "backlogs": 0, "previous_cgpa": 8.8}
    risk_pred = DummyRiskPrediction(risk_level="LOW", risk_score=10.0)
    rec = rule.evaluate(raw_data, None, risk_pred, None, None)

    assert rec is not None
    assert rec.priority == RecommendationPriority.LOW
    assert rec.category == RecommendationCategory.MAINTAIN_STRENGTH
    assert rec.time_horizon == TimeHorizon.LONGER_TERM
