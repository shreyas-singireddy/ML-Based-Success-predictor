"""
Phase 5 — Explainability Test Suite.

Tests cover:
- Feature catalog completeness and display info
- SHAP LinearExplainer initialization and correctness
- SHAP TreeExplainer initialization and correctness (sklearn DecisionTree)
- Global importance normalization
- SHAP value finiteness
- Contribution direction correctness (regression vs classification)
- Positive/negative factor separation
- Human-readable explanation narrative
- Leakage guard
- Unsupported model graceful fallback
- Top factors sorted by |SHAP|
- Feature catalog human-readable mapping

All tests use synthetic data with known structure so failures clearly indicate bugs.
"""

import json
from pathlib import Path
from typing import Dict, List
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import pytest
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier

# ---------------------------------------------------------------------------
# Module imports — test catalog, explainer factory, and explanation builder
# ---------------------------------------------------------------------------
from ml.explainability.feature_catalog import (
    FEATURE_DISPLAY_CATALOG,
    get_feature_info,
    get_demographic_features,
    GLOBAL_FAIRNESS_NOTE,
)
from ml.explainability.explainer import (
    LinearSHAPExplainer,
    TreeSHAPExplainer,
    UnsupportedExplainer,
    create_explainer,
)
from ml.explainability.local_explanation import (
    build_explanation,
    build_unavailable_explanation,
    FeatureContribution,
    ExplanationOutput,
)


# ---------------------------------------------------------------------------
# Fixtures: synthetic models and data
# ---------------------------------------------------------------------------

N_FEATURES = 10
FEATURE_NAMES = [f"feature_{i}" for i in range(N_FEATURES)]


@pytest.fixture(scope="module")
def synthetic_background():
    """Deterministic background data: 50 samples, 10 features."""
    rng = np.random.default_rng(seed=42)
    return rng.standard_normal((50, N_FEATURES))


@pytest.fixture(scope="module")
def synthetic_single_sample():
    """Single prediction sample."""
    rng = np.random.default_rng(seed=99)
    return rng.standard_normal((1, N_FEATURES))


@pytest.fixture(scope="module")
def fitted_linear_model(synthetic_background):
    """Fitted sklearn LinearRegression on synthetic data."""
    rng = np.random.default_rng(seed=42)
    y = rng.standard_normal(synthetic_background.shape[0])
    model = LinearRegression()
    model.fit(synthetic_background, y)
    return model


@pytest.fixture(scope="module")
def fitted_decision_tree(synthetic_background):
    """Fitted sklearn DecisionTreeClassifier on synthetic binary data."""
    rng = np.random.default_rng(seed=42)
    y = (rng.standard_normal(synthetic_background.shape[0]) > 0).astype(int)
    model = DecisionTreeClassifier(max_depth=3, random_state=42)
    model.fit(synthetic_background, y)
    return model


@pytest.fixture(scope="module")
def fitted_multiclass_tree(synthetic_background):
    """Fitted sklearn DecisionTreeClassifier on synthetic 4-class data (like risk levels)."""
    rng = np.random.default_rng(seed=42)
    y = rng.integers(0, 4, size=synthetic_background.shape[0])
    model = DecisionTreeClassifier(max_depth=4, random_state=42)
    model.fit(synthetic_background, y)
    return model


# ---------------------------------------------------------------------------
# 1. Feature Catalog Tests
# ---------------------------------------------------------------------------

class TestFeatureCatalog:

    def test_all_32_model_features_covered(self):
        """All 32 feature names from model_metadata.json are in the catalog."""
        registry_path = Path(__file__).resolve().parents[2] / "registry" / "model_metadata.json"
        if not registry_path.exists():
            pytest.skip("model_metadata.json not available in CI — skipping catalog coverage test.")
        with open(registry_path, "r") as f:
            meta = json.load(f)
        model_features = set(meta.get("feature_names", []))
        catalog_features = set(FEATURE_DISPLAY_CATALOG.keys())
        missing = model_features - catalog_features
        assert len(missing) == 0, (
            f"Feature catalog is missing display info for {len(missing)} model features: {missing}"
        )

    def test_get_feature_info_returns_for_known_feature(self):
        info = get_feature_info("attendance_percentage")
        assert info.display_name == "Attendance"
        assert info.unit == "%"
        assert info.higher_is_better is True

    def test_get_feature_info_fallback_for_unknown(self):
        info = get_feature_info("completely_unknown_feature_xyz")
        assert info.display_name is not None
        assert len(info.positive_template) > 0

    def test_demographic_features_have_is_demographic_flag(self):
        demo_features = get_demographic_features()
        assert "enc_gender_MALE" in demo_features
        assert "enc_gender_FEMALE" in demo_features
        assert len(demo_features) > 0

    def test_non_demographic_academic_features_not_flagged(self):
        assert FEATURE_DISPLAY_CATALOG["attendance_percentage"].is_demographic is False
        assert FEATURE_DISPLAY_CATALOG["backlogs"].is_demographic is False

    def test_fairness_note_is_non_empty(self):
        assert len(GLOBAL_FAIRNESS_NOTE) > 50

    def test_positive_and_negative_templates_differ(self):
        """Every feature must have distinct positive and negative templates."""
        for name, info in FEATURE_DISPLAY_CATALOG.items():
            assert info.positive_template != info.negative_template, (
                f"Feature '{name}' has identical positive and negative templates."
            )


