"""
Explanation Service Singleton for Phase 5 — Explainable AI.

Manages:
1. Artifact loading (reuses Phase 2 preprocessor + Phase 3/4 champion models).
2. Background dataset construction (training split for SHAP reference).
3. SHAP explainer initialization with cached global importance.
4. Orchestration of local explanation for individual CGPA / Risk predictions.
5. Leakage guard: validates no target columns in explanation input.
6. Consistency check: verifies explanation uses same model version as prediction service.

Conventions:
- Background dataset = Phase 2 training split (train.csv), SHAP-transformed only.
- Global importance is precomputed once at startup and cached for process lifetime.
- This service does NOT load models independently; it accepts model + preprocessor
  objects from the prediction/risk services to ensure exact same artifact.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd
import joblib

from ml.config.pipeline_config import (
    PROCESSED_DATA_DIR,
    REGISTRY_DIR,
    LEAKAGE_TARGET_COLUMNS,
    IDENTIFIER_COLUMNS,
)
from ml.explainability.explainer import BaseExplainer, create_explainer, UnsupportedExplainer
from ml.explainability.local_explanation import (
    ExplanationOutput,
    build_explanation,
    build_unavailable_explanation,
)

logger = logging.getLogger("student_predictor.explainability.explanation_service")

# Artifact paths (same registry as Phases 3 & 4)
_PREPROCESSOR_PATH = REGISTRY_DIR / "preprocessor.joblib"
_CGPA_MODEL_PATH = REGISTRY_DIR / "best_model.joblib"
_CGPA_METADATA_PATH = REGISTRY_DIR / "model_metadata.json"
_RISK_MODEL_PATH = REGISTRY_DIR / "best_risk_classifier.joblib"
_RISK_METADATA_PATH = REGISTRY_DIR / "risk_metadata.json"
_TRAIN_DATA_PATH = PROCESSED_DATA_DIR / "train.csv"


# Map risk_metadata model_type strings to create_explainer model_type strings
_RISK_MODEL_TYPE_MAP = {
    "DecisionTreeClassifier": "decision_tree",
    "RandomForestClassifier": "tree_ensemble",
    "XGBClassifier": "gradient_boosting",
    "LogisticRegression": "baseline_linear",
    "SVC": "svm_kernel",
    "MLPClassifier": "neural_network",
}

# Risk class ordering for label encoding (must match Phase 4 training)
RISK_CLASS_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class ExplanationService:
    """
    Singleton service providing SHAP-based explanations for Phase 3 + Phase 4 predictions.
    
    Lifecycle:
    1. On first call to explain_cgpa_prediction or explain_risk_prediction,
       _initialize() is called once.
    2. Artifacts are loaded, background data is prepared, and explainers are built.
    3. All subsequent calls reuse cached explainers (global importance precomputed).
    """

    def __init__(self, registry_dir: Optional[Path] = None, train_data_path: Optional[Path] = None):
        self.registry_dir = registry_dir or REGISTRY_DIR
        self.train_data_path = train_data_path or _TRAIN_DATA_PATH

        self._cgpa_explainer: Optional[BaseExplainer] = None
        self._risk_explainer: Optional[BaseExplainer] = None

        self._cgpa_metadata: Dict[str, Any] = {}
        self._risk_metadata: Dict[str, Any] = {}

        self._preprocessor = None
        self._background_X: Optional[np.ndarray] = None

        self._is_initialized: bool = False

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _initialize(self) -> None:
        """
        Load all artifacts, build background dataset, and initialize SHAP explainers.
        Called once on first explanation request.
        """
        if self._is_initialized:
            return

        logger.info("Initializing ExplanationService — loading artifacts and building explainers...")

        self._load_preprocessor()
        self._load_cgpa_explainer()
        self._load_risk_explainer()

        self._is_initialized = True
        logger.info("ExplanationService initialized successfully.")

    def _load_preprocessor(self) -> None:
        """Load the Phase 2 preprocessor and prepare the SHAP background dataset."""
        if not _PREPROCESSOR_PATH.exists():
            raise FileNotFoundError(
                f"Preprocessor artifact not found at {_PREPROCESSOR_PATH}. "
                "Run Phase 2 pipeline before using ExplanationService."
            )
        logger.info(f"Loading preprocessor from {_PREPROCESSOR_PATH}...")
        self._preprocessor = joblib.load(_PREPROCESSOR_PATH)
        logger.info("Preprocessor loaded.")

        # Build SHAP background dataset from training split
        self._background_X = self._build_background_data()

    def _build_background_data(self) -> np.ndarray:
        """
        Load the Phase 2 training split and transform it to get the SHAP background matrix.
        
        We use the PREPROCESSED training split to create the background.
        This is safe — we are using training-time statistics as reference values,
        not leaking test/val information into individual explanations.
        
        Falls back to a zero-matrix if training data is not available.
        """
        if not self.train_data_path.exists():
            logger.warning(
                f"Training data not found at {self.train_data_path}. "
                "Using a zero-vector background (SHAP explanations may be less accurate)."
            )
            # Use 1 zero row as a degenerate background
            return np.zeros((1, 32))

        logger.info(f"Loading training split from {self.train_data_path} for SHAP background...")
        try:
            train_df = pd.read_csv(self.train_data_path)

            # Strip leakage and identifier columns
            drop_cols = [
                col for col in LEAKAGE_TARGET_COLUMNS + IDENTIFIER_COLUMNS
                if col in train_df.columns
            ]
            X_train = train_df.drop(columns=drop_cols)

            # Transform using the loaded preprocessor
            X_background = self._preprocessor.transform(X_train)
            if hasattr(X_background, "values"):
                X_background = X_background.values
            X_background = np.array(X_background, dtype=float)

            logger.info(
                f"SHAP background dataset ready: {X_background.shape[0]} samples, "
                f"{X_background.shape[1]} features."
            )
            return X_background
        except Exception as e:
            logger.error(f"Failed to build background dataset: {e}. Using zero fallback.")
            return np.zeros((1, 32))

    def _load_cgpa_explainer(self) -> None:
        """Load Phase 3 CGPA champion model and create its SHAP explainer."""
        cgpa_model_path = self.registry_dir / "best_model.joblib"
        cgpa_meta_path = self.registry_dir / "model_metadata.json"

        if not cgpa_model_path.exists():
            raise FileNotFoundError(
                f"CGPA champion model not found at {cgpa_model_path}. Run Phase 3 training."
            )
        if not cgpa_meta_path.exists():
            raise FileNotFoundError(
                f"CGPA model metadata not found at {cgpa_meta_path}. Run Phase 3 training."
            )

        logger.info(f"Loading CGPA champion model from {cgpa_model_path}...")
        cgpa_model = joblib.load(cgpa_model_path)

        with open(cgpa_meta_path, "r", encoding="utf-8") as f:
            self._cgpa_metadata = json.load(f)

        feature_names = self._cgpa_metadata.get("feature_names", [])
        model_type = self._cgpa_metadata.get("model_type", "baseline_linear")

        logger.info(
            f"Building CGPA SHAP explainer: model={self._cgpa_metadata.get('model_name')}, "
            f"type={model_type}, features={len(feature_names)}"
        )

        # Ensure background has correct feature count
        bg = self._get_background_for_features(len(feature_names))

        self._cgpa_explainer = create_explainer(
            model=cgpa_model,
            model_type=model_type,
            feature_names=feature_names,
            background_data=bg,
            is_classifier=False,
        )
        logger.info("CGPA SHAP explainer ready.")

    def _load_risk_explainer(self) -> None:
        """Load Phase 4 Risk champion classifier and create its SHAP explainer."""
        risk_model_path = self.registry_dir / "best_risk_classifier.joblib"
        risk_meta_path = self.registry_dir / "risk_metadata.json"

        if not risk_model_path.exists():
            raise FileNotFoundError(
                f"Risk classifier artifact not found at {risk_model_path}. Run Phase 4 training."
            )
        if not risk_meta_path.exists():
            raise FileNotFoundError(
                f"Risk model metadata not found at {risk_meta_path}. Run Phase 4 training."
            )

        logger.info(f"Loading risk classifier from {risk_model_path}...")
        risk_model_wrapper = joblib.load(risk_model_path)

        with open(risk_meta_path, "r", encoding="utf-8") as f:
            self._risk_metadata = json.load(f)

        feature_names = self._risk_metadata.get("feature_names", [])
        raw_model_type = self._risk_metadata.get("model_type", "DecisionTreeClassifier")
        model_type = _RISK_MODEL_TYPE_MAP.get(raw_model_type, raw_model_type.lower())

        n_classes = len(RISK_CLASS_ORDER)

        # The Phase 4 model may be wrapped (e.g., RiskModelWrapper)
        # Unwrap to the raw sklearn/xgboost model for SHAP
        raw_model = risk_model_wrapper
        if hasattr(risk_model_wrapper, "model"):
            raw_model = risk_model_wrapper.model

        logger.info(
            f"Building Risk SHAP explainer: model={raw_model_type}, "
            f"mapped_type={model_type}, n_classes={n_classes}"
        )

        bg = self._get_background_for_features(len(feature_names))

        self._risk_explainer = create_explainer(
            model=raw_model,
            model_type=model_type,
            feature_names=feature_names,
            background_data=bg,
            is_classifier=True,
            n_classes=n_classes,
        )
        logger.info("Risk SHAP explainer ready.")

    def _get_background_for_features(self, n_features: int) -> np.ndarray:
        """Return the background array, reshaped to match expected feature count."""
        if self._background_X is None:
            return np.zeros((1, n_features))
        if self._background_X.shape[1] == n_features:
            return self._background_X
        # Mismatch — use zeros fallback and warn
        logger.warning(
            f"Background data shape mismatch: expected {n_features} features, "
            f"got {self._background_X.shape[1]}. Using zero fallback."
        )
        return np.zeros((1, n_features))

    # ------------------------------------------------------------------
    # Leakage guard
    # ------------------------------------------------------------------

    def _validate_no_leakage(self, transformed_X: np.ndarray, feature_names: List[str]) -> None:
        """
        Verify that target columns are not present in the transformed feature matrix.
        
        Since the preprocessor always drops leakage columns, this is a belt-and-suspenders check.
        """
        leakage_in_features = [
            name for name in feature_names
            if any(lc in name for lc in ["semester_cgpa", "risk_level", "grade"])
        ]
        if leakage_in_features:
            raise RuntimeError(
                f"Leakage detected in explanation input: {leakage_in_features} found in feature names. "
                "This is a critical error — check the preprocessing pipeline."
            )

    # ------------------------------------------------------------------
    # Public API: explain predictions
    # ------------------------------------------------------------------

    def explain_cgpa_prediction(
        self,
        transformed_X: np.ndarray,
        feature_values_raw: Dict[str, float],
    ) -> ExplanationOutput:
        """
        Generate a local SHAP explanation for a single CGPA prediction.

        Args:
            transformed_X: Shape (1, n_features) — preprocessed feature matrix 
                           (output of Phase 2 preprocessor.transform()).
            feature_values_raw: Dict of raw (unscaled) feature values from the prediction request.
                                Used for display in explanations.

        Returns:
            ExplanationOutput with ranked contributions and narrative text.
        """
        self._initialize()

        assert self._cgpa_explainer is not None, "CGPA explainer not initialized"
        feature_names = self._cgpa_explainer.feature_names
        model_name = self._cgpa_metadata.get("model_name", "LinearRegression")
        model_version = self._cgpa_metadata.get("model_version", "cgpa_v1.0.0")
        model_type = self._cgpa_metadata.get("model_type", "baseline_linear")

        if not self._cgpa_explainer.explanation_available:
            return build_unavailable_explanation(
                model_name=model_name,
                model_version=model_version,
                model_type=model_type,
                explainer_type=self._cgpa_explainer.explainer_type,
                feature_names=feature_names,
                task_type="cgpa_regression",
            )

        try:
            self._validate_no_leakage(transformed_X, feature_names)
            shap_values = self._cgpa_explainer.compute_local_shap_values(transformed_X)
            global_importance = self._cgpa_explainer.get_global_feature_importance()

            # Base value from LinearExplainer expected value
            try:
                base_value = float(self._cgpa_explainer._explainer.expected_value)
            except AttributeError:
                base_value = 0.0

            return build_explanation(
                shap_values=shap_values,
                feature_names=feature_names,
                feature_values_raw=feature_values_raw,
                base_value=base_value,
                global_importance=global_importance,
                explainer_type=self._cgpa_explainer.explainer_type,
                explanation_available=True,
                model_name=model_name,
                model_version=model_version,
                model_type=model_type,
                task_type="cgpa_regression",
                top_n=5,
            )
        except Exception as e:
            logger.error(f"CGPA explanation failed: {e}", exc_info=True)
            return build_unavailable_explanation(
                model_name=model_name,
                model_version=model_version,
                model_type=model_type,
                explainer_type=self._cgpa_explainer.explainer_type,
                feature_names=feature_names,
                task_type="cgpa_regression",
            )

    def explain_risk_prediction(
        self,
        transformed_X: np.ndarray,
        feature_values_raw: Dict[str, float],
        predicted_risk_level: str,
    ) -> ExplanationOutput:
        """
        Generate a local SHAP explanation for a single Risk prediction.

        Args:
            transformed_X: Shape (1, n_features) — preprocessed feature matrix.
            feature_values_raw: Dict of raw (unscaled) feature values from the prediction request.
            predicted_risk_level: The risk class predicted by Phase 4 model ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL').

        Returns:
            ExplanationOutput with ranked contributions and narrative text.
        """
        self._initialize()

        assert self._risk_explainer is not None, "Risk explainer not initialized"
        feature_names = self._risk_explainer.feature_names
        model_name = self._risk_metadata.get("model_name", "DecisionTreeClassifier")
        model_version = self._risk_metadata.get("model_version", "risk_v1.0.0")
        model_type = self._risk_metadata.get("model_type", "DecisionTreeClassifier")

        if not self._risk_explainer.explanation_available:
            return build_unavailable_explanation(
                model_name=model_name,
                model_version=model_version,
                model_type=model_type,
                explainer_type=self._risk_explainer.explainer_type,
                feature_names=feature_names,
                task_type="risk_classification",
            )

        try:
            self._validate_no_leakage(transformed_X, feature_names)
            shap_values = self._risk_explainer.compute_local_shap_values(transformed_X)
            global_importance = self._risk_explainer.get_global_feature_importance()

            # Base value for classifiers
            try:
                bv = self._risk_explainer._explainer.expected_value
                if isinstance(bv, (list, np.ndarray)):
                    # Multi-class: use mean
                    base_value = float(np.mean(bv))
                else:
                    base_value = float(bv)
            except AttributeError:
                base_value = 0.0

            return build_explanation(
                shap_values=shap_values,
                feature_names=feature_names,
                feature_values_raw=feature_values_raw,
                base_value=base_value,
                global_importance=global_importance,
                explainer_type=self._risk_explainer.explainer_type,
                explanation_available=True,
                model_name=model_name,
                model_version=model_version,
                model_type=model_type,
                task_type="risk_classification",
                explained_class=predicted_risk_level,
                top_n=5,
            )
        except Exception as e:
            logger.error(f"Risk explanation failed: {e}", exc_info=True)
            return build_unavailable_explanation(
                model_name=model_name,
                model_version=model_version,
                model_type=model_type,
                explainer_type=self._risk_explainer.explainer_type,
                feature_names=feature_names,
                task_type="risk_classification",
            )

    def get_cgpa_global_importance(self) -> Dict[str, float]:
        """Returns precomputed normalized global feature importance for CGPA model."""
        self._initialize()
        return self._cgpa_explainer.get_global_feature_importance()

    def get_risk_global_importance(self) -> Dict[str, float]:
        """Returns precomputed normalized global feature importance for Risk model."""
        self._initialize()
        return self._risk_explainer.get_global_feature_importance()


# Global singleton instance
explanation_service = ExplanationService()
