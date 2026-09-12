"""
SHAP Explainer Factory for ML-Based Student Success Predictor.

Provides a model-agnostic interface for computing SHAP values across the
champion model types used in Phases 3 and 4:

  Phase 3 (CGPA Regression)   → LinearRegression   → shap.LinearExplainer
  Phase 4 (Risk Classification) → DecisionTree      → shap.TreeExplainer
  Future tree models (RF, XGB) → shap.TreeExplainer
  Unsupported models (SVC, MLP) → UnsupportedExplainer (graceful fallback)

Design constraints:
- Explainers are created once and reused (no per-request re-fitting).
- For LinearExplainer, a background dataset (training feature matrix) is
  required for SHAP reference values. This must be the TRAIN split only —
  never val or test.
- SHAP values are computed on the already-transformed (preprocessed) feature
  matrix X_transformed, NOT on raw features.
- No SHAP value is cached between calls — each prediction gets fresh local SHAP.
- Global feature importance is precomputed once and cached in the explainer.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("student_predictor.explainability.explainer")

# ---------------------------------------------------------------------------
# Supported model type strings (matched against model metadata 'model_type')
# ---------------------------------------------------------------------------
_LINEAR_MODEL_TYPES = {"baseline_linear"}
_TREE_MODEL_TYPES = {"tree_ensemble", "gradient_boosting", "decision_tree"}
_UNSUPPORTED_TYPES = {"svm_kernel", "neural_network"}


class BaseExplainer(ABC):
    """Abstract interface for all SHAP explainer wrappers."""

    def __init__(self, feature_names: List[str]):
        self.feature_names = feature_names
        self._global_importance: Optional[Dict[str, float]] = None

    @property
    @abstractmethod
    def explainer_type(self) -> str:
        """Human-readable explainer type string for metadata."""
        ...

    @property
    def explanation_available(self) -> bool:
        return True

    @abstractmethod
    def _compute_raw_shap(self, X_transformed: np.ndarray) -> np.ndarray:
        """
        Compute raw SHAP values for a single preprocessed input row.

        Args:
            X_transformed: Shape (1, n_features) — single sample, post-preprocessing.

        Returns:
            np.ndarray of shape (n_features,) — SHAP values.
        """
        ...

    def compute_local_shap_values(self, X_transformed: np.ndarray) -> np.ndarray:
        """
        Public method: compute and validate local SHAP values.

        Args:
            X_transformed: Shape (1, n_features) — single sample.

        Returns:
            np.ndarray of shape (n_features,) — validated SHAP values.

        Raises:
            ValueError: if input shape is invalid.
            RuntimeError: if SHAP computation fails.
        """
        if X_transformed.ndim != 2 or X_transformed.shape[0] != 1:
            raise ValueError(
                f"Expected X_transformed of shape (1, n_features), got {X_transformed.shape}"
            )
        if X_transformed.shape[1] != len(self.feature_names):
            raise ValueError(
                f"Feature count mismatch: got {X_transformed.shape[1]} features, "
                f"expected {len(self.feature_names)}"
            )

        shap_vals = self._compute_raw_shap(X_transformed)

        # Validate output
        if not np.all(np.isfinite(shap_vals)):
            nan_count = np.sum(~np.isfinite(shap_vals))
            logger.error(
                f"SHAP computation produced {nan_count} non-finite values. "
                f"Returning zeros for non-finite entries."
            )
            shap_vals = np.where(np.isfinite(shap_vals), shap_vals, 0.0)

        return shap_vals

    def get_global_feature_importance(self) -> Dict[str, float]:
        """
        Returns cached global feature importance (normalized to sum to 100%).

        Global importance is the expected |SHAP| over the background dataset,
        normalized so values sum to 100.

        Returns:
            Dict mapping feature_name → importance percentage (float, sums to 100.0).
        """
        if self._global_importance is None:
            raise RuntimeError(
                "Global importance not computed yet. Call precompute_global_importance() first."
            )
        return self._global_importance

    @abstractmethod
    def precompute_global_importance(self, X_background: np.ndarray) -> None:
        """
        Precompute global feature importance from background dataset.

        Args:
            X_background: Shape (n_samples, n_features) — training split or representative subset.
        """
        ...

    def _normalize_importance(self, raw_importance: np.ndarray) -> Dict[str, float]:
        """Normalize raw importances to percentages summing to 100.0."""
        total = raw_importance.sum()
        if total == 0.0:
            percentages = np.zeros_like(raw_importance)
        else:
            percentages = (raw_importance / total) * 100.0
        return {
            name: round(float(pct), 3)
            for name, pct in zip(self.feature_names, percentages)
        }


class LinearSHAPExplainer(BaseExplainer):
    """
    SHAP explainer for LinearRegression using shap.LinearExplainer.

    LinearExplainer computes exact SHAP values (no approximation) using the
    model's coefficients and a background dataset for expected feature values.
    """

    def __init__(self, model, feature_names: List[str], background_data: np.ndarray):
        """
        Args:
            model: Fitted sklearn LinearRegression instance.
            feature_names: List of transformed feature names (length = n_features).
            background_data: Training set feature matrix (n_samples, n_features).
                             Used as the reference distribution for SHAP.
        """
        super().__init__(feature_names)
        import shap

        if background_data.ndim != 2:
            raise ValueError("background_data must be 2D array (n_samples, n_features)")

        logger.info(
            f"Initializing LinearSHAPExplainer with {background_data.shape[0]} background samples "
            f"and {len(feature_names)} features."
        )
        self._explainer = shap.LinearExplainer(
            model,
            masker=shap.maskers.Independent(background_data),
        )
        logger.info("LinearSHAPExplainer initialized successfully.")

    @property
    def explainer_type(self) -> str:
        return "SHAP_LinearExplainer"

    def _compute_raw_shap(self, X_transformed: np.ndarray) -> np.ndarray:
        shap_values = self._explainer.shap_values(X_transformed)
        return shap_values[0]  # shape (n_features,)

    def precompute_global_importance(self, X_background: np.ndarray) -> None:
        """
        Compute global importance as mean(|SHAP|) over the background dataset.

        For LinearExplainer this is equivalent to the expected absolute contribution.
        Computed over a random sample of at most 500 background points to keep
        startup time bounded.
        """
        import shap

        sample_size = min(500, X_background.shape[0])
        rng = np.random.default_rng(42)
        idx = rng.choice(X_background.shape[0], size=sample_size, replace=False)
        X_sample = X_background[idx]

        logger.info(
            f"Computing LinearExplainer global importance over {sample_size} samples..."
        )
        shap_matrix = self._explainer.shap_values(X_sample)  # (n_samples, n_features)
        mean_abs = np.mean(np.abs(shap_matrix), axis=0)
        self._global_importance = self._normalize_importance(mean_abs)
        logger.info("LinearExplainer global importance precomputed.")


class TreeSHAPExplainer(BaseExplainer):
    """
    SHAP explainer for tree-based models using shap.TreeExplainer.

    Applicable to:
    - sklearn DecisionTreeClassifier / Regressor
    - sklearn RandomForestClassifier / Regressor
    - xgboost.XGBClassifier / XGBRegressor

    TreeExplainer computes exact SHAP values using the tree structure.
    """

    def __init__(
        self,
        model,
        feature_names: List[str],
        is_classifier: bool = False,
        n_classes: Optional[int] = None,
    ):
        """
        Args:
            model: Fitted tree-based sklearn or XGBoost model instance.
            feature_names: List of transformed feature names.
            is_classifier: True if model is a classifier (multi-class SHAP output).
            n_classes: Number of classes (required when is_classifier=True).
        """
        super().__init__(feature_names)
        import shap

        self._is_classifier = is_classifier
        self._n_classes = n_classes

        logger.info(
            f"Initializing TreeSHAPExplainer "
            f"(classifier={is_classifier}, n_classes={n_classes})."
        )
        self._explainer = shap.TreeExplainer(model)
        logger.info("TreeSHAPExplainer initialized successfully.")

    @property
    def explainer_type(self) -> str:
        return "SHAP_TreeExplainer"

    def _compute_raw_shap(self, X_transformed: np.ndarray) -> np.ndarray:
        """
        Returns SHAP values for regression or the predicted-class SHAP values
        for classification.

        For classifiers: shape (n_classes, n_features) → we return the SHAP
        values for the predicted class index (argmax of SHAP base + sum).
        """
        shap_output = self._explainer.shap_values(X_transformed)

        if self._is_classifier:
            # shap_output: list of n_classes arrays, each (1, n_features)
            # Determine predicted class by which class has highest sum of SHAP values
            # (robust to models where .predict() isn't called here)
            if isinstance(shap_output, list):
                # Shape per class: (1, n_features) → squeeze to (n_features,)
                class_shap_arrays = [arr[0] for arr in shap_output]
                # Pick class with largest sum (highest push toward prediction)
                class_magnitudes = [np.sum(np.abs(arr)) for arr in class_shap_arrays]
                predicted_class_idx = int(np.argmax(class_magnitudes))
                logger.debug(
                    f"TreeSHAP classifier: selected class index {predicted_class_idx} "
                    f"for explanation (highest |SHAP| magnitude)."
                )
                return class_shap_arrays[predicted_class_idx]
            else:
                # Some versions return ndarray for binary classifiers
                if shap_output.ndim == 3:
                    return shap_output[0, :, -1]  # last class
                return shap_output[0]
        else:
            # Regression: shape (1, n_features)
            if isinstance(shap_output, list):
                return shap_output[0][0]
            return shap_output[0]

    def precompute_global_importance(self, X_background: np.ndarray) -> None:
        """
        Compute global importance as mean(|SHAP|) over a background subset.

        For tree models, this is an efficient approximation using a sample
        of at most 300 points (trees are much faster than linear).
        """
        sample_size = min(300, X_background.shape[0])
        rng = np.random.default_rng(42)
        idx = rng.choice(X_background.shape[0], size=sample_size, replace=False)
        X_sample = X_background[idx]

        logger.info(
            f"Computing TreeSHAP global importance over {sample_size} samples..."
        )
        shap_output = self._explainer.shap_values(X_sample)

        if self._is_classifier and isinstance(shap_output, list):
            # Average over classes: each element is (n_samples, n_features)
            all_abs = np.stack([np.abs(arr) for arr in shap_output], axis=0)
            mean_abs = np.mean(all_abs, axis=(0, 1))  # average over classes and samples
        elif isinstance(shap_output, np.ndarray) and shap_output.ndim == 3:
            mean_abs = np.mean(np.abs(shap_output), axis=(0, 1))
        else:
            # Regression: (n_samples, n_features)
            if isinstance(shap_output, list):
                shap_output = shap_output[0]
            mean_abs = np.mean(np.abs(shap_output), axis=0)

        self._global_importance = self._normalize_importance(mean_abs)
        logger.info("TreeSHAP global importance precomputed.")


class UnsupportedExplainer(BaseExplainer):
    """
    Fallback explainer for model types not supported by Phase 5 SHAP integration.
    Applies to: SVC (KernelExplainer — too expensive), MLP (KernelExplainer — too expensive).

    Returns a graceful response with explanation_available=False.
    """

    def __init__(self, model_type: str, feature_names: List[str]):
        super().__init__(feature_names)
        self._model_type = model_type
        logger.warning(
            f"UnsupportedExplainer instantiated for model_type='{model_type}'. "
            f"Local SHAP explanations will not be available."
        )

    @property
    def explainer_type(self) -> str:
        return f"Unsupported_{self._model_type}"

    @property
    def explanation_available(self) -> bool:
        return False

    def _compute_raw_shap(self, X_transformed: np.ndarray) -> np.ndarray:
        return np.zeros(len(self.feature_names))

    def compute_local_shap_values(self, X_transformed: np.ndarray) -> np.ndarray:
        return np.zeros(len(self.feature_names))

    def precompute_global_importance(self, X_background: np.ndarray) -> None:
        self._global_importance = {name: 0.0 for name in self.feature_names}

    def get_global_feature_importance(self) -> Dict[str, float]:
        return {name: 0.0 for name in self.feature_names}


def create_explainer(
    model,
    model_type: str,
    feature_names: List[str],
    background_data: np.ndarray,
    is_classifier: bool = False,
    n_classes: Optional[int] = None,
) -> BaseExplainer:
    """
    Factory function: create the appropriate SHAP explainer for a given model.

    Args:
        model: Fitted sklearn or XGBoost model object.
        model_type: String from model metadata (e.g., "baseline_linear", "tree_ensemble").
        feature_names: List of transformed feature names (length must match model input).
        background_data: Training set feature matrix (n_samples, n_features).
        is_classifier: True if model outputs class probabilities.
        n_classes: Number of output classes (used for classifiers).

    Returns:
        An appropriate BaseExplainer subclass instance with global importance precomputed.
    """
    normalized_type = model_type.lower().strip()

    if normalized_type in _LINEAR_MODEL_TYPES:
        explainer = LinearSHAPExplainer(model, feature_names, background_data)
    elif normalized_type in _TREE_MODEL_TYPES:
        explainer = TreeSHAPExplainer(
            model, feature_names, is_classifier=is_classifier, n_classes=n_classes
        )
    else:
        logger.warning(
            f"Model type '{model_type}' is not in supported types "
            f"({_LINEAR_MODEL_TYPES | _TREE_MODEL_TYPES}). "
            f"Using UnsupportedExplainer."
        )
        explainer = UnsupportedExplainer(model_type, feature_names)

    # Precompute global importance for supported explainers
    explainer.precompute_global_importance(background_data)
    return explainer
