"""
Phase 2 — ML Pipeline Configuration

Centralized settings, canonical schema definitions, validation ranges,
feature definitions, and split settings.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Root project paths
ML_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ML_DIR.parent
DATA_DIR = ML_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REGISTRY_DIR = ML_DIR / "registry"
REPORTS_DIR = ML_DIR / "reports"


@dataclass(frozen=True)
class ColumnSchema:
    # Student identifiers & demographics
    STUDENT_ID: str = "student_number"
    NAME: str = "name"
    GENDER: str = "gender"
    AGE: str = "age"
    DEPARTMENT: str = "department_code"
    
    # Academic semester identifiers
    SEMESTER: str = "semester"
    ACADEMIC_YEAR: str = "academic_year"
    
    # Pre-exam predictors (Available at prediction time during semester t)
    ATTENDANCE: str = "attendance_percentage"
    PREVIOUS_CGPA: str = "previous_cgpa"
    MID_1: str = "mid_1"
    MID_2: str = "mid_2"
    INTERNAL_MARKS: str = "internal_marks"
    BACKLOGS: str = "backlogs"
    
    # Target variables (Determined at END of semester t — Strictly excluded from input X)
    TARGET_CGPA: str = "semester_cgpa"
    TARGET_GRADE: str = "grade"
    TARGET_RISK: str = "risk_level"


SCHEMA = ColumnSchema()

# Canonical required input columns for raw academic datasets
CANONICAL_COLUMNS: List[str] = [
    SCHEMA.STUDENT_ID,
    SCHEMA.NAME,
    SCHEMA.GENDER,
    SCHEMA.AGE,
    SCHEMA.DEPARTMENT,
    SCHEMA.SEMESTER,
    SCHEMA.ACADEMIC_YEAR,
    SCHEMA.ATTENDANCE,
    SCHEMA.PREVIOUS_CGPA,
    SCHEMA.MID_1,
    SCHEMA.MID_2,
    SCHEMA.INTERNAL_MARKS,
    SCHEMA.BACKLOGS,
    SCHEMA.TARGET_CGPA,
]

# Optional columns that might be present in canonical datasets
OPTIONAL_COLUMNS: List[str] = [
    SCHEMA.TARGET_GRADE,
    SCHEMA.TARGET_RISK,
]

# Validation ranges based on university academic regulations
VALIDATION_BOUNDS: Dict[str, Tuple[float, float]] = {
    SCHEMA.AGE: (15.0, 100.0),
    SCHEMA.SEMESTER: (1.0, 12.0),
    SCHEMA.ATTENDANCE: (0.0, 100.0),
    SCHEMA.PREVIOUS_CGPA: (0.0, 10.0),
    SCHEMA.MID_1: (0.0, 100.0),
    SCHEMA.MID_2: (0.0, 100.0),
    SCHEMA.INTERNAL_MARKS: (0.0, 100.0),
    SCHEMA.BACKLOGS: (0.0, 50.0),
    SCHEMA.TARGET_CGPA: (0.0, 10.0),
}

# Categorical allowed values
ALLOWED_GENDERS: List[str] = ["MALE", "FEMALE", "OTHER"]
ALLOWED_DEPARTMENTS: List[str] = ["CS", "IT", "ECE", "EEE", "MECH", "CIVIL", "AI", "DS"]

# Engineered Feature Names
FEATURE_ACADEMIC_AVG = "academic_average"
FEATURE_ATTENDANCE_RISK = "attendance_risk_score"
FEATURE_ATTENDANCE_RISK_CAT = "attendance_risk_category"
FEATURE_INTERNAL_AVG = "internal_average"
FEATURE_MID_TERM_AVG = "mid_term_average"
FEATURE_PREV_CGPA_TREND = "previous_cgpa_trend"
FEATURE_BACKLOG_SEVERITY = "backlog_severity_score"
FEATURE_BACKLOG_SEVERITY_CAT = "backlog_severity_category"
FEATURE_ACADEMIC_STABILITY = "academic_stability"

ENGINEERED_FEATURE_NAMES: List[str] = [
    FEATURE_ACADEMIC_AVG,
    FEATURE_ATTENDANCE_RISK,
    FEATURE_ATTENDANCE_RISK_CAT,
    FEATURE_INTERNAL_AVG,
    FEATURE_MID_TERM_AVG,
    FEATURE_PREV_CGPA_TREND,
    FEATURE_BACKLOG_SEVERITY,
    FEATURE_BACKLOG_SEVERITY_CAT,
    FEATURE_ACADEMIC_STABILITY,
]

# Raw features to retain in feature matrix X alongside engineered features
BASE_FEATURES: List[str] = [
    SCHEMA.GENDER,
    SCHEMA.AGE,
    SCHEMA.DEPARTMENT,
    SCHEMA.SEMESTER,
    SCHEMA.ATTENDANCE,
    SCHEMA.PREVIOUS_CGPA,
    SCHEMA.MID_1,
    SCHEMA.MID_2,
    SCHEMA.INTERNAL_MARKS,
    SCHEMA.BACKLOGS,
]

# Explicit Leakage Columns: NEVER allowed in Feature Matrix X
LEAKAGE_TARGET_COLUMNS: List[str] = [
    SCHEMA.TARGET_CGPA,
    SCHEMA.TARGET_GRADE,
    SCHEMA.TARGET_RISK,
]

# Identifier Columns: Excluded from ML modeling to prevent memorization
IDENTIFIER_COLUMNS: List[str] = [
    SCHEMA.STUDENT_ID,
    SCHEMA.NAME,
    SCHEMA.ACADEMIC_YEAR,
]

# Numerical & Categorical feature subsets for Sklearn Pipeline
NUMERICAL_FEATURES: List[str] = [
    SCHEMA.AGE,
    SCHEMA.SEMESTER,
    SCHEMA.ATTENDANCE,
    SCHEMA.PREVIOUS_CGPA,
    SCHEMA.MID_1,
    SCHEMA.MID_2,
    SCHEMA.INTERNAL_MARKS,
    SCHEMA.BACKLOGS,
    FEATURE_ACADEMIC_AVG,
    FEATURE_ATTENDANCE_RISK,
    FEATURE_INTERNAL_AVG,
    FEATURE_MID_TERM_AVG,
    FEATURE_PREV_CGPA_TREND,
    FEATURE_BACKLOG_SEVERITY,
    FEATURE_ACADEMIC_STABILITY,
]

CATEGORICAL_FEATURES: List[str] = [
    SCHEMA.GENDER,
    SCHEMA.DEPARTMENT,
    FEATURE_ATTENDANCE_RISK_CAT,
    FEATURE_BACKLOG_SEVERITY_CAT,
]


@dataclass
class PipelineConfig:
    """Master pipeline configuration parameters."""
    random_seed: int = 42
    test_size: float = 0.15
    val_size: float = 0.15
    train_size: float = 0.70
    
    # Split strategy: "student_temporal" (recommended for longitudinal) or "student_group"
    split_strategy: str = "student_temporal"
    
    # Attendance thresholds
    attendance_critical_threshold: float = 65.0
    attendance_warning_threshold: float = 75.0
    
    # Outlier detection strategy: "domain_clip" or "iqr_fence"
    outlier_strategy: str = "domain_clip"
    iqr_multiplier: float = 1.5
    
    # Imputation strategy
    num_impute_strategy: str = "median"
    cat_impute_strategy: str = "constant"
    cat_fill_value: str = "Unknown"
    
    # Scaling method: "robust" (handles academic variances) or "standard"
    scaling_method: str = "robust"
    
    # Paths
    raw_data_dir: Path = RAW_DATA_DIR
    processed_data_dir: Path = PROCESSED_DATA_DIR
    registry_dir: Path = REGISTRY_DIR
    reports_dir: Path = REPORTS_DIR


DEFAULT_CONFIG = PipelineConfig()
