"""
Tests for Dataset Splitters (StudentTemporalSplitter & StudentGroupSplitter).
"""

import pandas as pd
import pytest

from ml.config.pipeline_config import SCHEMA, PipelineConfig
from ml.pipelines.splitter import (
    StudentGroupSplitter,
    StudentTemporalSplitter,
    SplitStrategyType,
)


@pytest.fixture
def multi_student_cohort():
    # 20 students, each with semesters 1 to 6
    records = []
    for i in range(1, 21):
        stu_id = f"2023cs{i:03d}"
        for sem in range(1, 7):
            records.append({
                SCHEMA.STUDENT_ID: stu_id,
                SCHEMA.NAME: f"Student {i}",
                SCHEMA.SEMESTER: sem,
                SCHEMA.ACADEMIC_YEAR: "2023-2024",
                SCHEMA.ATTENDANCE: 80.0,
                SCHEMA.PREVIOUS_CGPA: 8.0,
                SCHEMA.MID_1: 75.0,
                SCHEMA.MID_2: 78.0,
                SCHEMA.INTERNAL_MARKS: 80.0,
                SCHEMA.BACKLOGS: 0,
                SCHEMA.TARGET_CGPA: 8.2,
            })
    return pd.DataFrame(records)


def test_student_group_splitter_zero_crossover(multi_student_cohort):
    config = PipelineConfig(split_strategy=SplitStrategyType.STUDENT_GROUP.value, test_size=0.2, val_size=0.2)
    splitter = StudentGroupSplitter(config)
    result = splitter.split(multi_student_cohort)

    # Assert 0 student crossover
    assert result.student_crossover_detected == 0

    students_train = set(result.train_df[SCHEMA.STUDENT_ID])
    students_val = set(result.val_df[SCHEMA.STUDENT_ID])
    students_test = set(result.test_df[SCHEMA.STUDENT_ID])

    assert len(students_train.intersection(students_val)) == 0
    assert len(students_train.intersection(students_test)) == 0
    assert len(students_val.intersection(students_test)) == 0


def test_student_temporal_splitter_chronological_ordering(multi_student_cohort):
    config = PipelineConfig(split_strategy=SplitStrategyType.STUDENT_TEMPORAL.value)
    splitter = StudentTemporalSplitter(config)
    result = splitter.split(multi_student_cohort)

    # Semesters 1-4 in train, Sem 5 in val, Sem 6 in test
    train_max_sem = result.train_df[SCHEMA.SEMESTER].max()
    val_min_sem = result.val_df[SCHEMA.SEMESTER].min()
    val_max_sem = result.val_df[SCHEMA.SEMESTER].max()
    test_min_sem = result.test_df[SCHEMA.SEMESTER].min()

    assert train_max_sem <= val_min_sem
    assert val_max_sem <= test_min_sem
    assert result.temporal_violations_detected == 0
