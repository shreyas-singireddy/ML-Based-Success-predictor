"""
Tests for Data Validation Module.
"""

import pandas as pd
import pytest

from ml.config.pipeline_config import CANONICAL_COLUMNS, SCHEMA
from ml.pipelines.validation import DataValidator, ValidationSeverity


@pytest.fixture
def valid_dataframe():
    return pd.DataFrame({
        SCHEMA.STUDENT_ID: ["2023cs001", "2023cs002"],
        SCHEMA.NAME: ["Alice Smith", "Bob Jones"],
        SCHEMA.GENDER: ["FEMALE", "MALE"],
        SCHEMA.AGE: [19, 20],
        SCHEMA.DEPARTMENT: ["CS", "IT"],
        SCHEMA.SEMESTER: [1, 2],
        SCHEMA.ACADEMIC_YEAR: ["2023-2024", "2023-2024"],
        SCHEMA.ATTENDANCE: [85.0, 92.5],
        SCHEMA.PREVIOUS_CGPA: [8.5, 7.8],
        SCHEMA.MID_1: [75.0, 80.0],
        SCHEMA.MID_2: [78.0, 82.0],
        SCHEMA.INTERNAL_MARKS: [80.0, 85.0],
        SCHEMA.BACKLOGS: [0, 1],
        SCHEMA.TARGET_CGPA: [8.4, 8.0],
    })


def test_valid_dataset_passes_validation(valid_dataframe):
    validator = DataValidator()
    result = validator.validate(valid_dataframe)
    assert result.is_valid is True
    assert result.valid_records_count == 2
    assert result.invalid_records_count == 0
    assert len(result.issues) == 0


def test_missing_required_columns_fails(valid_dataframe):
    corrupt_df = valid_dataframe.drop(columns=[SCHEMA.ATTENDANCE, SCHEMA.PREVIOUS_CGPA])
    validator = DataValidator()
    result = validator.validate(corrupt_df)
    assert result.is_valid is False
    assert any(i.issue_type == "missing_columns" for i in result.issues)


def test_numeric_boundary_violations(valid_dataframe):
    corrupt_df = valid_dataframe.copy()
    corrupt_df.loc[0, SCHEMA.ATTENDANCE] = 120.0  # > 100%
    corrupt_df.loc[1, SCHEMA.PREVIOUS_CGPA] = -1.0  # < 0

    validator = DataValidator()
    result = validator.validate(corrupt_df)
    assert result.is_valid is False
    assert result.invalid_records_count == 2
    oob_issues = [i for i in result.issues if i.issue_type == "out_of_bounds"]
    assert len(oob_issues) >= 2


def test_logical_duplicate_records(valid_dataframe):
    # Duplicate student_number + semester combination
    corrupt_df = pd.concat([valid_dataframe, valid_dataframe.iloc[[0]]], ignore_index=True)
    validator = DataValidator()
    result = validator.validate(corrupt_df)
    assert result.is_valid is False
    assert any(i.issue_type == "logical_duplicate" for i in result.issues)


def test_missing_target_detection(valid_dataframe):
    corrupt_df = valid_dataframe.copy()
    corrupt_df.loc[0, SCHEMA.TARGET_CGPA] = None

    validator = DataValidator(require_target=True)
    result = validator.validate(corrupt_df)
    assert result.is_valid is False
    assert any(i.issue_type == "missing_target" for i in result.issues)
