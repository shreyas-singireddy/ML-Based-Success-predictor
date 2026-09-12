"""
Multiclass Evaluation and Safety-Gated Champion Selection for Academic Risk Classifiers.

Calculates:
- Accuracy
- Macro Precision & Weighted Precision
- Macro Recall & Weighted Recall
- Macro F1 & Weighted F1
- High Risk Recall & Critical Risk Recall
- High/Critical Combined Recall
- 4x4 Confusion Matrix with explicit class ordering ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
- Multiclass OvR ROC-AUC (with graceful None handling for missing classes)

Champion Selection:
- Enforces configurable safety recall gates on HIGH and CRITICAL risk classes.
- Ranks surviving models by Validation Macro F1.
- Deterministic tie-breaking without ever inspecting Test set metrics.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
)

from ml.classification.risk_policy import RISK_CLASSES


# Simplicity ranking for tie-breaking: lower number = simpler model
MODEL_SIMPLICITY_ORDER: Dict[str, int] = {
    "DecisionTreeClassifier": 1,
    "LogisticRegression": 2,
    "RandomForestClassifier": 3,
    "SVC": 4,
    "XGBClassifier": 5,
    "MLPClassifier": 6,
}


class RiskEvaluator:
    """Calculates comprehensive multiclass classification metrics with early-warning safety metrics."""

    @staticmethod
    def evaluate_predictions(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Optional[np.ndarray] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Computes standard and safety-focused multiclass classification metrics.
        """
        class_labels = labels or RISK_CLASSES
        y_true_arr = np.array(y_true)
        y_pred_arr = np.array(y_pred)

        # Standard metrics
        acc = float(accuracy_score(y_true_arr, y_pred_arr))
        macro_prec = float(precision_score(y_true_arr, y_pred_arr, labels=class_labels, average="macro", zero_division=0))
        weighted_prec = float(precision_score(y_true_arr, y_pred_arr, labels=class_labels, average="weighted", zero_division=0))
        macro_rec = float(recall_score(y_true_arr, y_pred_arr, labels=class_labels, average="macro", zero_division=0))
        weighted_rec = float(recall_score(y_true_arr, y_pred_arr, labels=class_labels, average="weighted", zero_division=0))
        macro_f1 = float(f1_score(y_true_arr, y_pred_arr, labels=class_labels, average="macro", zero_division=0))
        weighted_f1 = float(f1_score(y_true_arr, y_pred_arr, labels=class_labels, average="weighted", zero_division=0))

        # Per-class recall
        per_class_recalls_arr = recall_score(y_true_arr, y_pred_arr, labels=class_labels, average=None, zero_division=0)
        per_class_recall_dict = {
            cls_name: float(per_class_recalls_arr[i])
            for i, cls_name in enumerate(class_labels)
        }

        high_recall = per_class_recall_dict.get("HIGH", 0.0)
        critical_recall = per_class_recall_dict.get("CRITICAL", 0.0)

        # High + Critical combined recall: recall across all samples whose true class is HIGH or CRITICAL
        high_crit_mask = np.isin(y_true_arr, ["HIGH", "CRITICAL"])
        if np.any(high_crit_mask):
            high_crit_correct = np.isin(y_pred_arr[high_crit_mask], ["HIGH", "CRITICAL"])
            high_critical_combined_recall = float(np.mean(high_crit_correct))
        else:
            high_critical_combined_recall = 1.0

        # 4x4 Confusion Matrix
        cm = confusion_matrix(y_true_arr, y_pred_arr, labels=class_labels)
        cm_list = cm.tolist()

        # Multiclass OvR ROC-AUC
        roc_auc_val: Optional[float] = None
        roc_auc_status = "calculated"

        if y_prob is not None:
            try:
                # Map true string labels to canonical integer indices
                y_true_indices = np.array([class_labels.index(c) for c in y_true_arr])
                unique_indices = sorted(np.unique(y_true_indices))

                if len(unique_indices) >= 2:
                    if len(unique_indices) == len(class_labels):
                        roc_auc_val = float(
                            roc_auc_score(
                                y_true_indices,
                                y_prob,
                                multi_class="ovr",
                                average="macro",
                            )
                        )
                    else:
                        # Subset probabilities to present classes
                        prob_subset = y_prob[:, unique_indices]
                        prob_subset = prob_subset / prob_subset.sum(axis=1, keepdims=True)
                        roc_auc_val = float(
                            roc_auc_score(
                                y_true_indices,
                                prob_subset,
                                labels=unique_indices,
                                multi_class="ovr",
                                average="macro",
                            )
                        )
                else:
                    roc_auc_status = "undefined_single_class_in_target"
            except Exception as e:
                roc_auc_status = f"undefined: {str(e)}"
                roc_auc_val = None
        else:
            roc_auc_status = "no_probabilities_provided"

        return {
            "accuracy": round(acc, 4),
            "macro_precision": round(macro_prec, 4),
            "weighted_precision": round(weighted_prec, 4),
            "macro_recall": round(macro_rec, 4),
            "weighted_recall": round(weighted_rec, 4),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "high_recall": round(high_recall, 4),
            "critical_recall": round(critical_recall, 4),
            "high_critical_combined_recall": round(high_critical_combined_recall, 4),
            "per_class_recall": per_class_recall_dict,
            "confusion_matrix": cm_list,
            "class_labels": class_labels,
            "roc_auc": round(roc_auc_val, 4) if roc_auc_val is not None else None,
            "roc_auc_status": roc_auc_status,
        }


