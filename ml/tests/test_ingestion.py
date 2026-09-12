"""
Tests for Data Ingestion and Dataset Adapters.
"""

import tempfile
from pathlib import Path
import pandas as pd
import pytest

from ml.config.pipeline_config import CANONICAL_COLUMNS, SCHEMA
from ml.pipelines.ingestion import (
    UCIStudentPerformanceAdapter,
    compute_file_sha256,
    generate_manifest,
    load_canonical_csv,
)


def test_load_canonical_csv(tmp_path):
    sample_data = {
        SCHEMA.STUDENT_ID: ["2023cs001"],
        SCHEMA.NAME: ["Test Student"],
        SCHEMA.GENDER: ["FEMALE"],
        SCHEMA.AGE: [20],
        SCHEMA.DEPARTMENT: ["CS"],
        SCHEMA.SEMESTER: [1],
        SCHEMA.ACADEMIC_YEAR: ["2023-2024"],
        SCHEMA.ATTENDANCE: [85.0],
        SCHEMA.PREVIOUS_CGPA: [8.5],
        SCHEMA.MID_1: [80.0],
        SCHEMA.MID_2: [82.0],
        SCHEMA.INTERNAL_MARKS: [85.0],
        SCHEMA.BACKLOGS: [0],
        SCHEMA.TARGET_CGPA: [8.6],
    }
    df = pd.DataFrame(sample_data)
    csv_file = tmp_path / "sample.csv"
    df.to_csv(csv_file, index=False)

    loaded_df = load_canonical_csv(csv_file)
    assert len(loaded_df) == 1
    assert loaded_df[SCHEMA.STUDENT_ID].iloc[0] == "2023cs001"
    assert loaded_df[SCHEMA.ATTENDANCE].iloc[0] == 85.0


def test_uci_student_adapter():
    uci_raw = pd.DataFrame({
        "school": ["GP", "MS"],
        "sex": ["F", "M"],
        "age": [16, 17],
        "studytime": [2, 3],
        "failures": [0, 1],
        "absences": [4, 10],
        "G1": [15, 10],
        "G2": [14, 11],
        "G3": [16, 11],
    })
    
    adapter = UCIStudentPerformanceAdapter()
    canonical_df = adapter.adapt(uci_raw)
    
    # Assert canonical columns exist
    assert SCHEMA.GENDER in canonical_df.columns
    assert canonical_df[SCHEMA.GENDER].tolist() == ["FEMALE", "MALE"]
    
    # Assert scaling from 0-20 to 0-100 / 0-10
    # G1=15 -> Mid 1 = 75.0, G1=10 -> Mid 1 = 50.0
    assert canonical_df[SCHEMA.MID_1].tolist() == [75.0, 50.0]
    
    # G3=16 -> Target CGPA = 8.0, G3=11 -> Target CGPA = 5.5
    assert canonical_df[SCHEMA.TARGET_CGPA].tolist() == [8.0, 5.5]
    
    # Absences 4 -> Attendance 96.0%, Absences 10 -> Attendance 90.0%
    assert canonical_df[SCHEMA.ATTENDANCE].tolist() == [96.0, 90.0]


def test_dataset_manifest_creation(tmp_path):
    df = pd.DataFrame({col: [1] for col in CANONICAL_COLUMNS})
    sample_csv = tmp_path / "manifest_test.csv"
    df.to_csv(sample_csv, index=False)

    manifest = generate_manifest(
        df=df,
        source_name="Test_Dataset",
        source_type="CSV",
        source_path=str(sample_csv),
        output_dir=tmp_path,
    )
    
    assert manifest.dataset_name == "Test_Dataset"
    assert manifest.record_count == 1
    assert manifest.is_canonical is True
    assert len(manifest.sha256_hash) == 64
    assert (tmp_path / "dataset_manifest.json").exists()