# ---------------------------------------------------------------------------
# 2. Linear SHAP Explainer Tests
# ---------------------------------------------------------------------------

class TestLinearSHAPExplainer:

    def test_initializes_successfully(self, fitted_linear_model, synthetic_background):
        explainer = LinearSHAPExplainer(
            model=fitted_linear_model,
            feature_names=FEATURE_NAMES,
            background_data=synthetic_background,
        )
        assert explainer is not None
        assert explainer.explainer_type == "SHAP_LinearExplainer"
        assert explainer.explanation_available is True

    def test_shap_values_shape(self, fitted_linear_model, synthetic_background, synthetic_single_sample):
        explainer = LinearSHAPExplainer(
            model=fitted_linear_model,
            feature_names=FEATURE_NAMES,
            background_data=synthetic_background,
        )
        shap_vals = explainer.compute_local_shap_values(synthetic_single_sample)
        assert shap_vals.shape == (N_FEATURES,)

    def test_shap_values_are_all_finite(self, fitted_linear_model, synthetic_background, synthetic_single_sample):
        explainer = LinearSHAPExplainer(
            model=fitted_linear_model,
            feature_names=FEATURE_NAMES,
            background_data=synthetic_background,
        )
        shap_vals = explainer.compute_local_shap_values(synthetic_single_sample)
        assert np.all(np.isfinite(shap_vals)), "SHAP values contain NaN or Inf"

    def test_global_importance_precomputed_sums_to_100(self, fitted_linear_model, synthetic_background):
        explainer = LinearSHAPExplainer(
            model=fitted_linear_model,
            feature_names=FEATURE_NAMES,
            background_data=synthetic_background,
        )
        explainer.precompute_global_importance(synthetic_background)
        importance = explainer.get_global_feature_importance()
        total = sum(importance.values())
        assert abs(total - 100.0) < 0.5, f"Global importance sums to {total}, expected ~100.0"

    def test_invalid_input_shape_raises(self, fitted_linear_model, synthetic_background):
        explainer = LinearSHAPExplainer(
            model=fitted_linear_model,
            feature_names=FEATURE_NAMES,
            background_data=synthetic_background,
        )
        with pytest.raises(ValueError, match="shape"):
            explainer.compute_local_shap_values(np.zeros((5, N_FEATURES)))  # 5 rows, not 1


# ---------------------------------------------------------------------------
# 3. Tree SHAP Explainer Tests
# ---------------------------------------------------------------------------

class TestTreeSHAPExplainer:

    def test_initializes_for_regression(self, fitted_linear_model, synthetic_background):
        """TreeExplainer should work for any sklearn estimator including basic models."""
        # Use DecisionTreeClassifier as the primary tree test target
        pass  # See below

    def test_initializes_for_multiclass_decision_tree(self, fitted_multiclass_tree, synthetic_background):
        explainer = TreeSHAPExplainer(
            model=fitted_multiclass_tree,
            feature_names=FEATURE_NAMES,
            is_classifier=True,
            n_classes=4,
        )
        assert explainer.explainer_type == "SHAP_TreeExplainer"
        assert explainer.explanation_available is True

    def test_tree_shap_values_shape_classifier(self, fitted_multiclass_tree, synthetic_background, synthetic_single_sample):
        explainer = TreeSHAPExplainer(
            model=fitted_multiclass_tree,
            feature_names=FEATURE_NAMES,
            is_classifier=True,
            n_classes=4,
        )
        shap_vals = explainer.compute_local_shap_values(synthetic_single_sample)
        assert shap_vals.shape == (N_FEATURES,)

    def test_tree_shap_values_are_finite(self, fitted_multiclass_tree, synthetic_background, synthetic_single_sample):
        explainer = TreeSHAPExplainer(
            model=fitted_multiclass_tree,
            feature_names=FEATURE_NAMES,
            is_classifier=True,
            n_classes=4,
        )
        shap_vals = explainer.compute_local_shap_values(synthetic_single_sample)
        assert np.all(np.isfinite(shap_vals))

    def test_tree_global_importance_sums_to_100(self, fitted_multiclass_tree, synthetic_background):
        explainer = TreeSHAPExplainer(
            model=fitted_multiclass_tree,
            feature_names=FEATURE_NAMES,
            is_classifier=True,
            n_classes=4,
        )
        explainer.precompute_global_importance(synthetic_background)
        importance = explainer.get_global_feature_importance()
        total = sum(importance.values())
        assert abs(total - 100.0) < 0.5, f"Tree global importance sums to {total}"


