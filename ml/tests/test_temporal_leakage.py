"""
Critical Temporal Leakage and Future-Poisoning Canary Tests.

Validates:
1. Future Poisoning Canary Test: Proves mathematically that injecting extreme
   canary/poison values into future semesters (t+1, t+2) or future targets
   has zero impact on features computed for semester t.
2. Target Invariance: Proves that changing semester t's target semester_cgpa
   never alters any input or engineered feature for semester t.
3. Directional Chronological Integrity: Modifying past semester t-1 alters semester t,
   but modifying semester t NEVER alters semester t-1.
"""

import numpy as np
import pandas as pd
import pytest

from ml.config.pipeline_config import (
    FEATURE_ACADEMIC_AVG,
    FEATURE_ACADEMIC_STABILITY,
    FEATURE_ATTENDANCE_RISK,
    FEATURE_INTERNAL_AVG,
    FEATURE_MID_TERM_AVG,
    FEATURE_PREV_CGPA_TREND,
    FEATURE_BACKLOG_SEVERITY,
    SCHEMA,
)
from ml.pipelines.engineering import FeatureEngineer


@pytest.fixture
def clean_longitudinal_cohort():
    return pd.DataFrame({
        SCHEMA.STUDENT_ID: ["stu_01", "stu_01", "stu_01", "stu_01"],
        SCHEMA.SEMESTER: [1, 2, 3, 4],
        SCHEMA.ACADEMIC_YEAR: ["2022-2023", "2022-2023", "2023-2024", "2023-2024"],
        SCHEMA.ATTENDANCE: [88.0, 84.0, 80.0, 82.0],
        SCHEMA.PREVIOUS_CGPA: [8.50, 8.60, 8.75, 8.70],
        SCHEMA.MID_1: [80.0, 82.0, 85.0, 84.0],
        SCHEMA.MID_2: [82.0, 84.0, 86.0, 85.0],
        SCHEMA.INTERNAL_MARKS: [85.0, 86.0, 88.0, 87.0],
        SCHEMA.BACKLOGS: [0, 0, 0, 0],
        SCHEMA.TARGET_CGPA: [8.60, 8.75, 8.70, 8.85],
    })


def test_canary_future_poisoning_does_not_affect_past_features(clean_longitudinal_cohort):
    engineer = FeatureEngineer()
    
    # Baseline transformation
    baseline_df = engineer.transform(clean_longitudinal_cohort)
    
    # Create poisoned copy: Inject extreme poison/canary values into Semesters 3 and 4
    poisoned_cohort = clean_longitudinal_cohort.copy()
    
    # Poison Semester 3 target
    poisoned_cohort.loc[2, SCHEMA.TARGET_CGPA] = 0.00
    
    # Poison Semester 4 completely (future features & future targets)
    poisoned_cohort.loc[3, SCHEMA.ATTENDANCE] = 0.00
    poisoned_cohort.loc[3, SCHEMA.PREVIOUS_CGPA] = 0.00
    poisoned_cohort.loc[3, SCHEMA.MID_1] = 0.00
    poisoned_cohort.loc[3, SCHEMA.MID_2] = 0.00
    poisoned_cohort.loc[3, SCHEMA.INTERNAL_MARKS] = 0.00
    poisoned_cohort.loc[3, SCHEMA.BACKLOGS] = 50
    poisoned_cohort.loc[3, SCHEMA.TARGET_CGPA] = 0.00

    poisoned_transformed = engineer.transform(poisoned_cohort)

    # 1. Assert Semester 1 features are 100% bit-for-bit invariant
    sem1_base = baseline_df.iloc[0][[FEATURE_ACADEMIC_AVG, FEATURE_ATTENDANCE_RISK, FEATURE_PREV_CGPA_TREND, FEATURE_ACADEMIC_STABILITY]]
    sem1_pois = poisoned_transformed.iloc[0][[FEATURE_ACADEMIC_AVG, FEATURE_ATTENDANCE_RISK, FEATURE_PREV_CGPA_TREND, FEATURE_ACADEMIC_STABILITY]]
    pd.testing.assert_series_equal(sem1_base, sem1_pois, obj="Semester 1 Feature Invariance")

    # 2. Assert Semester 2 features are 100% bit-for-bit invariant
    sem2_base = baseline_df.iloc[1][[FEATURE_ACADEMIC_AVG, FEATURE_ATTENDANCE_RISK, FEATURE_PREV_CGPA_TREND, FEATURE_ACADEMIC_STABILITY]]
    sem2_pois = poisoned_transformed.iloc[1][[FEATURE_ACADEMIC_AVG, FEATURE_ATTENDANCE_RISK, FEATURE_PREV_CGPA_TREND, FEATURE_ACADEMIC_STABILITY]]
    pd.testing.assert_series_equal(sem2_base, sem2_pois, obj="Semester 2 Feature Invariance")

    # 3. Assert Semester 3 historical features (Trend and Stability) are 100% bit-for-bit invariant
    assert baseline_df.loc[2, FEATURE_PREV_CGPA_TREND] == poisoned_transformed.loc[2, FEATURE_PREV_CGPA_TREND]
    assert baseline_df.loc[2, FEATURE_ACADEMIC_STABILITY] == poisoned_transformed.loc[2, FEATURE_ACADEMIC_STABILITY]


