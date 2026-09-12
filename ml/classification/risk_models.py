"""
Risk Classifiers Suite for Academic Risk Prediction.

Implements all six required classifiers:
1. DecisionTreeClassifier
2. RandomForestClassifier
3. LogisticRegression
4. Support Vector Classifier (SVC with probability=True)
5. XGBClassifier
6. MLPClassifier (Neural Network)

Provides uniform wrapper handling class alignment with standard classes:
['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].
"""

from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from ml.classification.risk_policy import RISK_CLASSES


class XGBoostRiskWrapper(BaseEstimator, ClassifierMixin):
    """
    Wrapper around XGBClassifier that safely manages string label encoding
    and probability alignment with standard target classes.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 4,
        learning_rate: float = 0.08,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.model = XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=self.random_state,
            eval_metric="mlogloss",
        )
        self.label_encoder = LabelEncoder()
        self.classes_: np.ndarray = np.array([])

    def fit(self, X: np.ndarray, y: np.ndarray) -> "XGBoostRiskWrapper":
        # Fit label encoder on observed y
        y_encoded = self.label_encoder.fit_transform(y)
        self.classes_ = self.label_encoder.classes_
        self.model.fit(X, y_encoded)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        preds_encoded = self.model.predict(X)
        return self.label_encoder.inverse_transform(preds_encoded)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)


def get_risk_classifiers(random_seed: int = 42) -> Dict[str, BaseEstimator]:
    """
    Instantiates and returns all six required classifiers configured for academic risk prediction.
    """
    return {
        "DecisionTreeClassifier": DecisionTreeClassifier(
            max_depth=5,
            min_samples_split=4,
            class_weight="balanced",
            random_state=random_seed,
        ),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            class_weight="balanced",
            random_state=random_seed,
        ),
        "LogisticRegression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=random_seed,
        ),
        "SVC": SVC(
            kernel="rbf",
            probability=True,
            class_weight="balanced",
            random_state=random_seed,
        ),
        "XGBClassifier": XGBoostRiskWrapper(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=random_seed,
        ),
        "MLPClassifier": MLPClassifier(
            hidden_layer_sizes=(64, 32),
            activation="relu",
            alpha=0.01,
            max_iter=500,
            random_state=random_seed,
        ),
    }


def extract_aligned_probabilities(
    model: BaseEstimator,
    X: np.ndarray,
    target_classes: Optional[List[str]] = None,
) -> np.ndarray:
    """
    Extracts prediction probabilities for input matrix X and ensures the columns
    are strictly aligned with the canonical class ordering:
    ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].
    Handles models with fewer fitted classes gracefully.
    """
    classes_list = target_classes or RISK_CLASSES
    raw_probs = model.predict_proba(X)  # shape (N, n_classes_fitted)
    model_classes = list(model.classes_)

    aligned_probs = np.zeros((len(X), len(classes_list)), dtype=float)
    for col_idx, cls_name in enumerate(classes_list):
        if cls_name in model_classes:
            raw_col_idx = model_classes.index(cls_name)
            aligned_probs[:, col_idx] = raw_probs[:, raw_col_idx]
        else:
            aligned_probs[:, col_idx] = 0.0

    # Renormalize rows to sum to 1.0 within tolerance if any floating precision drift
    row_sums = aligned_probs.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    aligned_probs = aligned_probs / row_sums

    return aligned_probs
