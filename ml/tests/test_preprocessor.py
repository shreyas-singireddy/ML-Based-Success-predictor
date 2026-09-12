"""
Tests for Preprocessor Pipeline (Fit Isolation, Unseen Categories, Persistence).
"""

import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from ml.config.pipeline_config import (
    FEATURE_ACADEMIC_AVG,
    FEATURE_ACADEMIC_STABILITY,
    FEATURE_ATTENDANCE_RISK,
    FEATURE_ATTENDANCE_RISK_CAT,
    FEATURE_INTERNAL_AVG,
    FEATURE_MID_TERM_AVG,
    FEATURE_PREV_CGPA_TREND,
    FEATURE_BACKLOG_SEVERITY,
    FEATURE_BACKLOG_SEVERITY_CAT,
    SCHEMA,
)
from ml.pipelines.preprocessor import AcademicPreprocessor


@pytest.fixture
def train_and_test_data():
    train_df = pd.DataFrame({
        SCHEMA.STUDENT_ID: ["s1", "s2", "s3", "s4"],
        SCHEMA.NAME: ["A", "B", "C", "D"],
        SCHEMA.GENDER: ["FEMALE", "MALE", "FEMALE", "MALE"],
        SCHEMA.AGE: [19, 20, 21, 20],
        SCHEMA.DEPARTMENT: ["CS", "IT", "ECE", "CS"],
        SCHEMA.SEMESTER: [1, 2, 3, 4],
        SCHEMA.ACADEMIC_YEAR: ["2023-2024"] * 4,
        SCHEMA.ATTENDANCE: [85.0, 90.0, 75.0, 60.0],
        SCHEMA.PREVIOUS_CGPA: [8.5, 7.8, 8.0, 6.5],
        SCHEMA.MID_1: [80.0, 75.0, 70.0, 50.0],
        SCHEMA.MID_2: [82.0, 78.0, 72.0, 55.0],
        SCHEMA.INTERNAL_MARKS: [85.0, 80.0, 75.0, 60.0],
        SCHEMA.BACKLOGS: [0, 0, 1, 3],
        FEATURE_ACADEMIC_AVG: [82.33, 77.67, 72.33, 55.0],
        FEATURE_ATTENDANCE_RISK: [0.0, 0.0, 0.0, 0.2],
        FEATURE_ATTENDANCE_RISK_CAT: ["NORMAL", "NORMAL", "NORMAL", "CRITICAL"],
        FEATURE_INTERNAL_AVG: [0.85, 0.80, 0.75, 0.60],
        FEATURE_MID_TERM_AVG: [81.0, 76.5, 71.0, 52.5],
        FEATURE_PREV_CGPA_TREND: [0.0, 0.1, -0.2, -0.5],
        FEATURE_BACKLOG_SEVERITY: [0.0, 0.0, 0.2, 0.6],
        FEATURE_BACKLOG_SEVERITY_CAT: ["NONE", "NONE", "MODERATE", "SEVERE"],
        FEATURE_ACADEMIC_STABILITY: [0.0, 0.0, 0.15, 0.25],
        SCHEMA.TARGET_CGPA: [8.6, 8.0, 7.9, 6.2],
    })

    # Inference data with completely UNSEEN categories (e.g. DEPARTMENT="AEROSPACE", GENDER="NONBINARY")
    test_df = pd.DataFrame({
        SCHEMA.STUDENT_ID: ["s99"],
        SCHEMA.NAME: ["Unseen Student"],
        SCHEMA.GENDER: ["NONBINARY"],  # Unseen
        SCHEMA.AGE: [22],
        SCHEMA.DEPARTMENT: ["AEROSPACE"],  # Unseen
        SCHEMA.SEMESTER: [5],
        SCHEMA.ACADEMIC_YEAR: ["2024-2025"],
        SCHEMA.ATTENDANCE: [80.0],
        SCHEMA.PREVIOUS_CGPA: [7.5],
        SCHEMA.MID_1: [70.0],
        SCHEMA.MID_2: [72.0],
        SCHEMA.INTERNAL_MARKS: [75.0],
        SCHEMA.BACKLOGS: [0],
        FEATURE_ACADEMIC_AVG: [72.33],
        FEATURE_ATTENDANCE_RISK: [0.0],
        FEATURE_ATTENDANCE_RISK_CAT: ["NORMAL"],
        FEATURE_INTERNAL_AVG: [0.75],
        FEATURE_MID_TERM_AVG: [71.0],
        FEATURE_PREV_CGPA_TREND: [0.0],
        FEATURE_BACKLOG_SEVERITY: [0.0],
        FEATURE_BACKLOG_SEVERITY_CAT: ["NONE"],
        FEATURE_ACADEMIC_STABILITY: [0.0],
        SCHEMA.TARGET_CGPA: [7.8],
    })

    return train_df, test_df


def test_preprocessor_fit_and_unseen_categories(train_and_test_data):
    train_df, test_df = train_and_test_data
    preprocessor = AcademicPreprocessor()

    X_train, y_train = preprocessor.extract_features_and_target(train_df)
    X_test, y_test = preprocessor.extract_features_and_target(test_df)

    # Assert target is completely removed from X
    assert SCHEMA.TARGET_CGPA not in X_train.columns
    assert SCHEMA.TARGET_CGPA not in X_test.columns
    assert SCHEMA.STUDENT_ID not in X_train.columns

    # Fit on train
    preprocessor.fit(X_train)
    assert preprocessor.is_fitted is True

    # Transform train and test
    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)

    # Assert exact column matching and zero NaN values produced
    assert list(X_train_trans.columns) == list(X_test_trans.columns)
    assert X_test_trans.isna().sum().sum() == 0


def test_preprocessor_serialization(train_and_test_data, tmp_path):
    train_df, test_df = train_and_test_data
    preprocessor = AcademicPreprocessor()

    X_train, _ = preprocessor.extract_features_and_target(train_df)
    X_test, _ = preprocessor.extract_features_and_target(test_df)

    preprocessor.fit(X_train)
    original_test_trans = preprocessor.transform(X_test)

    # Save to disk
    joblib_file = tmp_path / "test_preprocessor.joblib"
    preprocessor.save(joblib_file)

    # Load from disk
    loaded_preprocessor = AcademicPreprocessor.load(joblib_file)
    loaded_test_trans = loaded_preprocessor.transform(X_test)

    # Assert bit-for-bit equivalence
    pd.testing.assert_frame_equal(original_test_trans, loaded_test_trans)
