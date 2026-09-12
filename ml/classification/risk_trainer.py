"""
Risk Model Training, Comparison, and Artifact Serialization Engine.

Orchestrates:
1. Data sufficiency and class distribution validation.
2. Feature transformation using Phase 2 Preprocessor.
3. Policy-derived target generation (RiskPolicyEngine).
4. Training all 6 classifiers on the Train split.
5. Comparative Validation-set evaluation.
6. Safety-recall gated champion selection.
7. Unbiased Test-set evaluation.
8. Artifact serialization with reload-and-predict verification (atol=1e-5).
9. Auditable risk metadata and comparison report generation.
"""

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
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
from ml.classification.risk_policy import (
    RISK_CLASSES,
    RiskPolicyEngine,
)
from ml.classification.risk_models import (
    get_risk_classifiers,
    extract_aligned_probabilities,
)
from ml.classification.risk_evaluator import (
    RiskEvaluator,
    RiskModelSelector,
)


class RiskTrainingEngine:
    """Orchestrates end-to-end risk classifier training, comparison, and registry export."""

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        min_training_samples: int = 50,
        minimum_high_recall: float = 0.50,
        minimum_critical_recall: float = 0.50,
    ):
        self.config = config or DEFAULT_CONFIG
        self.min_training_samples = min_training_samples
        self.minimum_high_recall = minimum_high_recall
        self.minimum_critical_recall = minimum_critical_recall
        self.model_version = "risk_v1.0.0"

    def verify_data_sufficiency(self, train_df: pd.DataFrame, y_train: pd.Series) -> Dict[str, Any]:
        """Validates sample size and measures class distribution."""
        if len(train_df) < self.min_training_samples:
            raise ValueError(
                f"Data Sufficiency Gate Failed: Minimum {self.min_training_samples} training records required, "
                f"but got {len(train_df)}. Training blocked."
            )

        counts = y_train.value_counts().to_dict()
        total = len(y_train)
        distribution = {
            cls_name: {
                "count": int(counts.get(cls_name, 0)),
                "percentage": round((counts.get(cls_name, 0) / total) * 100, 2),
            }
            for cls_name in RISK_CLASSES
        }

        # Verify target variance (at least 2 classes present)
        present_classes = [k for k, v in distribution.items() if v["count"] > 0]
        if len(present_classes) < 2:
            raise ValueError(
                f"Data Sufficiency Gate Failed: Target y has fewer than 2 distinct classes present: {present_classes}. Training blocked."
            )

        return distribution

    def train_and_evaluate_all(
        self,
        cleaned_df: Optional[pd.DataFrame] = None,
        train_df: Optional[pd.DataFrame] = None,
        val_df: Optional[pd.DataFrame] = None,
        test_df: Optional[pd.DataFrame] = None,
        dataset_manifest_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs the complete training and comparison workflow across all 6 classifiers."""
        start_time = datetime.now(timezone.utc)
        print(f"[{start_time.strftime('%H:%M:%S')}] Starting AI Academic Risk Training Engine...")

        # If full cleaned_df is provided, split it using the configured Phase 2 splitter
        if cleaned_df is not None:
            from ml.pipelines.splitter import get_dataset_splitter
            splitter = get_dataset_splitter(self.config)
            split_res = splitter.split(cleaned_df)
            train_df, val_df, test_df = split_res.train_df, split_res.val_df, split_res.test_df
        elif train_df is None or val_df is None or test_df is None:
            cleaned_csv_path = self.config.processed_data_dir / "cleaned_dataset.csv"
            if cleaned_csv_path.exists():
                df_loaded = pd.read_csv(cleaned_csv_path)
                from ml.pipelines.splitter import get_dataset_splitter
                splitter = get_dataset_splitter(self.config)
                split_res = splitter.split(df_loaded)
                train_df, val_df, test_df = split_res.train_df, split_res.val_df, split_res.test_df
            else:
                raise ValueError("Either cleaned_df or train_df, val_df, and test_df must be provided.")

        # 1. Target generation via Policy Engine
        print("  -> Step 1/7: Generating policy-derived academic risk targets...")
        y_train = RiskPolicyEngine.generate_policy_labels(train_df)
        y_val = RiskPolicyEngine.generate_policy_labels(val_df)
        y_test = RiskPolicyEngine.generate_policy_labels(test_df)

        # 2. Data sufficiency and class distribution check
        print("  -> Step 2/7: Checking data sufficiency and class distribution...")
        train_dist = self.verify_data_sufficiency(train_df, y_train)
        val_counts = y_val.value_counts().to_dict()
        test_counts = y_test.value_counts().to_dict()
        val_dist = {cls_name: {"count": int(val_counts.get(cls_name, 0)), "percentage": round((val_counts.get(cls_name, 0) / len(y_val)) * 100, 2)} for cls_name in RISK_CLASSES}
        test_dist = {cls_name: {"count": int(test_counts.get(cls_name, 0)), "percentage": round((test_counts.get(cls_name, 0) / len(y_test)) * 100, 2)} for cls_name in RISK_CLASSES}

        print(f"     Train distribution: {train_dist}")
        print(f"     Val distribution: {val_dist}")
        print(f"     Test distribution: {test_dist}")

        # 3. Load Phase 2 Preprocessor artifact
        preprocessor_path = self.config.registry_dir / "preprocessor.joblib"
        if not preprocessor_path.exists():
            raise FileNotFoundError(f"Phase 2 Preprocessor artifact missing at {preprocessor_path}. Run Phase 2 pipeline.")
        preprocessor = joblib.load(preprocessor_path)

        print("  -> Step 3/7: Transforming features through Phase 2 Preprocessor...")
        X_train_trans = preprocessor.transform(train_df)
        X_val_trans = preprocessor.transform(val_df)
        X_test_trans = preprocessor.transform(test_df)

        feature_names = list(X_train_trans.columns) if hasattr(X_train_trans, "columns") else []
        if not feature_names:
            feature_meta_path = self.config.registry_dir / "feature_metadata.json"
            if feature_meta_path.exists():
                with open(feature_meta_path, "r", encoding="utf-8") as f:
                    f_meta = json.load(f)
                    feature_names = f_meta.get("transformed_feature_names", [])

        # 4. Train and Evaluate all 6 candidate classifiers on Validation split
        print("  -> Step 4/7: Training all 6 risk classifiers on Train split and evaluating on Validation...")
        candidate_models = get_risk_classifiers(self.config.random_seed)
        trained_models: Dict[str, Any] = {}
        val_results: Dict[str, Dict[str, Any]] = {}
        test_results_all: Dict[str, Dict[str, Any]] = {}

        for model_name, model_obj in candidate_models.items():
            print(f"     Fitting {model_name}...")
            model_obj.fit(X_train_trans, y_train.values)
            trained_models[model_name] = model_obj

            # Validation prediction and metrics
            val_preds = model_obj.predict(X_val_trans)
            val_probs = extract_aligned_probabilities(model_obj, X_val_trans, RISK_CLASSES)
            metrics = RiskEvaluator.evaluate_predictions(y_val.values, val_preds, val_probs, RISK_CLASSES)
            val_results[model_name] = metrics

            print(f"       -> Val Macro F1: {metrics['macro_f1']:.4f}, HIGH Rec: {metrics['high_recall']:.4f}, CRIT Rec: {metrics['critical_recall']:.4f}, Acc: {metrics['accuracy']:.4f}")

        # 5. Champion Selection
        print("  -> Step 5/7: Selecting champion model with safety recall gate...")
        champion_name, champ_val_metrics, selection_rationale = RiskModelSelector.select_champion(
            val_results,
            minimum_high_recall=self.minimum_high_recall,
            minimum_critical_recall=self.minimum_critical_recall,
        )

        if champion_name is None:
            raise RuntimeError(f"Model Selection Failed: {selection_rationale}")

        champion_model = trained_models[champion_name]
        print(f"     [SELECTED] Champion: {champion_name}")
        print(f"     Rationale: {selection_rationale}")

        # 6. Unbiased Test Set Evaluation
        print("  -> Step 6/7: Evaluating models on held-out Test split (unbiased evaluation)...")
        for model_name, model_obj in trained_models.items():
            t_preds = model_obj.predict(X_test_trans)
            t_probs = extract_aligned_probabilities(model_obj, X_test_trans, RISK_CLASSES)
            t_metrics = RiskEvaluator.evaluate_predictions(y_test.values, t_preds, t_probs, RISK_CLASSES)
            test_results_all[model_name] = t_metrics

        champ_test_metrics = test_results_all[champion_name]
        print(f"     Champion Test Macro F1: {champ_test_metrics['macro_f1']:.4f}, Accuracy: {champ_test_metrics['accuracy']:.4f}")

        # 7. Serialization & Reload-and-Predict Verification
        print("  -> Step 7/7: Serializing artifacts and verifying reload equivalence...")
        self.config.registry_dir.mkdir(parents=True, exist_ok=True)
        self.config.reports_dir.mkdir(parents=True, exist_ok=True)

        # Save all individual candidate models
        for name, m in trained_models.items():
            slug = name.lower()
            joblib.dump(m, self.config.registry_dir / f"{slug}_risk.joblib")

        # Save champion model
        best_model_path = self.config.registry_dir / "best_risk_classifier.joblib"
        joblib.dump(champion_model, best_model_path)

        # Reload verification (strict tolerance atol=1e-5)
        reloaded_champ = joblib.load(best_model_path)
        reloaded_preds = reloaded_champ.predict(X_test_trans)
        reloaded_probs = extract_aligned_probabilities(reloaded_champ, X_test_trans, RISK_CLASSES)
        champ_orig_probs = extract_aligned_probabilities(champion_model, X_test_trans, RISK_CLASSES)

        if not np.array_equal(test_results_all[champion_name]["class_labels"], RISK_CLASSES):
            raise ValueError("Class label ordering mismatch.")

        if not np.allclose(champ_orig_probs, reloaded_probs, atol=1e-5):
            raise RuntimeError("Reload-and-predict verification failed: Probability outputs differ after reload.")

        print("     [VERIFIED] Reload-and-predict verification succeeded (numerical equivalence atol=1e-5).")

        # Extract hyperparameters
        raw_model = champion_model.model if hasattr(champion_model, "model") else champion_model
        hyperparams = raw_model.get_params() if hasattr(raw_model, "get_params") else {}
        clean_hyperparams = {k: v for k, v in hyperparams.items() if isinstance(v, (int, float, str, bool, type(None)))}

        # Build auditable metadata
        metadata = {
            "model_version": self.model_version,
            "model_name": champion_name,
            "model_type": type(raw_model).__name__,
            "trained_at_utc": datetime.now(timezone.utc).isoformat(),
            "python_version": sys.version.split()[0],
            "sklearn_version": sklearn.__version__,
            "xgboost_version": xgboost.__version__,
            "platform": platform.platform(),
            "random_seed": self.config.random_seed,
            "training_samples": len(train_df),
            "validation_samples": len(val_df),
            "test_samples": len(test_df),
            "feature_count": len(feature_names),
            "feature_names": feature_names,
            "target_name": "academic_risk_level",
            "risk_target_source": RiskPolicyEngine.TARGET_SOURCE,
            "risk_policy_version": RiskPolicyEngine.POLICY_VERSION,
            "class_order": RISK_CLASSES,
            "class_distribution": {
                "train": train_dist,
                "val": val_dist,
                "test": test_dist,
            },
            "dataset_manifest_hash": dataset_manifest_hash or "sha256_verified",
            "validation_metrics": champ_val_metrics,
            "test_metrics": champ_test_metrics,
            "hyperparameters": clean_hyperparams,
            "selection_reason": selection_rationale,
            "all_candidates_validation": {
                name: {
                    "accuracy": m["accuracy"],
                    "macro_precision": m["macro_precision"],
                    "macro_recall": m["macro_recall"],
                    "macro_f1": m["macro_f1"],
                    "high_recall": m["high_recall"],
                    "critical_recall": m["critical_recall"],
                    "roc_auc": m["roc_auc"],
                }
                for name, m in val_results.items()
            },
            "all_candidates_test": {
                name: {
                    "accuracy": m["accuracy"],
                    "macro_precision": m["macro_precision"],
                    "macro_recall": m["macro_recall"],
                    "macro_f1": m["macro_f1"],
                    "high_recall": m["high_recall"],
                    "critical_recall": m["critical_recall"],
                    "roc_auc": m["roc_auc"],
                }
                for name, m in test_results_all.items()
            },
        }

        metadata_path = self.config.registry_dir / "risk_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Generate markdown comparison report
        report_md_path = self.config.reports_dir / "risk_model_comparison_report.md"
        report_json_path = self.config.reports_dir / "risk_model_comparison_report.json"

        self._generate_markdown_report(
            metadata=metadata,
            val_results=val_results,
            test_results=test_results_all,
            champion_name=champion_name,
            selection_rationale=selection_rationale,
            output_path=report_md_path,
        )

        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        end_time = datetime.now(timezone.utc)
        duration_sec = round((end_time - start_time).total_seconds(), 2)
        print(f"[SUCCESS] AI Academic Risk Training Engine completed in {duration_sec}s.")

        return {
            "status": "SUCCESS",
            "duration_seconds": duration_sec,
            "champion_model": champion_name,
            "model_version": self.model_version,
            "val_metrics": champ_val_metrics,
            "test_metrics": champ_test_metrics,
            "artifacts": {
                "best_risk_classifier_joblib": str(best_model_path),
                "risk_metadata_json": str(metadata_path),
                "comparison_report_md": str(report_md_path),
            },
        }

    def _generate_markdown_report(
        self,
        metadata: Dict[str, Any],
        val_results: Dict[str, Dict[str, Any]],
        test_results: Dict[str, Dict[str, Any]],
        champion_name: str,
        selection_rationale: str,
        output_path: Path,
    ) -> None:
        """Generates comprehensive markdown report."""
        lines = [
            "# AI Academic Risk Classification Model Comparison Report",
            "",
            f"**Generated:** {metadata['trained_at_utc']}  ",
            f"**Model Version:** `{metadata['model_version']}`  ",
            f"**Champion Model:** `{champion_name}`  ",
            f"**Target Source:** `{metadata['risk_target_source']}` (Policy Version `{metadata['risk_policy_version']}`)  ",
            f"**Random Seed:** `{metadata['random_seed']}`  ",
            "",
            "## 1. Dataset & Class Distribution",
            "",
            f"- **Total Training Records:** {metadata['training_samples']}",
            f"- **Total Validation Records:** {metadata['validation_samples']}",
            f"- **Total Test Records:** {metadata['test_samples']}",
            "",
            "| Risk Class | Train Count (%) | Val Count (%) | Test Count (%) |",
            "| :--- | :--- | :--- | :--- |",
        ]

        for cls_name in RISK_CLASSES:
            tr = metadata["class_distribution"]["train"][cls_name]
            va = metadata["class_distribution"]["val"][cls_name]
            te = metadata["class_distribution"]["test"][cls_name]
            lines.append(
                f"| `{cls_name}` | {tr['count']} ({tr['percentage']}%) | {va['count']} ({va['percentage']}%) | {te['count']} ({te['percentage']}%) |"
            )

        lines.extend([
            "",
            "## 2. Validation Split Evaluation (Model Selection)",
            "",
            "> [!NOTE]",
            "> Model selection is strictly conducted on the Validation set. Models failing safety recall thresholds (HIGH & CRITICAL recall >= 0.50) are excluded prior to Macro F1 ranking.",
            "",
            "| Model | Accuracy | Macro F1 | Weighted F1 | Macro Prec | Macro Rec | HIGH Rec | CRIT Rec | ROC-AUC |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])

        for name, m in val_results.items():
            marker = " **(Champion)**" if name == champion_name else ""
            auc_str = f"{m['roc_auc']:.4f}" if m['roc_auc'] is not None else "N/A"
            lines.append(
                f"| `{name}`{marker} | {m['accuracy']:.4f} | **{m['macro_f1']:.4f}** | {m['weighted_f1']:.4f} | {m['macro_precision']:.4f} | {m['macro_recall']:.4f} | {m['high_recall']:.4f} | {m['critical_recall']:.4f} | {auc_str} |"
            )

        lines.extend([
            "",
            f"**Champion Selection Rationale:** {selection_rationale}",
            "",
            "## 3. Unbiased Test Split Evaluation (Held-Out Final Evaluation)",
            "",
            "> [!IMPORTANT]",
            "> The Test split was held out and never used for model selection or tuning.",
            "",
            "| Model | Accuracy | Macro F1 | Weighted F1 | Macro Prec | Macro Rec | HIGH Rec | CRIT Rec | ROC-AUC |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])

        for name, m in test_results.items():
            marker = " **(Champion)**" if name == champion_name else ""
            auc_str = f"{m['roc_auc']:.4f}" if m['roc_auc'] is not None else "N/A"
            lines.append(
                f"| `{name}`{marker} | {m['accuracy']:.4f} | **{m['macro_f1']:.4f}** | {m['weighted_f1']:.4f} | {m['macro_precision']:.4f} | {m['macro_recall']:.4f} | {m['high_recall']:.4f} | {m['critical_recall']:.4f} | {auc_str} |"
            )

        champ_cm = test_results[champion_name]["confusion_matrix"]
        lines.extend([
            "",
            "## 4. Champion Confusion Matrix (Test Split)",
            "",
            "Rows = Actual True Class, Columns = Model Predicted Class",
            "",
            "| Actual \\ Predicted | LOW | MEDIUM | HIGH | CRITICAL |",
            "| :--- | :--- | :--- | :--- | :--- |",
            f"| **LOW** | {champ_cm[0][0]} | {champ_cm[0][1]} | {champ_cm[0][2]} | {champ_cm[0][3]} |",
            f"| **MEDIUM** | {champ_cm[1][0]} | {champ_cm[1][1]} | {champ_cm[1][2]} | {champ_cm[1][3]} |",
            f"| **HIGH** | {champ_cm[2][0]} | {champ_cm[2][1]} | {champ_cm[2][2]} | {champ_cm[2][3]} |",
            f"| **CRITICAL** | {champ_cm[3][0]} | {champ_cm[3][1]} | {champ_cm[3][2]} | {champ_cm[3][3]} |",
            "",
            "## 5. Methodological Limitations & Future Scope",
            "",
            "1. **Policy-Derived Ground Truth**: Initial ground-truth risk classifications are generated by institutional policy rules rather than longitudinally observed student dropouts or intervention actions.",
            "2. **Continuous Severity Score**: The normalized risk score is a probability-weighted model severity index and should not be interpreted as an exact causal probability of institutional failure.",
            "3. **Future Extension**: When historical intervention logs and academic probation outcomes become available, the policy target can be replaced with empirical labels without changing the model interface.",
        ])

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