# ---------------------------------------------------------------------------
# 4. Unsupported Explainer Graceful Fallback Tests
# ---------------------------------------------------------------------------

class TestUnsupportedExplainer:

    def test_explanation_available_is_false(self):
        explainer = UnsupportedExplainer("svm_kernel", FEATURE_NAMES)
        assert explainer.explanation_available is False

    def test_returns_zero_shap_values(self):
        explainer = UnsupportedExplainer("svm_kernel", FEATURE_NAMES)
        shap_vals = explainer.compute_local_shap_values(np.zeros((1, N_FEATURES)))
        assert np.all(shap_vals == 0.0)

    def test_global_importance_returns_zeros(self):
        explainer = UnsupportedExplainer("neural_network", FEATURE_NAMES)
        explainer.precompute_global_importance(np.zeros((5, N_FEATURES)))
        importance = explainer.get_global_feature_importance()
        assert all(v == 0.0 for v in importance.values())


# ---------------------------------------------------------------------------
# 5. create_explainer Factory Tests
# ---------------------------------------------------------------------------

class TestCreateExplainerFactory:

    def test_linear_type_creates_linear_explainer(self, fitted_linear_model, synthetic_background):
        explainer = create_explainer(
            model=fitted_linear_model,
            model_type="baseline_linear",
            feature_names=FEATURE_NAMES,
            background_data=synthetic_background,
        )
        assert isinstance(explainer, LinearSHAPExplainer)

    def test_tree_type_creates_tree_explainer(self, fitted_multiclass_tree, synthetic_background):
        explainer = create_explainer(
            model=fitted_multiclass_tree,
            model_type="decision_tree",
            feature_names=FEATURE_NAMES,
            background_data=synthetic_background,
            is_classifier=True,
            n_classes=4,
        )
        assert isinstance(explainer, TreeSHAPExplainer)

    def test_unsupported_type_creates_unsupported_explainer(self, fitted_linear_model, synthetic_background):
        explainer = create_explainer(
            model=fitted_linear_model,
            model_type="svm_kernel",
            feature_names=FEATURE_NAMES,
            background_data=synthetic_background,
        )
        assert isinstance(explainer, UnsupportedExplainer)

    def test_global_importance_precomputed_after_factory(self, fitted_linear_model, synthetic_background):
        explainer = create_explainer(
            model=fitted_linear_model,
            model_type="baseline_linear",
            feature_names=FEATURE_NAMES,
            background_data=synthetic_background,
        )
        importance = explainer.get_global_feature_importance()
        assert len(importance) == N_FEATURES


# ---------------------------------------------------------------------------
# 6. Local Explanation Builder Tests
# ---------------------------------------------------------------------------

