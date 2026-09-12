"""
Tests for Feature Engineering Formulas and Edge Cases.
"""

import pandas as pd
import pytest

from ml.config.pipeline_config import (
    FEATURE_ACADEMIC_AVG,
    FEATURE_ATTENDANCE_RISK,
    FEATURE_ATTENDANCE_RISK_CAT,
    FEATURE_INTERNAL_AVG,
    FEATURE_MID_TERM_AVG,
    FEATURE_PREV_CGPA_TREND,
    FEATURE_BACKLOG_SEVERITY,
    FEATURE_BACKLOG_SEVERITY_CAT,
    FEATURE_ACADEMIC_STABILITY,
    SCHEMA,
)
from ml.pipelines.engineering import FeatureEngineer


@pytest.fixture
def multi_semester_student():
    # 4 consecutive semesters for a single student
    return pd.DataFrame({
        SCHEMA.STUDENT_ID: ["s1", "s1", "s1", "s1"],
        SCHEMA.SEMESTER: [1, 2, 3, 4],
        SCHEMA.ACADEMIC_YEAR: ["2022-2023", "2022-2023", "2023-2024", "2023-2024"],
        SCHEMA.ATTENDANCE: [90.0, 70.0, 60.0, 80.0],
        SCHEMA.PREVIOUS_CGPA: [8.0, 8.2, 8.5, 8.1],
        SCHEMA.MID_1: [80.0, 60.0, 50.0, 70.0],
        SCHEMA.MID_2: [82.0, 64.0, 52.0, 72.0],
        SCHEMA.INTERNAL_MARKS: [84.0, 62.0, 54.0, 74.0],
        SCHEMA.BACKLOGS: [0, 1, 3, 0],
        SCHEMA.TARGET_CGPA: [8.2, 8.5, 8.1, 8.6],
    })


def test_feature_engineering_formulas(multi_semester_student):
    engineer = FeatureEngineer()
    res = engineer.transform(multi_semester_student)

    # 1. Academic Average: (80 + 82 + 84)/3 = 82.0
    assert res[FEATURE_ACADEMIC_AVG].iloc[0] == 82.0

    # 2. Attendance Risk Category:
    # Row 0 (90%) -> NORMAL
    # Row 1 (70%) -> AT_RISK
    # Row 2 (60%) -> CRITICAL
    assert res[FEATURE_ATTENDANCE_RISK_CAT].tolist() == ["NORMAL", "AT_RISK", "CRITICAL", "NORMAL"]

    # 3. Internal Average: 84 / 100 = 0.84
    assert res[FEATURE_INTERNAL_AVG].iloc[0] == 0.84

    # 4. Mid-Term Average: (80 + 82)/2 = 81.0
    assert res[FEATURE_MID_TERM_AVG].iloc[0] == 81.0

    # 5. Backlog Severity Category:
    # 0 -> NONE, 1 -> MODERATE, 3 -> SEVERE
    assert res[FEATURE_BACKLOG_SEVERITY_CAT].tolist() == ["NONE", "MODERATE", "SEVERE", "NONE"]

    # 6. Previous CGPA Trend:
    # Sem 1: 0.0 (initial)
    # Sem 2: 8.2 - 8.0 = +0.2
    # Sem 3: 8.5 - 8.2 = +0.3
    # Sem 4: 8.1 - 8.5 = -0.4
    assert res[FEATURE_PREV_CGPA_TREND].iloc[0] == 0.0
    assert res[FEATURE_PREV_CGPA_TREND].iloc[1] == 0.2
    assert res[FEATURE_PREV_CGPA_TREND].iloc[2] == 0.3
    assert res[FEATURE_PREV_CGPA_TREND].iloc[3] == -0.4

    # 7. Academic Stability:
    # Sem 1: 0.0
    # Sem 2: 0.0
    # Sem 3: std([8.0, 8.2, 8.5])
    # Sem 4: std([8.0, 8.2, 8.5, 8.1])
    assert res[FEATURE_ACADEMIC_STABILITY].iloc[0] == 0.0
    assert res[FEATURE_ACADEMIC_STABILITY].iloc[1] == 0.0
    assert res[FEATURE_ACADEMIC_STABILITY].iloc[2] > 0.0
    assert res[FEATURE_ACADEMIC_STABILITY].iloc[3] > 0.0
