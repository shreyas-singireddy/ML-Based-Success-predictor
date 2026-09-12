"""
Tests for Model Training, Evaluation Metrics, and Quality Gates.
"""

import numpy as np
import pandas as pd
import pytest

from ml.config.pipeline_config import PROCESSED_DATA_DIR
from ml.training.evaluator import ModelEvaluator
from ml.training.models import get_candidate_models
from ml.training.trainer import ModelTrainingEngine


@pytest.fixture
def processed_datasets():
    train_path = PROCESSED_DATA_DIR / "train.csv"
    val_path = PROCESSED_DATA_DIR / "val.csv"
    test_path = PROCESSED_DATA_DIR / "test.csv"

    if not train_path.exists() or not val_path.exists() or not test_path.exists():
        pytest.skip("Phase 2 processed datasets not found. Run Phase 2 pipeline first.")

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    target_col = "target_cgpa"
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]

    X_val = val_df.drop(columns=[target_col])
    y_val = val_df[target_col]

    X_test = test_df.drop(columns=[target_col])
    y_test = test_df[target_col]

    return X_train, y_train, X_val, y_val, X_test, y_test


def test_data_sufficiency_gate():
    trainer = ModelTrainingEngine()
    
    # Fail on < 50 rows
    small_X = pd.DataFrame({"feat1": np.random.randn(20)})
    small_y = pd.Series(np.random.uniform(5.0, 9.0, 20))
    with pytest.raises(ValueError, match="Data Sufficiency Gate Failed"):
        trainer.verify_data_sufficiency(small_X, small_y)

    # Fail on zero variance target
    const_X = pd.DataFrame({"feat1": np.random.randn(60)})
    const_y = pd.Series([7.5] * 60)
    with pytest.raises(ValueError, match="zero variance"):
        trainer.verify_data_sufficiency(const_X, const_y)


def test_all_three_models_train_and_metrics_valid(processed_datasets):
    X_train, y_train, X_val, y_val, X_test, y_test = processed_datasets
    candidate_models = get_candidate_models(random_seed=42)

    assert len(candidate_models) == 3
    model_names = [m.name for m in candidate_models]
    assert "LinearRegression" in model_names
    assert "RandomForestRegressor" in model_names
    assert "XGBRegressor" in model_names

    for model_obj in candidate_models:
        model_obj.fit(X_train.values, y_train.values, feature_names=list(X_train.columns))
        assert model_obj.is_fitted is True

        preds = model_obj.predict(X_val.values)
        assert len(preds) == len(y_val)
        assert np.all(preds >= 0.0) and np.all(preds <= 10.0)
        assert np.all(np.isfinite(preds))

        metrics = ModelEvaluator.compute_metrics(y_val.values, preds)
        # Verify MAE, MSE, RMSE are positive and finite
        assert metrics.mae >= 0.0
        assert metrics.mse >= 0.0
        assert metrics.rmse >= 0.0
        # R^2 mathematically must be <= 1.0 (allowed to be negative)
        assert metrics.r2 <= 1.0
        assert np.isfinite(metrics.r2)


def test_training_engine_full_workflow(processed_datasets, tmp_path):
    X_train, y_train, X_val, y_val, X_test, y_test = processed_datasets
    
    from ml.config.pipeline_config import PipelineConfig
    test_config = PipelineConfig(
        registry_dir=tmp_path / "registry",
        reports_dir=tmp_path / "reports",
    )

    trainer = ModelTrainingEngine(config=test_config)
    result = trainer.train_and_evaluate_all(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
    )

    assert result["status"] == "SUCCESS"
    assert result["champion_model"] in ["LinearRegression", "RandomForestRegressor", "XGBRegressor"]
    assert (tmp_path / "registry" / "best_model.joblib").exists()
    assert (tmp_path / "registry" / "model_metadata.json").exists()
    assert (tmp_path / "reports" / "model_comparison_report.md").exists()