def test_target_semester_cgpa_invariance(clean_longitudinal_cohort):
    """Proves that changing current target semester_cgpa has zero effect on any feature in that semester."""
    engineer = FeatureEngineer()
    
    df1 = clean_longitudinal_cohort.copy()
    df1.loc[1, SCHEMA.TARGET_CGPA] = 9.99
    
    df2 = clean_longitudinal_cohort.copy()
    df2.loc[1, SCHEMA.TARGET_CGPA] = 1.00

    res1 = engineer.transform(df1)
    res2 = engineer.transform(df2)

    features_to_check = [
        FEATURE_ACADEMIC_AVG,
        FEATURE_ATTENDANCE_RISK,
        FEATURE_INTERNAL_AVG,
        FEATURE_MID_TERM_AVG,
        FEATURE_PREV_CGPA_TREND,
        FEATURE_BACKLOG_SEVERITY,
        FEATURE_ACADEMIC_STABILITY,
    ]

    # Row 1 features must be exactly identical despite completely opposite targets
    pd.testing.assert_series_equal(res1.loc[1, features_to_check], res2.loc[1, features_to_check])


def test_reverse_time_directional_integrity(clean_longitudinal_cohort):
    """Modifying Semester 1 alters Semester 2 trend, but modifying Semester 2 NEVER alters Semester 1."""
    engineer = FeatureEngineer()
    base_res = engineer.transform(clean_longitudinal_cohort)
    
    # 1. Modify Semester 2: Verify Semester 1 is unchanged
    mod_sem2 = clean_longitudinal_cohort.copy()
    mod_sem2.loc[1, SCHEMA.PREVIOUS_CGPA] = 5.00  # drastically alter sem 2
    res_mod_sem2 = engineer.transform(mod_sem2)

    # Semester 1 features MUST remain identical
    assert res_mod_sem2.loc[0, FEATURE_PREV_CGPA_TREND] == base_res.loc[0, FEATURE_PREV_CGPA_TREND]
    assert res_mod_sem2.loc[0, FEATURE_ACADEMIC_STABILITY] == base_res.loc[0, FEATURE_ACADEMIC_STABILITY]

    # 2. Modify Semester 1: Verify Semester 2 trend DOES change (forward causality)
    mod_sem1 = clean_longitudinal_cohort.copy()
    mod_sem1.loc[0, SCHEMA.PREVIOUS_CGPA] = 5.00  # alter past baseline
    res_mod_sem1 = engineer.transform(mod_sem1)

    # Semester 2 trend must reflect the new baseline
    # Original sem 2 delta: 8.60 - 8.50 = +0.10
    # New sem 2 delta: 8.60 - 5.00 = +3.60
    assert res_mod_sem1.loc[1, FEATURE_PREV_CGPA_TREND] != base_res.loc[1, FEATURE_PREV_CGPA_TREND]
    assert res_mod_sem1.loc[1, FEATURE_PREV_CGPA_TREND] == 3.60
