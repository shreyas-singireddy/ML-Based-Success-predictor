"""
Tests for Data Cleaning and Imputation Module.
"""

import pandas as pd
import pytest

from ml.config.pipeline_config import SCHEMA
from ml.pipelines.cleaning import DataCleaner


@pytest.fixture
def messy_dataframe():
    return pd.DataFrame({
        SCHEMA.STUDENT_ID: ["2023cs001", "2023cs001", "2023cs002", "2023cs003"],
        SCHEMA.NAME: ["Alice", "Alice", "Bob", "Charlie"],
        SCHEMA.GENDER: ["FEMALE", "FEMALE", None, "MALE"],
        SCHEMA.AGE: [19, 19, 20, 21],
        SCHEMA.DEPARTMENT: ["CS", "CS", "IT", None],
        SCHEMA.SEMESTER: [1, 1, 1, 2],  # Note row 0 & 1 are logical duplicates (same student + semester)
        SCHEMA.ACADEMIC_YEAR: ["2023-2024", "2023-2024", "2023-2024", "2023-2024"],
        SCHEMA.ATTENDANCE: [85.0, 85.0, None, 110.0],  # row 2 has missing att, row 3 has oob > 100
        SCHEMA.PREVIOUS_CGPA: [8.5, 8.5, 7.5, 6.0],
        SCHEMA.MID_1: [75.0, 75.0, None, 80.0],
        SCHEMA.MID_2: [78.0, 78.0, 70.0, 85.0],
        SCHEMA.INTERNAL_MARKS: [80.0, 80.0, 75.0, None],
        SCHEMA.BACKLOGS: [0, 0, 1, -2],  # row 3 has negative backlogs
        SCHEMA.TARGET_CGPA: [8.4, 8.4, 7.8, None],  # row 3 missing target
    })


def test_cleaner_deduplication_and_target_exclusion(messy_dataframe):
    cleaner = DataCleaner()
    cleaned_df, meta = cleaner.clean(messy_dataframe, is_training=True)

    # Initial 4 rows -> 1 duplicate removed, 1 missing target removed -> 2 rows remain
    assert len(cleaned_df) == 2
    assert meta.exact_duplicates_removed == 1 or meta.logical_duplicates_resolved == 1
    assert meta.missing_target_rows_removed == 1
    assert cleaned_df[SCHEMA.STUDENT_ID].tolist() == ["2023cs001", "2023cs002"]


def test_cleaner_domain_clipping(messy_dataframe):
    cleaner = DataCleaner()
    # Test on non-training mode so row with missing target is kept
    cleaned_df, meta = cleaner.clean(messy_dataframe, is_training=False)

    # Row with attendance 110.0 should be clipped to 100.0
    charlie_att = cleaned_df[cleaned_df[SCHEMA.STUDENT_ID] == "2023cs003"][SCHEMA.ATTENDANCE].iloc[0]
    assert charlie_att == 100.0

    # Row with backlogs -2 should be clipped to 0
    charlie_backlogs = cleaned_df[cleaned_df[SCHEMA.STUDENT_ID] == "2023cs003"][SCHEMA.BACKLOGS].iloc[0]
    assert charlie_backlogs == 0


def test_cleaner_imputation_values():
    train_df = pd.DataFrame({
        SCHEMA.STUDENT_ID: ["s1", "s2", "s3"],
        SCHEMA.SEMESTER: [1, 2, 3],
        SCHEMA.ATTENDANCE: [80.0, 90.0, 100.0],  # Median = 90.0
        SCHEMA.MID_1: [60.0, 70.0, 80.0],       # Median = 70.0
        SCHEMA.TARGET_CGPA: [7.0, 8.0, 9.0],
    })
    test_df = pd.DataFrame({
        SCHEMA.STUDENT_ID: ["s4"],
        SCHEMA.SEMESTER: [1],
        SCHEMA.ATTENDANCE: [None],
        SCHEMA.MID_1: [None],
        SCHEMA.TARGET_CGPA: [8.0],
    })

    cleaner = DataCleaner()
    cleaner.fit(train_df)
    
    assert cleaner.fitted_medians[SCHEMA.ATTENDANCE] == 90.0
    assert cleaner.fitted_medians[SCHEMA.MID_1] == 70.0

    # Transform test_df using fitted statistics
    cleaned_test, meta = cleaner.clean(test_df, is_training=False)
    assert cleaned_test[SCHEMA.ATTENDANCE].iloc[0] == 90.0
    assert cleaned_test[SCHEMA.MID_1].iloc[0] == 70.0
