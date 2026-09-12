"""
Model Definitions and Wrappers for CGPA Regression.

Defines the three required models:
1. Linear Regression (Baseline)
2. Random Forest Regressor (Non-linear ensemble)
3. XGBoost Regressor (Gradient boosted decision trees)

Provides uniform fit/predict interface and feature importance extraction:
- Linear Regression: Linear coefficients (beta weights)
- Random Forest: Mean Decrease in Impurity (MDI / variance reduction)
- XGBoost: Feature importances (gain / weight)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor


class BaseCGPAModel(ABC):
    """Abstract base class for CGPA regression models."""

    def __init__(self, name: str, model_type: str):
        self.name = name
        self.model_type = model_type
        self.model = None
        self.feature_names: List[str] = []
        self.is_fitted: bool = False

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "BaseCGPAModel":
        pass

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted or self.model is None:
            raise RuntimeError(f"Model {self.name} is not fitted yet.")
        preds = self.model.predict(X)
        # Bounded CGPA output check [0.0, 10.0]
        return np.clip(preds, 0.0, 10.0)

    @abstractmethod
    def get_feature_importances(self) -> Dict[str, float]:
        """Returns feature importance or coefficient weights."""
        pass


class LinearRegressionModel(BaseCGPAModel):
    """Linear Regression baseline model with coefficient analysis."""

    def __init__(self, fit_intercept: bool = True):
        super().__init__(name="LinearRegression", model_type="baseline_linear")
        self.fit_intercept = fit_intercept
        self.model = LinearRegression(fit_intercept=fit_intercept)

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "LinearRegressionModel":
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def get_feature_importances(self) -> Dict[str, float]:
        if not self.is_fitted:
            return {}
        coefs = self.model.coef_
        return {name: round(float(coef), 4) for name, coef in zip(self.feature_names, coefs)}


class RandomForestModel(BaseCGPAModel):
    """
    Random Forest Regressor.
    Feature importance is computed as Mean Decrease in Impurity (MDI / variance reduction).
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = 8,
        min_samples_split: int = 4,
        random_state: int = 42,
    ):
        super().__init__(name="RandomForestRegressor", model_type="tree_ensemble")
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            random_state=random_state,
        )

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "RandomForestModel":
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def get_feature_importances(self) -> Dict[str, float]:
        if not self.is_fitted:
            return {}
        importances = self.model.feature_importances_
        return {name: round(float(imp), 4) for name, imp in zip(self.feature_names, importances)}


class XGBoostModel(BaseCGPAModel):
    """
    XGBoost Gradient Boosted Decision Trees Regressor.
    Feature importance is computed via tree gain/weight.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 4,
        learning_rate: float = 0.08,
        subsample: float = 0.85,
        random_state: int = 42,
    ):
        super().__init__(name="XGBRegressor", model_type="gradient_boosting")
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.random_state = random_state
        self.model = XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            random_state=random_state,
            verbosity=0,
        )

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "XGBoostModel":
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def get_feature_importances(self) -> Dict[str, float]:
        if not self.is_fitted:
            return {}
        importances = self.model.feature_importances_
        return {name: round(float(imp), 4) for name, imp in zip(self.feature_names, importances)}


def get_candidate_models(random_seed: int = 42) -> List[BaseCGPAModel]:
    """Factory returning instances of the three required models."""
    return [
        LinearRegressionModel(),
        RandomForestModel(random_state=random_seed),
        XGBoostModel(random_state=random_seed),
    ]