class RiskModelSelector:
    """Selects the champion model using validation metrics and safety recall gates."""

    @classmethod
    def select_champion(
        cls,
        validation_results: Dict[str, Dict[str, Any]],
        minimum_high_recall: float = 0.50,
        minimum_critical_recall: float = 0.50,
    ) -> Tuple[Optional[str], Dict[str, Any], str]:
        """
        Determines the champion model from validation evaluation results.
        Returns (champion_name, champion_metrics, selection_rationale).
        """
        if not validation_results:
            return None, {}, "No models evaluated."

        safe_candidates: List[Tuple[str, Dict[str, Any]]] = []
        excluded_candidates: List[Tuple[str, str]] = []

        for model_name, metrics in validation_results.items():
            hr = metrics.get("high_recall", 0.0)
            cr = metrics.get("critical_recall", 0.0)

            if hr < minimum_high_recall or cr < minimum_critical_recall:
                excluded_candidates.append(
                    (model_name, f"Failed safety recall gate (HIGH: {hr:.2f} < {minimum_high_recall}, CRITICAL: {cr:.2f} < {minimum_critical_recall})")
                )
            else:
                safe_candidates.append((model_name, metrics))

        # If no model passes strict safety recall, check if we must trigger NO_SAFE_CHAMPION
        if not safe_candidates:
            rationale = (
                f"STATUS: NO_SAFE_CHAMPION. All models failed safety constraints "
                f"(min HIGH recall: {minimum_high_recall}, min CRITICAL recall: {minimum_critical_recall}). "
                f"Excluded: {excluded_candidates}"
            )
            return None, {}, rationale

        # Sort surviving candidates deterministically
        def sort_key(item: Tuple[str, Dict[str, Any]]):
            name, m = item
            macro_f1 = m.get("macro_f1", 0.0)
            combined_rec = m.get("high_critical_combined_recall", 0.0)
            macro_rec = m.get("macro_recall", 0.0)
            weighted_f1 = m.get("weighted_f1", 0.0)
            simplicity = -MODEL_SIMPLICITY_ORDER.get(name, 99)
            return (macro_f1, combined_rec, macro_rec, weighted_f1, simplicity)

        ranked = sorted(safe_candidates, key=sort_key, reverse=True)
        champion_name, champion_metrics = ranked[0]

        rationale = (
            f"Selected '{champion_name}' with highest Validation Macro F1 ({champion_metrics.get('macro_f1', 0.0):.4f}) "
            f"satisfying safety recall gates (HIGH Recall: {champion_metrics.get('high_recall', 0.0):.4f} >= {minimum_high_recall}, "
            f"CRITICAL Recall: {champion_metrics.get('critical_recall', 0.0):.4f} >= {minimum_critical_recall}). "
            f"Combined HIGH/CRITICAL Recall: {champion_metrics.get('high_critical_combined_recall', 0.0):.4f}."
        )

        return champion_name, champion_metrics, rationale
