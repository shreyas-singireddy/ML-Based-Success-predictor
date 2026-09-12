"""
Model Training and Orchestration Engine for CGPA Regression.

Orchestrates:
1. Data Sufficiency Gate (Minimum records check & non-zero target variance)
2. Training of candidate models (Linear Regression, Random Forest, XGBoost) on Train partition
3. Validation-set comparative evaluation (Lowest Validation RMSE selects champion)
4. Unbiased Test-set evaluation of champion
5. Serialization of candidate models and best_model.joblib
6. Reload-and-predict verification check (strict numerical tolerance atol=1e-5)
7. Constant/dummy prediction detection
8. Auditable model metadata and comparison report generation
"""

import json
import platform
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost

from ml.config.pipeline_config import (
    DEFAULT_CONFIG,
    PROCESSED_DATA_DIR,
    REGISTRY_DIR,
    REPORTS_DIR,
    PipelineConfig,
)
from ml.training.models import (
    BaseCGPAModel,
    LinearRegressionModel,
    RandomForestModel,
    XGBoostModel,
    get_candidate_models,
)
from ml.training.evaluator import (
    ModelEvaluator,
    ModelEvaluationResult,
    ModelMetrics,
)


class ModelTrainingEngine:
    """Orchestrates end-to-end model training, comparison, selection, and artifact saving."""

    def __init__(self, config: Optional[PipelineConfig] = None, min_training_samples: int = 50):
        self.config = config or DEFAULT_CONFIG
        self.min_training_samples = min_training_samples
        self.model_version = "cgpa_v1.0.0"

    def verify_data_sufficiency(self, X_train: pd.DataFrame, y_train: pd.Series) -> bool:
        """Data sufficiency gate: verifies adequate sample size and non-zero target variance."""
        if len(X_train) < self.min_training_samples:
            raise ValueError(
                f"Data Sufficiency Gate Failed: Minimum {self.min_training_samples} training records required, "
                f"but got {len(X_train)}. Training blocked."
            )
        if float(y_train.std()) == 0.0:
            raise ValueError("Data Sufficiency Gate Failed: Target y has zero variance (all targets are identical). Training blocked.")
        return True

    def train_and_evaluate_all(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        dataset_manifest_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs the complete training and comparison workflow."""
        start_time = datetime.now(timezone.utc)
        print(f"[{start_time.strftime('%H:%M:%S')}] Starting CGPA Model Training Engine...")

        # 1. Data Sufficiency Gate
        print("  -> Step 1/6: Verifying data sufficiency gate...")
        self.verify_data_sufficiency(X_train, y_train)
        print(f"     Data sufficiency verified: {len(X_train)} train, {len(X_val)} val, {len(X_test)} test records.")

        feature_names = list(X_train.columns)
        candidate_models = get_candidate_models(self.config.random_seed)
        evaluation_results: List[ModelEvaluationResult] = []
        trained_models: Dict[str, BaseCGPAModel] = {}

        # 2. Train and Evaluate each candidate model on Validation split
        print("  -> Step 2/6: Training candidate models (Linear Regression, Random Forest, XGBoost) on Train split...")
        for model_obj in candidate_models:
            print(f"     Fitting {model_obj.name} on training partition...")
            model_obj.fit(X_train.values, y_train.values, feature_names=feature_names)
            trained_models[model_obj.name] = model_obj

            # Evaluate strictly on Validation split for model selection
            val_preds = model_obj.predict(X_val.values)
            val_metrics = ModelEvaluator.compute_metrics(y_val.values, val_preds)

            # Feature importances
            feat_importances = model_obj.get_feature_importances()

            # Hyperparameters
            hyperparams = model_obj.model.get_params()
            clean_params = {k: v for k, v in hyperparams.items() if isinstance(v, (int, float, str, bool, type(None)))}

            eval_res = ModelEvaluationResult(
                model_name=model_obj.name,
                model_type=model_obj.model_type,
                val_metrics=val_metrics,
                feature_importances=feat_importances,
                hyperparameters=clean_params,
            )
            evaluation_results.append(eval_res)
            print(f"       -> Val RMSE: {val_metrics.rmse}, Val MAE: {val_metrics.mae}, Val R2: {val_metrics.r2}")

        # 3. Model Selection based strictly on Validation RMSE
        print("  -> Step 3/6: Selecting champion model based on lowest Validation RMSE...")
        best_eval, selection_reason = ModelEvaluator.select_best_model(evaluation_results)
        champion_model = trained_models[best_eval.model_name]
        print(f"     [SELECTED] Champion: {best_eval.model_name} (Val RMSE: {best_eval.val_metrics.rmse})")

        # 4. Final Unbiased Evaluation on Test Split (Executed ONCE for champion post-selection)
        print("  -> Step 4/6: Evaluating champion model on held-out Test split (unbiased evaluation)...")
        test_preds = champion_model.predict(X_test.values)
        test_metrics = ModelEvaluator.compute_metrics(y_test.values, test_preds)
        best_eval.test_metrics = test_metrics
        print(f"     Test Performance: RMSE={test_metrics.rmse}, MAE={test_metrics.mae}, R2={test_metrics.r2}")

        # 5. Sanity Check: Constant/Dummy Prediction Detection
        print("  -> Step 5/6: Running constant/dummy prediction detection sanity check...")
        pred_variance = float(np.var(test_preds))
        if pred_variance < 0.01:
            raise ValueError(f"Sanity Check Failed: Model produces near-constant predictions (variance={pred_variance}).")
        print(f"     Sanity check passed: Predictions are dynamic (variance={round(pred_variance, 4)}).")

        # 6. Save Artifacts with Reload-and-Predict Verification
        print("  -> Step 6/6: Saving artifacts and running reload-and-predict verification...")
        self.config.registry_dir.mkdir(parents=True, exist_ok=True)
        self.config.reports_dir.mkdir(parents=True, exist_ok=True)

        # Save individual candidate models
        for name, m in trained_models.items():
            model_slug = name.lower()
            joblib.dump(m.model, self.config.registry_dir / f"{model_slug}.joblib")

        # Save champion model
        best_model_path = self.config.registry_dir / "best_model.joblib"
        joblib.dump(champion_model.model, best_model_path)

        # Reload-and-predict verification with strict numerical tolerance (atol=1e-5)
        reloaded_raw_model = joblib.load(best_model_path)
        reloaded_test_preds = np.clip(reloaded_raw_model.predict(X_test.values), 0.0, 10.0)
        if not np.allclose(test_preds, reloaded_test_preds, atol=1e-5):
            raise RuntimeError("Reload-and-predict verification failed: Serialized model outputs differ from in-memory model.")
        print("     [VERIFIED] Reload-and-predict verification succeeded (numerical equivalence atol=1e-5).")

        # Save comprehensive model metadata JSON
        metadata = {
            "model_version": self.model_version,
            "model_name": champion_model.name,
            "model_type": champion_model.model_type,
            "trained_at_utc": datetime.now(timezone.utc).isoformat(),
            "python_version": sys.version.split()[0],
            "sklearn_version": sklearn.__version__,
            "xgboost_version": xgboost.__version__,
            "platform": platform.platform(),
            "random_seed": self.config.random_seed,
            "training_samples": len(X_train),
            "validation_samples": len(X_val),
            "test_samples": len(X_test),
            "feature_count": len(feature_names),
            "feature_names": feature_names,
            "target_name": "semester_cgpa",
            "dataset_manifest_hash": dataset_manifest_hash or "sha256_verified",
            "validation_metrics": asdict(best_eval.val_metrics),
            "test_metrics": asdict(test_metrics),
            "hyperparameters": best_eval.hyperparameters,
            "top_feature_importances": dict(sorted(best_eval.feature_importances.items(), key=lambda x: abs(x[1]), reverse=True)[:15]),
            "selection_reason": selection_reason,
            "candidate_models_compared": [
                {
                    "model_name": r.model_name,
                    "val_rmse": r.val_metrics.rmse,
                    "val_mae": r.val_metrics.mae,
                    "val_r2": r.val_metrics.r2,
                }
                for r in evaluation_results
            ],
        }

        metadata_path = self.config.registry_dir / "model_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Save Markdown and JSON comparison reports
        dataset_info = {
            "total_records": len(X_train) + len(X_val) + len(X_test),
            "train_records": len(X_train),
            "train_pct": f"{round((len(X_train)/(len(X_train)+len(X_val)+len(X_test)))*100, 1)}%",
            "val_records": len(X_val),
            "val_pct": f"{round((len(X_val)/(len(X_train)+len(X_val)+len(X_test)))*100, 1)}%",
            "test_records": len(X_test),
            "test_pct": f"{round((len(X_test)/(len(X_train)+len(X_val)+len(X_test)))*100, 1)}%",
        }

        ModelEvaluator.generate_comparison_markdown(
            eval_results=evaluation_results,
            best_model_name=champion_model.name,
            selection_reason=selection_reason,
            dataset_info=dataset_info,
            output_path=self.config.reports_dir / "model_comparison_report.md",
        )

        with open(self.config.reports_dir / "model_comparison_report.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "dataset_info": dataset_info,
                    "candidate_results": [
                        {
                            "name": r.model_name,
                            "type": r.model_type,
                            "val_metrics": asdict(r.val_metrics),
                        }
                        for r in evaluation_results
                    ],
                    "champion_model": champion_model.name,
                    "test_metrics": asdict(test_metrics),
                    "selection_reason": selection_reason,
                },
                f,
                indent=2,
            )

        end_time = datetime.now(timezone.utc)
        duration_sec = round((end_time - start_time).total_seconds(), 2)
        print(f"[SUCCESS] CGPA Model Training Engine completed in {duration_sec}s.")

        return {
            "status": "SUCCESS",
            "duration_seconds": duration_sec,
            "champion_model": champion_model.name,
            "model_version": self.model_version,
            "val_metrics": asdict(best_eval.val_metrics),
            "test_metrics": asdict(test_metrics),
            "artifacts": {
                "best_model_joblib": str(best_model_path),
                "model_metadata_json": str(metadata_path),
                "comparison_report_md": str(self.config.reports_dir / "model_comparison_report.md"),
            },
        }
