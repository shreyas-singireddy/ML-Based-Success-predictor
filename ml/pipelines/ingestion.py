"""
Data Ingestion and Dataset Adapters for ML Pipeline.

Provides mechanisms to load academic datasets from:
1. Canonical CSV format
2. Relational Database (SQLAlchemy StudentProfile + AcademicRecord)
3. Public Benchmark Datasets via Adapters (e.g. UCI Student Performance)

Generates dataset manifest capturing provenance, record counts, and schema mappings.
"""

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from ml.config.pipeline_config import (
    SCHEMA,
    CANONICAL_COLUMNS,
    DEFAULT_CONFIG,
    REPORTS_DIR,
)


@dataclass
class DatasetManifest:
    dataset_name: str
    source_type: str
    source_path: str
    record_count: int
    column_count: int
    sha256_hash: str
    columns_original: List[str]
    columns_mapped: Dict[str, str]
    columns_dropped: List[str]
    created_at_utc: str
    is_canonical: bool


class DatasetAdapter:
    """Base class for transforming third-party academic datasets to canonical schema."""
    
    def __init__(self, name: str):
        self.name = name
        self.column_mapping: Dict[str, str] = {}
        self.dropped_columns: List[str] = []
        
    def adapt(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError("Subclasses must implement adapt()")


class UCIStudentPerformanceAdapter(DatasetAdapter):
    """
    Adapter for UCI Student Performance dataset (student-mat.csv / student-por.csv).
    Maps secondary/tertiary performance columns (G1, G2, G3, absences, studytime)
    to the canonical academic schema.
    """
    
    def __init__(self):
        super().__init__(name="UCI_Student_Performance")
        self.column_mapping = {
            "sex": SCHEMA.GENDER,
            "age": SCHEMA.AGE,
            "school": SCHEMA.DEPARTMENT,
            "G1": SCHEMA.MID_1,
            "G2": SCHEMA.MID_2,
            "G3": SCHEMA.TARGET_CGPA,
            "failures": SCHEMA.BACKLOGS,
        }
        
    def adapt(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        df = raw_df.copy()
        original_cols = list(df.columns)
        
        # Gender mapping
        if "sex" in df.columns:
            df[SCHEMA.GENDER] = df["sex"].map({"M": "MALE", "F": "FEMALE"}).fillna("OTHER")
        else:
            df[SCHEMA.GENDER] = "OTHER"
            
        # Age
        df[SCHEMA.AGE] = pd.to_numeric(df.get("age", 18), errors="coerce").fillna(18)
        
        # Department fallback
        df[SCHEMA.DEPARTMENT] = df.get("school", "CS").astype(str).str.upper()
        
        # Attendance: UCI has absences (0-93). Normalize to attendance percentage.
        # Assuming ~100 total class sessions per semester: attendance = max(0, 100 - absences)
        if "absences" in df.columns:
            df[SCHEMA.ATTENDANCE] = (100.0 - df["absences"].clip(lower=0, upper=100)).round(2)
        else:
            df[SCHEMA.ATTENDANCE] = 85.0
            
        # Marks: UCI G1, G2, G3 are scored 0-20. Scale to 0-100 marks / 0-10 CGPA.
        if "G1" in df.columns:
            df[SCHEMA.MID_1] = (df["G1"].clip(0, 20) * 5.0).round(2)
        else:
            df[SCHEMA.MID_1] = 60.0
            
        if "G2" in df.columns:
            df[SCHEMA.MID_2] = (df["G2"].clip(0, 20) * 5.0).round(2)
        else:
            df[SCHEMA.MID_2] = 60.0
            
        # Internal marks approximation from studytime (1-4) and paid/freetime
        df[SCHEMA.INTERNAL_MARKS] = (df.get("studytime", 2).clip(1, 4) * 20.0 + 20.0).round(2)
        
        # Backlogs from failures
        df[SCHEMA.BACKLOGS] = pd.to_numeric(df.get("failures", 0), errors="coerce").fillna(0).astype(int)
        
        # Target CGPA (G3 scaled 0-20 -> 0-10)
        if "G3" in df.columns:
            df[SCHEMA.TARGET_CGPA] = (df["G3"].clip(0, 20) / 2.0).round(2)
        else:
            df[SCHEMA.TARGET_CGPA] = 7.0
            
        # Previous CGPA (Derived from G1 or baseline)
        df[SCHEMA.PREVIOUS_CGPA] = (df[SCHEMA.MID_1] / 10.0).round(2)
        
        # Identifiers
        df[SCHEMA.STUDENT_ID] = [f"UCI_{i:04d}" for i in range(1, len(df) + 1)]
        df[SCHEMA.NAME] = [f"Student_{i:04d}" for i in range(1, len(df) + 1)]
        df[SCHEMA.SEMESTER] = 1
        df[SCHEMA.ACADEMIC_YEAR] = "2023-2024"
        
        self.dropped_columns = [c for c in original_cols if c not in self.column_mapping.keys() and c not in df.columns]
        
        # Select canonical columns
        canonical_cols_present = [c for c in CANONICAL_COLUMNS if c in df.columns]
        return df[canonical_cols_present].copy()


def compute_file_sha256(filepath: Union[str, Path]) -> str:
    """Calculates SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_canonical_csv(filepath: Union[str, Path]) -> pd.DataFrame:
    """Loads a CSV dataset in the canonical schema format."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Canonical dataset file not found at: {path}")
    df = pd.read_csv(path)
    return df


def load_from_database(db_session) -> pd.DataFrame:
    """
    Extracts canonical academic records directly from the Phase 1 database.
    Queries StudentProfile joined with Department and AcademicRecord.
    """
    from backend.app.models.student import StudentProfile
    from backend.app.models.academic_record import AcademicRecord
    from backend.app.models.department import Department
    from sqlalchemy import select
    
    stmt = (
        select(
            StudentProfile.student_number,
            StudentProfile.first_name,
            StudentProfile.last_name,
            StudentProfile.gender,
            StudentProfile.date_of_birth,
            Department.code.label("department_code"),
            AcademicRecord.semester,
            AcademicRecord.academic_year,
            AcademicRecord.attendance_percentage,
            AcademicRecord.previous_cgpa,
            AcademicRecord.mid_1,
            AcademicRecord.mid_2,
            AcademicRecord.internal_marks,
            AcademicRecord.backlogs,
            AcademicRecord.semester_cgpa,
            AcademicRecord.grade,
            AcademicRecord.risk_level,
        )
        .join(Department, StudentProfile.department_id == Department.id)
        .join(AcademicRecord, AcademicRecord.student_id == StudentProfile.id)
    )
    
    results = db_session.execute(stmt).fetchall()
    
    records = []
    current_year = datetime.now(timezone.utc).year
    
    for row in results:
        # Approximate age from date_of_birth if present
        if row.date_of_birth:
            age = current_year - row.date_of_birth.year
        else:
            age = 20
            
        full_name = f"{row.first_name} {row.last_name}".strip()
        
        records.append({
            SCHEMA.STUDENT_ID: row.student_number,
            SCHEMA.NAME: full_name,
            SCHEMA.GENDER: row.gender.value if hasattr(row.gender, "value") else str(row.gender),
            SCHEMA.AGE: age,
            SCHEMA.DEPARTMENT: row.department_code,
            SCHEMA.SEMESTER: row.semester,
            SCHEMA.ACADEMIC_YEAR: row.academic_year,
            SCHEMA.ATTENDANCE: float(row.attendance_percentage) if row.attendance_percentage is not None else None,
            SCHEMA.PREVIOUS_CGPA: float(row.previous_cgpa) if row.previous_cgpa is not None else None,
            SCHEMA.MID_1: float(row.mid_1) if row.mid_1 is not None else None,
            SCHEMA.MID_2: float(row.mid_2) if row.mid_2 is not None else None,
            SCHEMA.INTERNAL_MARKS: float(row.internal_marks) if row.internal_marks is not None else None,
            SCHEMA.BACKLOGS: int(row.backlogs) if row.backlogs is not None else 0,
            SCHEMA.TARGET_CGPA: float(row.semester_cgpa) if row.semester_cgpa is not None else None,
            SCHEMA.TARGET_GRADE: row.grade if row.grade is not None else None,
            SCHEMA.TARGET_RISK: row.risk_level.value if hasattr(row.risk_level, "value") else str(row.risk_level) if row.risk_level else None,
        })
        
    return pd.DataFrame(records)


def generate_manifest(
    df: pd.DataFrame,
    source_name: str,
    source_type: str,
    source_path: str,
    column_mapping: Optional[Dict[str, str]] = None,
    dropped_columns: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
) -> DatasetManifest:
    """Generates and writes a dataset manifest JSON."""
    if Path(source_path).exists():
        sha256 = compute_file_sha256(source_path)
    else:
        sha256 = hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()
        
    manifest = DatasetManifest(
        dataset_name=source_name,
        source_type=source_type,
        source_path=str(source_path),
        record_count=len(df),
        column_count=len(df.columns),
        sha256_hash=sha256,
        columns_original=list(df.columns),
        columns_mapped=column_mapping or {},
        columns_dropped=dropped_columns or [],
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        is_canonical=all(col in df.columns for col in CANONICAL_COLUMNS),
    )
    
    target_dir = output_dir or REPORTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = target_dir / "dataset_manifest.json"
    
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(asdict(manifest), f, indent=2)
        
    return manifest
