"""
Scikit-Learn Preprocessing Pipeline for Academic Datasets.

Constructs a robust, leakage-safe ColumnTransformer pipeline:
- Numerical Features: SimpleImputer(strategy="median") -> RobustScaler / StandardScaler
- Categorical Features: SimpleImputer(strategy="constant", fill_value="Unknown") -> OneHotEncoder(handle_unknown="ignore")
- Fit Isolation: Pipeline is STRICTLY fit on X_train.
- Target Isolation: Target variables (semester_cgpa, grade, risk_level) are completely excluded from X.
- Reusable Artifacts: Saves preprocessor.joblib and feature_metadata.json for inference.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler

from ml.config.pipeline_config import (
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    LEAKAGE_TARGET_COLUMNS,
    IDENTIFIER_COLUMNS,
    REGISTRY_DIR,
    DEFAULT_CONFIG,
    PipelineConfig,
)
from ml.pipelines.engineering import FEATURE_CATALOG


class AcademicPreprocessor:
    """
    Leakage-safe Preprocessing Pipeline wrapper around Sklearn ColumnTransformer.
    Ensures zero transformation leakage and handles unseen categorical levels at inference.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.num_features = list(NUMERICAL_FEATURES)
        self.cat_features = list(CATEGORICAL_FEATURES)
        self.fitted_feature_names: List[str] = []
        self.is_fitted: bool = False
        self.pipeline: Optional[ColumnTransformer] = None
        self._build_pipeline()

    def _build_pipeline(self):
        # Numerical sub-pipeline
        scaler = RobustScaler() if self.config.scaling_method == "robust" else StandardScaler()
        num_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy=self.config.num_impute_strategy)),
            ("scaler", scaler),
        ])

        # Categorical sub-pipeline
        cat_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy=self.config.cat_impute_strategy, fill_value=self.config.cat_fill_value)),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])

        # Composite ColumnTransformer
        self.pipeline = ColumnTransformer(
            transformers=[
                ("num", num_pipeline, self.num_features),
                ("cat", cat_pipeline, self.cat_features),
            ],
            remainder="drop",
        )

    def extract_features_and_target(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """
        Extracts feature matrix X and target y, enforcing target isolation.
        Removes identifiers and leakage columns from X.
        """
        data = df.copy()
        
        # Extract target if present
        target_series = None
        target_col = "semester_cgpa"
        if target_col in data.columns:
            target_series = pd.to_numeric(data[target_col], errors="coerce")

        # Exclude leakage and identifier columns from X
        drop_cols = [col for col in LEAKAGE_TARGET_COLUMNS + IDENTIFIER_COLUMNS if col in data.columns]
        X = data.drop(columns=drop_cols)
        
        return X, target_series

    def fit(self, X_train: pd.DataFrame) -> "AcademicPreprocessor":
        """Fits the pipeline strictly on training data."""
        # Ensure all expected columns exist in X_train (with fallback nulls if missing)
        X = self._align_columns(X_train)
        self.pipeline.fit(X)
        
        # Extract fitted feature names
        self.fitted_feature_names = self._extract_output_feature_names()
        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transforms feature matrix X using the fitted pipeline."""
        if not self.is_fitted:
            raise RuntimeError("AcademicPreprocessor must be fitted on training data before calling transform().")
        
        aligned_X = self._align_columns(X)
        transformed_arr = self.pipeline.transform(aligned_X)
        
        return pd.DataFrame(transformed_arr, columns=self.fitted_feature_names, index=X.index)

    def fit_transform(self, X_train: pd.DataFrame) -> pd.DataFrame:
        """Fits on X_train and transforms X_train."""
        return self.fit(X_train).transform(X_train)

    def _align_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensures all numerical and categorical columns exist in DataFrame."""
        aligned = df.copy()
        for col in self.num_features:
            if col not in aligned.columns:
                aligned[col] = np.nan
        for col in self.cat_features:
            if col not in aligned.columns:
                aligned[col] = self.config.cat_fill_value
        return aligned

    def _extract_output_feature_names(self) -> List[str]:
        names = []
        try:
            raw_names = self.pipeline.get_feature_names_out()
            for name in raw_names:
                # Clean prefix for readability (e.g. num__attendance_percentage -> attendance_percentage)
                cleaned = name.replace("num__", "").replace("cat__", "enc_")
                names.append(cleaned)
        except Exception:
            # Fallback manual generation
            names.extend(self.num_features)
            cat_encoder = self.pipeline.named_transformers_["cat"].named_steps["onehot"]
            cat_out = cat_encoder.get_feature_names_out(self.cat_features)
            names.extend([f"enc_{c}" for c in cat_out])
        return names

    def save(self, filepath: Optional[Path] = None) -> Path:
        """Serializes the preprocessor pipeline artifact."""
        if not self.is_fitted:
            raise RuntimeError("Cannot save an unfitted preprocessor artifact.")
        
        target_path = filepath or (REGISTRY_DIR / "preprocessor.joblib")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, target_path)
        
        # Save feature metadata contract
        self._save_metadata(target_path.parent / "feature_metadata.json")
        return target_path

    def _save_metadata(self, meta_path: Path):
        meta = {
            "preprocessor_version": "1.0.0",
            "scaling_method": self.config.scaling_method,
            "num_impute_strategy": self.config.num_impute_strategy,
            "cat_impute_strategy": self.config.cat_impute_strategy,
            "total_input_features": len(self.num_features) + len(self.cat_features),
            "total_transformed_features": len(self.fitted_feature_names),
            "numerical_features": self.num_features,
            "categorical_features": self.cat_features,
            "transformed_feature_names": self.fitted_feature_names,
            "engineered_features_catalog": {
                k: {
                    "description": v.description,
                    "formula": v.formula,
                    "availability": v.availability_time,
                    "leakage_status": v.leakage_status,
                }
                for k, v in FEATURE_CATALOG.items()
            },
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    @classmethod
    def load(cls, filepath: Path) -> "AcademicPreprocessor":
        """Loads a preprocessor instance from a serialized joblib artifact."""
        instance = cls()
        instance.pipeline = joblib.load(filepath)
        instance.is_fitted = True
        instance.fitted_feature_names = instance._extract_output_feature_names()
        return instance
