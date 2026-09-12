"""
Feature Display Catalog for Explainable AI.

Maps every transformed feature name (including OHE-encoded names) to a
human-readable label, description, direction of positive impact,
and narrative templates for student-facing explanations.

This is the single source of truth for how ML features are presented
to students, faculty, and administrators.

Design principles:
- No fabricated rules: templates use the word "associates" or
  "corresponds", NOT "causes" or "proves".
- Every feature has a fairness note flag for demographics.
- Encoded OHE features (e.g., enc_gender_MALE) are grouped under their
  parent feature for display purposes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class FeatureDisplayInfo:
    """Human-readable metadata for a single model feature."""

    # Displayed name in UI (e.g. "Attendance Rate")
    display_name: str

    # What this feature measures
    description: str

    # Unit string shown alongside value (e.g., "%", "points", "count")
    unit: str

    # True if higher value is associated with better outcome
    higher_is_better: bool

    # Template for explaining a positive SHAP contribution (pushing CGPA up / Risk down)
    positive_template: str

    # Template for explaining a negative SHAP contribution (pushing CGPA down / Risk up)
    negative_template: str

    # True if feature is demographic — triggers fairness transparency note
    is_demographic: bool = False

    # Parent group for OHE-expanded features (e.g., "gender" for enc_gender_MALE)
    parent_group: Optional[str] = None

    # Original raw value label for OHE columns (e.g., "MALE" for enc_gender_MALE)
    ohe_value: Optional[str] = None


# ---------------------------------------------------------------------------
# Feature catalog — covers all 32 transformed features from model_metadata.json
# ---------------------------------------------------------------------------

FEATURE_DISPLAY_CATALOG: Dict[str, FeatureDisplayInfo] = {
    # ------------------------------------------------------------------
    # Numerical features (15)
    # ------------------------------------------------------------------
    "age": FeatureDisplayInfo(
        display_name="Age",
        description="Student's age in years",
        unit="years",
        higher_is_better=False,
        positive_template=(
            "Your age is associated with a slight positive influence on the model's prediction. "
            "The model may associate it with experience or maturity patterns in the dataset."
        ),
        negative_template=(
            "Your age has a small negative influence on this prediction. "
            "This reflects statistical patterns in the training data, not any judgment about ability."
        ),
        is_demographic=True,
    ),
    "semester": FeatureDisplayInfo(
        display_name="Semester",
        description="Current semester number (1–12)",
        unit="semester",
        higher_is_better=True,
        positive_template=(
            "Being in a higher semester is associated with stronger predicted outcomes "
            "in this dataset. The model reflects that later-semester students tend to have "
            "more established academic patterns."
        ),
        negative_template=(
            "Being in an earlier semester is associated with a slight downward influence. "
            "The model reflects patterns where early semesters show more variability."
        ),
    ),
    "attendance_percentage": FeatureDisplayInfo(
        display_name="Attendance",
        description="Percentage of classes attended this semester",
        unit="%",
        higher_is_better=True,
        positive_template=(
            "Your attendance rate is one of the model's strongest positive signals. "
            "The model strongly associates higher attendance with better predicted CGPA and lower risk."
        ),
        negative_template=(
            "Your attendance rate is one of the factors most negatively affecting this prediction. "
            "The model strongly associates lower attendance with poorer predicted outcomes."
        ),
    ),
    "previous_cgpa": FeatureDisplayInfo(
        display_name="Previous CGPA",
        description="Cumulative CGPA from all prior semesters",
        unit="/ 10.0",
        higher_is_better=True,
        positive_template=(
            "Your previous CGPA is positively influencing this prediction. "
            "The model uses past academic performance as a strong indicator of current trajectory."
        ),
        negative_template=(
            "Your previous CGPA is negatively influencing this prediction. "
            "The model associates a lower historical CGPA with a lower predicted current semester CGPA."
        ),
    ),
    "mid_1": FeatureDisplayInfo(
        display_name="Mid-Term 1 Score",
        description="Score in the first mid-term examination",
        unit="/ 100",
        higher_is_better=True,
        positive_template=(
            "Your Mid-Term 1 score contributes positively to this prediction. "
            "The model uses this as an early-semester academic performance signal."
        ),
        negative_template=(
            "Your Mid-Term 1 score is contributing negatively to this prediction. "
            "The model associates a lower Mid-Term 1 score with a lower predicted outcome."
        ),
    ),
    "mid_2": FeatureDisplayInfo(
        display_name="Mid-Term 2 Score",
        description="Score in the second mid-term examination",
        unit="/ 100",
        higher_is_better=True,
        positive_template=(
            "Your Mid-Term 2 score contributes positively to this prediction. "
            "Strong mid-semester performance is a meaningful signal for the model."
        ),
        negative_template=(
            "Your Mid-Term 2 score is a negative factor in this prediction. "
            "The model associates a lower Mid-Term 2 score with a lower predicted outcome."
        ),
    ),
    "internal_marks": FeatureDisplayInfo(
        display_name="Internal Assessment Marks",
        description="Continuous internal assessment marks throughout the semester",
        unit="/ 100",
        higher_is_better=True,
        positive_template=(
            "Your internal assessment marks are contributing positively. "
            "Consistent performance in internal assessments is a strong predictor in this model."
        ),
        negative_template=(
            "Your internal assessment marks are contributing negatively to this prediction. "
            "The model associates lower internal marks with weaker predicted outcomes."
        ),
    ),
    "backlogs": FeatureDisplayInfo(
        display_name="Active Backlogs",
        description="Number of subjects with active academic backlogs",
        unit="subjects",
        higher_is_better=False,
        positive_template=(
            "Having zero or few backlogs is contributing positively to this prediction. "
            "The model associates a clean academic record with better outcomes."
        ),
        negative_template=(
            "Your active backlogs are negatively influencing this prediction. "
            "The model strongly associates more backlogs with lower predicted CGPA and higher risk."
        ),
    ),
    "academic_average": FeatureDisplayInfo(
        display_name="Academic Average",
        description="Engineered composite of mid-term and internal assessment marks",
        unit="score",
        higher_is_better=True,
        positive_template=(
            "Your overall academic average is one of the most influential positive factors. "
            "This composite score combines your mid-term and internal performance and strongly "
            "guides the model's prediction."
        ),
        negative_template=(
            "Your overall academic average is negatively affecting this prediction. "
            "This composite score combines mid-term and internal marks — the model associates "
            "a lower average with weaker predicted outcomes."
        ),
    ),
    "attendance_risk_score": FeatureDisplayInfo(
        display_name="Attendance Risk Score",
        description="Engineered risk score derived from attendance percentage (higher = more at-risk)",
        unit="score",
        higher_is_better=False,
        positive_template=(
            "Your engineered attendance risk score is low, which contributes positively. "
            "This reflects that your attendance level does not place you in an at-risk zone."
        ),
        negative_template=(
            "Your engineered attendance risk score is elevated, contributing negatively. "
            "This risk score reflects how far your attendance falls below safe thresholds."
        ),
    ),
    "internal_average": FeatureDisplayInfo(
        display_name="Internal Mark Average",
        description="Engineered average of internal assessment marks",
        unit="score",
        higher_is_better=True,
        positive_template=(
            "Your internal mark average contributes positively to this prediction. "
            "Consistent internal assessment performance is valued by the model."
        ),
        negative_template=(
            "Your internal mark average is contributing negatively. "
            "The model associates a lower internal average with weaker academic outcomes."
        ),
    ),
    "mid_term_average": FeatureDisplayInfo(
        display_name="Mid-Term Average",
        description="Engineered average of Mid-Term 1 and Mid-Term 2 scores",
        unit="score",
        higher_is_better=True,
        positive_template=(
            "Your mid-term average is contributing positively to this prediction. "
            "Strong combined mid-semester exam performance is a positive signal."
        ),
        negative_template=(
            "Your mid-term average is contributing negatively. "
            "The model associates a lower mid-term average with lower predicted outcomes."
        ),
    ),
    "previous_cgpa_trend": FeatureDisplayInfo(
        display_name="CGPA Trend (Historical)",
        description="Engineered trend feature from multi-semester historical CGPA records",
        unit="trend",
        higher_is_better=True,
        positive_template=(
            "Your historical CGPA trend is improving, which positively influences the prediction. "
            "An upward trajectory in past semesters is a strong signal."
        ),
        negative_template=(
            "Your historical CGPA trend is declining or flat, contributing negatively. "
            "A downward trajectory in past performance records is factored in negatively."
        ),
    ),
    "backlog_severity_score": FeatureDisplayInfo(
        display_name="Backlog Severity Score",
        description="Engineered continuous severity score reflecting number and impact of backlogs",
        unit="score",
        higher_is_better=False,
        positive_template=(
            "Your backlog severity score is low or zero, contributing positively. "
            "The model associates a clean or minimal backlog record with better outcomes."
        ),
        negative_template=(
            "Your backlog severity score is elevated, negatively affecting this prediction. "
            "The model assigns significant weight to the severity of academic backlogs."
        ),
    ),
    "academic_stability": FeatureDisplayInfo(
        display_name="Academic Stability",
        description="Engineered score reflecting consistency of performance across assessments",
        unit="score",
        higher_is_better=True,
        positive_template=(
            "Your academic stability score is high, meaning your performance is consistent. "
            "The model rewards consistent academic performance across assessments."
        ),
        negative_template=(
            "Your academic stability score suggests variable performance. "
            "Large swings between assessments are associated with less predictable outcomes."
        ),
    ),
    # ------------------------------------------------------------------
    # OHE-encoded categorical features (17)
    # ------------------------------------------------------------------
    "enc_gender_FEMALE": FeatureDisplayInfo(
        display_name="Gender (Female)",
        description="One-hot encoded gender category",
        unit="",
        higher_is_better=True,
        positive_template=(
            "Your gender category has a slight positive association in the model's prediction. "
            "Note: demographic features reflect patterns in the training data, not inherent ability."
        ),
        negative_template=(
            "Your gender category has a slight negative association in the model's prediction. "
            "Note: demographic features reflect patterns in the training data, not inherent ability."
        ),
        is_demographic=True,
        parent_group="gender",
        ohe_value="FEMALE",
    ),
    "enc_gender_MALE": FeatureDisplayInfo(
        display_name="Gender (Male)",
        description="One-hot encoded gender category",
        unit="",
        higher_is_better=True,
        positive_template=(
            "Your gender category has a slight positive association in the model's prediction. "
            "Note: demographic features reflect patterns in the training data, not inherent ability."
        ),
        negative_template=(
            "Your gender category has a slight negative association in the model's prediction. "
            "Note: demographic features reflect patterns in the training data, not inherent ability."
        ),
        is_demographic=True,
        parent_group="gender",
        ohe_value="MALE",
    ),
    "enc_gender_OTHER": FeatureDisplayInfo(
        display_name="Gender (Other)",
        description="One-hot encoded gender category",
        unit="",
        higher_is_better=True,
        positive_template=(
            "Your gender category has a slight positive association in the model's prediction. "
            "Note: demographic features reflect patterns in the training data, not inherent ability."
        ),
        negative_template=(
            "Your gender category has a slight negative association in the model's prediction. "
            "Note: demographic features reflect patterns in the training data, not inherent ability."
        ),
        is_demographic=True,
        parent_group="gender",
        ohe_value="OTHER",
    ),
    "enc_department_code_AI": FeatureDisplayInfo(
        display_name="Department (AI)",
        description="One-hot encoded academic department",
        unit="",
        higher_is_better=True,
        positive_template="Your department is associated with slightly better outcomes in this dataset.",
        negative_template="Your department is associated with slightly lower outcomes in this dataset. This reflects distributional patterns, not any judgment about the department.",
        is_demographic=True,
        parent_group="department_code",
        ohe_value="AI",
    ),
    "enc_department_code_CIVIL": FeatureDisplayInfo(
        display_name="Department (Civil)",
        description="One-hot encoded academic department",
        unit="",
        higher_is_better=True,
        positive_template="Your department is associated with slightly better outcomes in this dataset.",
        negative_template="Your department is associated with slightly lower outcomes in this dataset. This reflects distributional patterns, not any judgment about the department.",
        is_demographic=True,
        parent_group="department_code",
        ohe_value="CIVIL",
    ),
    "enc_department_code_CS": FeatureDisplayInfo(
        display_name="Department (CS)",
        description="One-hot encoded academic department",
        unit="",
        higher_is_better=True,
        positive_template="Your department is associated with slightly better outcomes in this dataset.",
        negative_template="Your department is associated with slightly lower outcomes in this dataset. This reflects distributional patterns, not any judgment about the department.",
        is_demographic=True,
        parent_group="department_code",
        ohe_value="CS",
    ),
    "enc_department_code_DS": FeatureDisplayInfo(
        display_name="Department (DS)",
        description="One-hot encoded academic department",
        unit="",
        higher_is_better=True,
        positive_template="Your department is associated with slightly better outcomes in this dataset.",
        negative_template="Your department is associated with slightly lower outcomes in this dataset. This reflects distributional patterns, not any judgment about the department.",
        is_demographic=True,
        parent_group="department_code",
        ohe_value="DS",
    ),
    "enc_department_code_ECE": FeatureDisplayInfo(
        display_name="Department (ECE)",
        description="One-hot encoded academic department",
        unit="",
        higher_is_better=True,
        positive_template="Your department is associated with slightly better outcomes in this dataset.",
        negative_template="Your department is associated with slightly lower outcomes in this dataset. This reflects distributional patterns, not any judgment about the department.",
        is_demographic=True,
        parent_group="department_code",
        ohe_value="ECE",
    ),
    "enc_department_code_EEE": FeatureDisplayInfo(
        display_name="Department (EEE)",
        description="One-hot encoded academic department",
        unit="",
        higher_is_better=True,
        positive_template="Your department is associated with slightly better outcomes in this dataset.",
        negative_template="Your department is associated with slightly lower outcomes in this dataset. This reflects distributional patterns, not any judgment about the department.",
        is_demographic=True,
        parent_group="department_code",
        ohe_value="EEE",
    ),
    "enc_department_code_IT": FeatureDisplayInfo(
        display_name="Department (IT)",
        description="One-hot encoded academic department",
        unit="",
        higher_is_better=True,
        positive_template="Your department is associated with slightly better outcomes in this dataset.",
        negative_template="Your department is associated with slightly lower outcomes in this dataset. This reflects distributional patterns, not any judgment about the department.",
        is_demographic=True,
        parent_group="department_code",
        ohe_value="IT",
    ),
    "enc_department_code_MECH": FeatureDisplayInfo(
        display_name="Department (Mech)",
        description="One-hot encoded academic department",
        unit="",
        higher_is_better=True,
        positive_template="Your department is associated with slightly better outcomes in this dataset.",
        negative_template="Your department is associated with slightly lower outcomes in this dataset. This reflects distributional patterns, not any judgment about the department.",
        is_demographic=True,
        parent_group="department_code",
        ohe_value="MECH",
    ),
    "enc_attendance_risk_category_AT_RISK": FeatureDisplayInfo(
        display_name="Attendance Category (At Risk)",
        description="One-hot encoded attendance risk classification",
        unit="",
        higher_is_better=False,
        positive_template="Being classified as 'At Risk' by attendance has a small positive signal here (unusual — review raw attendance value).",
        negative_template="Being classified in the 'At Risk' attendance category contributes negatively. Your attendance falls below safe thresholds.",
        parent_group="attendance_risk_category",
        ohe_value="AT_RISK",
    ),
    "enc_attendance_risk_category_CRITICAL": FeatureDisplayInfo(
        display_name="Attendance Category (Critical)",
        description="One-hot encoded attendance risk classification",
        unit="",
        higher_is_better=False,
        positive_template="Being in the 'Critical' attendance category has a minimal positive signal here (likely offset by other features).",
        negative_template="Being classified in the 'Critical' attendance category contributes strongly and negatively. Attendance is critically low.",
        parent_group="attendance_risk_category",
        ohe_value="CRITICAL",
    ),
    "enc_attendance_risk_category_NORMAL": FeatureDisplayInfo(
        display_name="Attendance Category (Normal)",
        description="One-hot encoded attendance risk classification",
        unit="",
        higher_is_better=True,
        positive_template="Being in the 'Normal' attendance category contributes positively. Your attendance meets or exceeds required thresholds.",
        negative_template="Being outside the 'Normal' attendance category contributes negatively. This reflects attendance falling below safe thresholds.",
        parent_group="attendance_risk_category",
        ohe_value="NORMAL",
    ),
    "enc_backlog_severity_category_MODERATE": FeatureDisplayInfo(
        display_name="Backlog Severity (Moderate)",
        description="One-hot encoded backlog severity classification",
        unit="",
        higher_is_better=False,
        positive_template="Having a moderate backlog level is reflected here. While not ideal, it's considered a moderate burden by the model.",
        negative_template="A moderate backlog severity category is contributing negatively. Clearing backlogs would improve this signal.",
        parent_group="backlog_severity_category",
        ohe_value="MODERATE",
    ),
    "enc_backlog_severity_category_NONE": FeatureDisplayInfo(
        display_name="Backlog Severity (None)",
        description="One-hot encoded backlog severity classification",
        unit="",
        higher_is_better=True,
        positive_template="Having no backlogs is contributing positively. A clean academic record is strongly associated with better outcomes.",
        negative_template="The absence of the 'None' backlog category implies you have active backlogs, contributing negatively.",
        parent_group="backlog_severity_category",
        ohe_value="NONE",
    ),
    "enc_backlog_severity_category_SEVERE": FeatureDisplayInfo(
        display_name="Backlog Severity (Severe)",
        description="One-hot encoded backlog severity classification",
        unit="",
        higher_is_better=False,
        positive_template="A severe backlog classification here has an unusual positive signal (likely offset by other factors). Review raw backlog count.",
        negative_template="A severe backlog classification is one of the strongest negative factors. The model associates severe backlogs with significantly worse outcomes.",
        parent_group="backlog_severity_category",
        ohe_value="SEVERE",
    ),
}


def get_feature_info(feature_name: str) -> FeatureDisplayInfo:
    """Returns display info for a feature. Falls back to a generic entry if not found."""
    if feature_name in FEATURE_DISPLAY_CATALOG:
        return FEATURE_DISPLAY_CATALOG[feature_name]
    # Generic fallback for any unexpected feature names
    return FeatureDisplayInfo(
        display_name=feature_name.replace("_", " ").title(),
        description=f"Model feature: {feature_name}",
        unit="",
        higher_is_better=True,
        positive_template=f"The feature '{feature_name}' has a positive influence on this prediction.",
        negative_template=f"The feature '{feature_name}' has a negative influence on this prediction.",
    )


def get_demographic_features() -> List[str]:
    """Returns list of all demographic feature names for fairness disclosure."""
    return [name for name, info in FEATURE_DISPLAY_CATALOG.items() if info.is_demographic]


GLOBAL_FAIRNESS_NOTE = (
    "This prediction is generated by a machine learning model trained on historical academic data. "
    "Demographic features (gender, age, department) reflect statistical patterns in the training data "
    "and do not represent any judgment about individual ability or potential. "
    "These predictions are advisory only and should be reviewed by an academic advisor before "
    "making any academic decisions."
)
