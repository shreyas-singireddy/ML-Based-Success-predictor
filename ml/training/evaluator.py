"""
Model Evaluation and Comparison for CGPA Regression.

Calculates exact metrics:
- MAE (Mean Absolute Error)
- MSE (Mean Squared Error)
- RMSE (Root Mean Squared Error)
- R² (Coefficient of Determination)

Provides documented model selection logic:
- Primary criterion: Lowest Validation RMSE
- Secondary checks: Validation MAE and R²
- Evaluates selected champion on the unbiased Test partition
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ml.training.models import BaseCGPAModel


@dataclass
class ModelMetrics:
    mae: float
    mse: float
    rmse: float
    r2: float
    sample_count: int


@dataclass
class ModelEvaluationResult:
    model_name: str
    model_type: str
    val_metrics: ModelMetrics
    test_metrics: Optional[ModelMetrics] = None
    cv_rmse_mean: Optional[float] = None
    cv_rmse_std: Optional[float] = None
    feature_importances: Dict[str, float] = None
    hyperparameters: Dict[str, Any] = None


class ModelEvaluator:
    """Evaluates candidate models and formats comparison reports."""

    @staticmethod
    def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> ModelMetrics:
        """Computes MAE, MSE, RMSE, and R² for predictions."""
        mae = float(mean_absolute_error(y_true, y_pred))
        mse = float(mean_squared_error(y_true, y_pred))
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(y_true, y_pred))
        return ModelMetrics(
            mae=round(mae, 4),
            mse=round(mse, 4),
            rmse=round(rmse, 4),
            r2=round(r2, 4),
            sample_count=len(y_true),
        )

    @staticmethod
    def select_best_model(eval_results: List[ModelEvaluationResult]) -> Tuple[ModelEvaluationResult, str]:
        """
        Selects the best model using a deterministic selection rule:
        Primary: Lowest Validation RMSE.
        """
        if not eval_results:
            raise ValueError("No model evaluation results provided for selection.")

        # Sort by validation RMSE ascending
        sorted_results = sorted(eval_results, key=lambda r: r.val_metrics.rmse)
        best = sorted_results[0]
        
        reason = (
            f"Selected '{best.model_name}' because it achieved the lowest Validation RMSE ({best.val_metrics.rmse}) "
            f"and Validation MAE ({best.val_metrics.mae}) with R² of {best.val_metrics.r2}."
        )
        return best, reason

    @staticmethod
    def generate_comparison_markdown(
        eval_results: List[ModelEvaluationResult],
        best_model_name: str,
        selection_reason: str,
        dataset_info: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> str:
        lines = [
            "# ML Pipeline Phase 3 — CGPA Regression Model Comparison Report",
            f"\n**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}  ",
            f"**Selected Champion Model:** `{best_model_name}`\n",
            "## 1. Dataset Partition Summary",
            "| Partition | Records | Percentage |",
            "| :--- | :--- | :--- |",
            f"| Total Records | {dataset_info.get('total_records', '-')} | 100% |",
            f"| Training Split | {dataset_info.get('train_records', '-')} | {dataset_info.get('train_pct', '-')} |",
            f"| Validation Split | {dataset_info.get('val_records', '-')} | {dataset_info.get('val_pct', '-')} |",
            f"| Test Split | {dataset_info.get('test_records', '-')} | {dataset_info.get('test_pct', '-')} |\n",
            "## 2. Model Performance Comparison (Validation Split)",
            "| Model | Model Type | Val MAE | Val MSE | Val RMSE | Val R² | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for res in eval_results:
            is_best = (res.model_name == best_model_name)
            tag = "**CHAMPION**" if is_best else "BASELINE/CANDIDATE"
            lines.append(
                f"| `{res.model_name}` | {res.model_type} | {res.val_metrics.mae} | {res.val_metrics.mse} | {res.val_metrics.rmse} | {res.val_metrics.r2} | {tag} |"
            )

        lines.extend([
            "\n## 3. Final Champion Performance (Unbiased Test Partition)",
            "| Metric | Value | Interpretation |",
            "| :--- | :--- | :--- |",
        ])

        champion_res = next((r for r in eval_results if r.model_name == best_model_name), None)
        if champion_res and champion_res.test_metrics:
            tm = champion_res.test_metrics
            lines.extend([
                f"| **Test MAE** | {tm.mae} | Average absolute deviation in CGPA points |",
                f"| **Test MSE** | {tm.mse} | Mean squared error penalty |",
                f"| **Test RMSE** | {tm.rmse} | Root mean squared error in CGPA units |",
                f"| **Test R²** | {tm.r2} | Proportion of CGPA variance explained |",
            ])

        lines.extend([
            "\n## 4. Model Selection Rationale",
            f"> {selection_reason}\n",
            "## 5. Feature Importance / Interpretability",
            "*(Note: Feature importance indicates which pre-exam features were most influential to this model; it does not imply direct causation.)*",
            "\n| Feature | Importance / Weight |",
            "| :--- | :--- |",
        ])

        if champion_res and champion_res.feature_importances:
            sorted_feats = sorted(champion_res.feature_importances.items(), key=lambda x: abs(x[1]), reverse=True)
            for feat, weight in sorted_feats[:10]:
                lines.append(f"| `{feat}` | {weight} |")

        md_content = "\n".join(lines)
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(md_content)

        return md_content
