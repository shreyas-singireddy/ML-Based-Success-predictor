"""
Tests for Model Selection and Comparison Logic.
"""

import pytest
from ml.training.evaluator import ModelEvaluator, ModelEvaluationResult, ModelMetrics


def test_select_best_model_lowest_rmse():
    res1 = ModelEvaluationResult(
        model_name="Model_A",
        model_type="linear",
        val_metrics=ModelMetrics(mae=0.30, mse=0.10, rmse=0.316, r2=0.85, sample_count=100),
    )
    res2 = ModelEvaluationResult(
        model_name="Model_B",
        model_type="tree",
        val_metrics=ModelMetrics(mae=0.20, mse=0.05, rmse=0.223, r2=0.92, sample_count=100),
    )
    res3 = ModelEvaluationResult(
        model_name="Model_C",
        model_type="boosting",
        val_metrics=ModelMetrics(mae=0.25, mse=0.07, rmse=0.264, r2=0.89, sample_count=100),
    )

    best, reason = ModelEvaluator.select_best_model([res1, res2, res3])
    assert best.model_name == "Model_B"
    assert "0.223" in reason


def test_model_comparison_markdown_generation():
    res = ModelEvaluationResult(
        model_name="Model_B",
        model_type="tree",
        val_metrics=ModelMetrics(mae=0.20, mse=0.05, rmse=0.223, r2=0.92, sample_count=100),
        test_metrics=ModelMetrics(mae=0.22, mse=0.06, rmse=0.245, r2=0.90, sample_count=100),
        feature_importances={"attendance": 0.45, "mid_1": 0.35},
    )

    md = ModelEvaluator.generate_comparison_markdown(
        eval_results=[res],
        best_model_name="Model_B",
        selection_reason="Lowest RMSE",
        dataset_info={"total_records": 300},
    )

    assert "# ML Pipeline Phase 3" in md
    assert "Model_B" in md
    assert "0.223" in md
    assert "0.245" in md