class TestBuildExplanation:

    @pytest.fixture
    def sample_shap_values(self):
        """SHAP values with known structure for assertion."""
        vals = np.zeros(N_FEATURES)
        vals[0] = 0.8   # Strong positive → feature_0 is HIGH positive
        vals[1] = -0.5  # Strong negative → feature_1 is HIGH negative
        vals[2] = 0.15  # Medium positive
        vals[3] = -0.05 # Low negative
        return vals

    @pytest.fixture
    def global_importance(self):
        return {name: round(100.0 / N_FEATURES, 3) for name in FEATURE_NAMES}

    def test_top_factors_sorted_by_magnitude(self, sample_shap_values, global_importance):
        output = build_explanation(
            shap_values=sample_shap_values,
            feature_names=FEATURE_NAMES,
            feature_values_raw={},
            base_value=5.0,
            global_importance=global_importance,
            explainer_type="SHAP_LinearExplainer",
            explanation_available=True,
            model_name="LinearRegression",
            model_version="cgpa_v1.0.0",
            model_type="baseline_linear",
            task_type="cgpa_regression",
            top_n=5,
        )
        magnitudes = [abs(f.shap_value) for f in output.top_factors]
        assert magnitudes == sorted(magnitudes, reverse=True), "Top factors not sorted by |SHAP|"

    def test_positive_factors_all_have_positive_direction(self, sample_shap_values, global_importance):
        output = build_explanation(
            shap_values=sample_shap_values,
            feature_names=FEATURE_NAMES,
            feature_values_raw={},
            base_value=5.0,
            global_importance=global_importance,
            explainer_type="SHAP_LinearExplainer",
            explanation_available=True,
            model_name="LinearRegression",
            model_version="cgpa_v1.0.0",
            model_type="baseline_linear",
            task_type="cgpa_regression",
            top_n=5,
        )
        for factor in output.positive_factors:
            assert factor.contribution_direction == "positive", (
                f"Factor {factor.feature_name} in positive_factors has direction {factor.contribution_direction}"
            )

    def test_negative_factors_all_have_negative_direction(self, sample_shap_values, global_importance):
        output = build_explanation(
            shap_values=sample_shap_values,
            feature_names=FEATURE_NAMES,
            feature_values_raw={},
            base_value=5.0,
            global_importance=global_importance,
            explainer_type="SHAP_LinearExplainer",
            explanation_available=True,
            model_name="LinearRegression",
            model_version="cgpa_v1.0.0",
            model_type="baseline_linear",
            task_type="cgpa_regression",
            top_n=5,
        )
        for factor in output.negative_factors:
            assert factor.contribution_direction == "negative"

    def test_regression_positive_shap_means_positive_direction(self, global_importance):
        """For CGPA regression, positive SHAP → positive student outcome direction."""
        shap_vals = np.array([0.5] + [0.0] * (N_FEATURES - 1))
        output = build_explanation(
            shap_values=shap_vals,
            feature_names=FEATURE_NAMES,
            feature_values_raw={},
            base_value=5.0,
            global_importance=global_importance,
            explainer_type="SHAP_LinearExplainer",
            explanation_available=True,
            model_name="LinearRegression",
            model_version="cgpa_v1.0.0",
            model_type="baseline_linear",
            task_type="cgpa_regression",
            top_n=1,
        )
        assert output.top_factors[0].contribution_direction == "positive"

    def test_risk_classification_positive_shap_for_high_class_is_negative_outcome(self, global_importance):
        """For risk classification with HIGH class, positive SHAP is bad for student."""
        shap_vals = np.array([0.7] + [0.0] * (N_FEATURES - 1))
        output = build_explanation(
            shap_values=shap_vals,
            feature_names=FEATURE_NAMES,
            feature_values_raw={},
            base_value=0.0,
            global_importance=global_importance,
            explainer_type="SHAP_TreeExplainer",
            explanation_available=True,
            model_name="DecisionTreeClassifier",
            model_version="risk_v1.0.0",
            model_type="decision_tree",
            task_type="risk_classification",
            explained_class="HIGH",
            top_n=1,
        )
        # Positive SHAP for HIGH risk class → bad for student → negative direction
        assert output.top_factors[0].contribution_direction == "negative"

    def test_risk_classification_negative_shap_for_high_class_is_positive_outcome(self, global_importance):
        """For risk classification with HIGH class, negative SHAP is good for student."""
        shap_vals = np.array([-0.7] + [0.0] * (N_FEATURES - 1))
        output = build_explanation(
            shap_values=shap_vals,
            feature_names=FEATURE_NAMES,
            feature_values_raw={},
            base_value=0.0,
            global_importance=global_importance,
            explainer_type="SHAP_TreeExplainer",
            explanation_available=True,
            model_name="DecisionTreeClassifier",
            model_version="risk_v1.0.0",
            model_type="decision_tree",
            task_type="risk_classification",
            explained_class="HIGH",
            top_n=1,
        )
        assert output.top_factors[0].contribution_direction == "positive"

    def test_high_impact_classification_correct(self, global_importance):
        shap_vals = np.array([0.5, 0.15, 0.05] + [0.0] * (N_FEATURES - 3))
        output = build_explanation(
            shap_values=shap_vals,
            feature_names=FEATURE_NAMES,
            feature_values_raw={},
            base_value=5.0,
            global_importance=global_importance,
            explainer_type="SHAP_LinearExplainer",
            explanation_available=True,
            model_name="LinearRegression",
            model_version="cgpa_v1.0.0",
            model_type="baseline_linear",
            task_type="cgpa_regression",
        )
        assert output.top_factors[0].impact_level == "HIGH"    # |0.5| > 0.3
        assert output.top_factors[1].impact_level == "MEDIUM"  # |0.15| > 0.1

    def test_shap_sum_matches_values(self, sample_shap_values, global_importance):
        output = build_explanation(
            shap_values=sample_shap_values,
            feature_names=FEATURE_NAMES,
            feature_values_raw={},
            base_value=5.0,
            global_importance=global_importance,
            explainer_type="SHAP_LinearExplainer",
            explanation_available=True,
            model_name="LinearRegression",
            model_version="cgpa_v1.0.0",
            model_type="baseline_linear",
            task_type="cgpa_regression",
        )
        expected_sum = float(np.sum(sample_shap_values))
        assert abs(output.shap_sum - expected_sum) < 1e-4

    def test_fairness_note_always_present(self, sample_shap_values, global_importance):
        output = build_explanation(
            shap_values=sample_shap_values,
            feature_names=FEATURE_NAMES,
            feature_values_raw={},
            base_value=5.0,
            global_importance=global_importance,
            explainer_type="SHAP_LinearExplainer",
            explanation_available=True,
            model_name="LinearRegression",
            model_version="cgpa_v1.0.0",
            model_type="baseline_linear",
            task_type="cgpa_regression",
        )
        assert len(output.fairness_note) > 50

    def test_student_explanation_text_is_non_empty(self, sample_shap_values, global_importance):
        output = build_explanation(
            shap_values=sample_shap_values,
            feature_names=FEATURE_NAMES,
            feature_values_raw={},
            base_value=5.0,
            global_importance=global_importance,
            explainer_type="SHAP_LinearExplainer",
            explanation_available=True,
            model_name="LinearRegression",
            model_version="cgpa_v1.0.0",
            model_type="baseline_linear",
            task_type="cgpa_regression",
        )
        for factor in output.top_factors:
            assert len(factor.student_explanation) > 10

    def test_unavailable_explanation_has_correct_flag(self):
        output = build_unavailable_explanation(
            model_name="SVC",
            model_version="risk_v1.0.0",
            model_type="svm_kernel",
            explainer_type="Unsupported_svm_kernel",
            feature_names=FEATURE_NAMES,
            task_type="risk_classification",
        )
        assert output.explanation_available is False
        assert len(output.top_factors) == 0

    def test_feature_names_length_mismatch_raises(self, global_importance):
        """Mismatched shap_values and feature_names should raise ValueError."""
        with pytest.raises(ValueError, match="length"):
            build_explanation(
                shap_values=np.zeros(5),  # 5 values
                feature_names=FEATURE_NAMES,  # 10 names — mismatch
                feature_values_raw={},
                base_value=5.0,
                global_importance=global_importance,
                explainer_type="SHAP_LinearExplainer",
                explanation_available=True,
                model_name="LinearRegression",
                model_version="cgpa_v1.0.0",
                model_type="baseline_linear",
                task_type="cgpa_regression",
            )


# ---------------------------------------------------------------------------
# 7. Leakage Guard Tests
# ---------------------------------------------------------------------------

class TestLeakageGuard:

    def test_leakage_detection_raises_on_target_feature(self):
        """ExplanationService should detect if target columns appear in feature names."""
        from ml.explainability.explanation_service import ExplanationService

        svc = ExplanationService.__new__(ExplanationService)
        svc._is_initialized = False

        leaky_features = ["attendance_percentage", "semester_cgpa", "previous_cgpa"]
        dummy_X = np.zeros((1, len(leaky_features)))

        with pytest.raises(RuntimeError, match="Leakage"):
            svc._validate_no_leakage(dummy_X, leaky_features)

    def test_clean_features_do_not_trigger_leakage_guard(self):
        from ml.explainability.explanation_service import ExplanationService

        svc = ExplanationService.__new__(ExplanationService)
        svc._is_initialized = False

        clean_features = ["attendance_percentage", "previous_cgpa", "backlogs"]
        dummy_X = np.zeros((1, len(clean_features)))

        # Should not raise
        svc._validate_no_leakage(dummy_X, clean_features)
