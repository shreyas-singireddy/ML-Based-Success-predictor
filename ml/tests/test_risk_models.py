"""
Unit Tests for Risk Classifiers Suite (6 Models) & Probability Extraction.
"""

import pytest
import numpy as np
from ml.classification.risk_models import get_risk_classifiers, extract_aligned_probabilities
from ml.classification.risk_policy import RISK_CLASSES


@pytest.fixture
def dummy_classification_data():
    """Generates synthetic multi-class training data."""
    np.random.seed(42)
    N = 100
    D = 10
    X = np.random.randn(N, D)
    classes = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    y = np.random.choice(classes, size=N, p=[0.35, 0.25, 0.25, 0.15])
    return X, y


def test_all_six_models_train_and_predict(dummy_classification_data):
    """Verifies all six required classifiers fit, predict, and produce valid probabilities."""
    X, y = dummy_classification_data
    models = get_risk_classifiers(random_seed=42)

    assert len(models) == 6
    expected_names = {
        "DecisionTreeClassifier",
        "RandomForestClassifier",
        "LogisticRegression",
        "SVC",
        "XGBClassifier",
        "MLPClassifier",
    }
    assert set(models.keys()) == expected_names

    for name, model in models.items():
        # 1. Fit
        model.fit(X, y)

        # 2. Predict classes
        preds = model.predict(X)
        assert len(preds) == len(y)
        assert all(p in RISK_CLASSES for p in preds), f"Model {name} returned invalid class: {preds}"

        # 3. Extract and validate aligned probabilities
        probs = extract_aligned_probabilities(model, X, RISK_CLASSES)
        assert probs.shape == (len(X), 4), f"Model {name} probs shape was {probs.shape}"
        assert np.all(probs >= 0.0) and np.all(probs <= 1.0), f"Model {name} produced out-of-bound probabilities"
        assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-4), f"Model {name} probabilities do not sum to 1.0"
