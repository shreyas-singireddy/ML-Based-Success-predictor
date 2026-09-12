"""
Unit Tests for Risk Model Selection, Safety Recall Gating, and Evaluator.
"""

import pytest
import numpy as np
from ml.classification.risk_evaluator import RiskEvaluator, RiskModelSelector


def test_evaluator_metrics_and_confusion_matrix():
    """Verifies that RiskEvaluator correctly computes multiclass metrics, safety recalls, and 4x4 matrix."""
    y_true = np.array(["LOW", "MEDIUM", "HIGH", "CRITICAL", "HIGH", "CRITICAL"])
    y_pred = np.array(["LOW", "MEDIUM", "HIGH", "HIGH", "HIGH", "CRITICAL"])  # One CRITICAL misclassified as HIGH
    y_prob = np.array([
        [0.8, 0.1, 0.1, 0.0],
        [0.1, 0.7, 0.1, 0.1],
        [0.0, 0.1, 0.8, 0.1],
        [0.0, 0.1, 0.6, 0.3],
        [0.1, 0.1, 0.7, 0.1],
        [0.0, 0.0, 0.2, 0.8],
    ])

    metrics = RiskEvaluator.evaluate_predictions(y_true, y_pred, y_prob)

    assert "accuracy" in metrics
    assert "macro_f1" in metrics
    assert "high_recall" in metrics
    assert "critical_recall" in metrics
    assert "high_critical_combined_recall" in metrics
    assert "confusion_matrix" in metrics
    assert len(metrics["confusion_matrix"]) == 4
    assert len(metrics["confusion_matrix"][0]) == 4

    # High recall: 2 actual HIGH, both predicted HIGH -> 1.0
    assert metrics["high_recall"] == 1.0
    # Critical recall: 2 actual CRITICAL, 1 predicted CRITICAL -> 0.5
    assert metrics["critical_recall"] == 0.5
    # Combined: 4 actual HIGH/CRITICAL, all 4 predicted HIGH or CRITICAL -> 1.0
    assert metrics["high_critical_combined_recall"] == 1.0


def test_champion_selection_safety_recall_gate():
    """Verifies safety recall gating: models with HIGH or CRITICAL recall below threshold are excluded."""
    results = {
        "HighF1_Unsafe": {
            "macro_f1": 0.95,
            "high_recall": 0.40,  # Fails safety gate (< 0.50)
            "critical_recall": 0.90,
            "high_critical_combined_recall": 0.65,
            "macro_recall": 0.70,
            "weighted_f1": 0.95,
        },
        "Safe_Champion": {
            "macro_f1": 0.90,
            "high_recall": 0.85,  # Passes safety gate (>= 0.50)
            "critical_recall": 0.85,
            "high_critical_combined_recall": 0.85,
            "macro_recall": 0.90,
            "weighted_f1": 0.90,
        },
    }

    champ, m, rationale = RiskModelSelector.select_champion(
        results,
        minimum_high_recall=0.50,
        minimum_critical_recall=0.50,
    )

    assert champ == "Safe_Champion"
    assert "HighF1_Unsafe" not in champ


def test_no_safe_champion_state():
    """Verifies that if all models fail the safety gate, NO_SAFE_CHAMPION is returned."""
    results = {
        "ModelA": {"macro_f1": 0.90, "high_recall": 0.30, "critical_recall": 0.30},
        "ModelB": {"macro_f1": 0.85, "high_recall": 0.40, "critical_recall": 0.20},
    }

    champ, m, rationale = RiskModelSelector.select_champion(
        results,
        minimum_high_recall=0.50,
        minimum_critical_recall=0.50,
    )

    assert champ is None
    assert "NO_SAFE_CHAMPION" in rationale
