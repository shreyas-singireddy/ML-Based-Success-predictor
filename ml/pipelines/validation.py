"""
Data Validation Module for Academic Datasets.

Validates:
1. Schema & Required Columns
2. Numeric Ranges and Boundaries
3. Categorical Allowed Values
4. Logical Consistency (e.g. impossible marks, duplicate semester records, negative backlogs)

Generates structured validation issues categorized as ERROR, WARNING, or INFO.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd

from ml.config.pipeline_config import (
    SCHEMA,
    CANONICAL_COLUMNS,
    VALIDATION_BOUNDS,
    ALLOWED_GENDERS,
    ALLOWED_DEPARTMENTS,
)


class ValidationSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    column: str
    severity: ValidationSeverity
    issue_type: str
    message: str
    affected_count: int
    sample_indices: List[Any] = field(default_factory=list)


@dataclass
class ValidationResult:
    is_valid: bool
    total_records: int
    valid_records_count: int
    invalid_records_count: int
    issues: List[ValidationIssue]
    invalid_row_indices: Set[Any] = field(default_factory=set)


class DataValidator:
    """Validates raw academic datasets against canonical rules and domain boundaries."""
    
    def __init__(
        self,
        bounds: Optional[Dict[str, Tuple[float, float]]] = None,
        allowed_genders: Optional[List[str]] = None,
        allowed_departments: Optional[List[str]] = None,
        require_target: bool = True,
    ):
        self.bounds = bounds or VALIDATION_BOUNDS
        self.allowed_genders = allowed_genders or ALLOWED_GENDERS
        self.allowed_departments = allowed_departments or ALLOWED_DEPARTMENTS
        self.require_target = require_target

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        issues: List[ValidationIssue] = []
        invalid_indices: Set[Any] = set()
        
        # 1. Schema Validation — Check required columns
        missing_required = [col for col in CANONICAL_COLUMNS if col not in df.columns]
        if not self.require_target and SCHEMA.TARGET_CGPA in missing_required:
            missing_required.remove(SCHEMA.TARGET_CGPA)
            
        if missing_required:
            issues.append(
                ValidationIssue(
                    column="schema",
                    severity=ValidationSeverity.ERROR,
                    issue_type="missing_columns",
                    message=f"Missing required canonical columns: {missing_required}",
                    affected_count=len(missing_required),
                )
            )
            # Cannot proceed with row validation if fundamental schema is missing
            return ValidationResult(
                is_valid=False,
                total_records=len(df),
                valid_records_count=0,
                invalid_records_count=len(df),
                issues=issues,
                invalid_row_indices=set(df.index),
            )
            
        # 2. Missing Key Identifiers Check
        for id_col in [SCHEMA.STUDENT_ID, SCHEMA.SEMESTER]:
            if id_col in df.columns:
                null_mask = df[id_col].isna()
                count = int(null_mask.sum())
                if count > 0:
                    bad_idx = df.index[null_mask].tolist()
                    invalid_indices.update(bad_idx)
                    issues.append(
                        ValidationIssue(
                            column=id_col,
                            severity=ValidationSeverity.ERROR,
                            issue_type="null_identifier",
                            message=f"Identifier column '{id_col}' has {count} null values.",
                            affected_count=count,
                            sample_indices=bad_idx[:5],
                        )
                    )

        # 3. Numeric Boundary Validation
        for col, (min_val, max_val) in self.bounds.items():
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce")
                # Detect non-numeric conversions (strings in numeric columns)
                non_num_mask = df[col].notna() & series.isna()
                non_num_count = int(non_num_mask.sum())
                if non_num_count > 0:
                    bad_idx = df.index[non_num_mask].tolist()
                    invalid_indices.update(bad_idx)
                    issues.append(
                        ValidationIssue(
                            column=col,
                            severity=ValidationSeverity.ERROR,
                            issue_type="invalid_datatype",
                            message=f"Column '{col}' has {non_num_count} non-numeric values.",
                            affected_count=non_num_count,
                            sample_indices=bad_idx[:5],
                        )
                    )
                
                # Detect out-of-bounds values
                out_of_bounds_mask = series.notna() & ((series < min_val) | (series > max_val))
                oob_count = int(out_of_bounds_mask.sum())
                if oob_count > 0:
                    bad_idx = df.index[out_of_bounds_mask].tolist()
                    invalid_indices.update(bad_idx)
                    issues.append(
                        ValidationIssue(
                            column=col,
                            severity=ValidationSeverity.ERROR,
                            issue_type="out_of_bounds",
                            message=f"Column '{col}' has {oob_count} values outside allowable range [{min_val}, {max_val}].",
                            affected_count=oob_count,
                            sample_indices=bad_idx[:5],
                        )
                    )

        # 4. Categorical Allowed Values Check
        if SCHEMA.GENDER in df.columns:
            gender_series = df[SCHEMA.GENDER].astype(str).str.upper()
            invalid_gender_mask = df[SCHEMA.GENDER].notna() & ~gender_series.isin(self.allowed_genders)
            count = int(invalid_gender_mask.sum())
            if count > 0:
                bad_idx = df.index[invalid_gender_mask].tolist()
                issues.append(
                    ValidationIssue(
                        column=SCHEMA.GENDER,
                        severity=ValidationSeverity.WARNING,
                        issue_type="unrecognized_category",
                        message=f"Column '{SCHEMA.GENDER}' has {count} unrecognized values (will be handled as Unknown).",
                        affected_count=count,
                        sample_indices=bad_idx[:5],
                    )
                )

        if SCHEMA.DEPARTMENT in df.columns:
            dept_series = df[SCHEMA.DEPARTMENT].astype(str).str.upper()
            invalid_dept_mask = df[SCHEMA.DEPARTMENT].notna() & ~dept_series.isin(self.allowed_departments)
            count = int(invalid_dept_mask.sum())
            if count > 0:
                bad_idx = df.index[invalid_dept_mask].tolist()
                issues.append(
                    ValidationIssue(
                        column=SCHEMA.DEPARTMENT,
                        severity=ValidationSeverity.WARNING,
                        issue_type="unrecognized_category",
                        message=f"Column '{SCHEMA.DEPARTMENT}' has {count} unrecognized values (will be handled as Unknown).",
                        affected_count=count,
                        sample_indices=bad_idx[:5],
                    )
                )

        # 5. Logical Consistency — Conflicting duplicate (student_number, semester) records
        if SCHEMA.STUDENT_ID in df.columns and SCHEMA.SEMESTER in df.columns:
            dup_mask = df.duplicated(subset=[SCHEMA.STUDENT_ID, SCHEMA.SEMESTER], keep=False)
            dup_count = int(dup_mask.sum())
            if dup_count > 0:
                bad_idx = df.index[dup_mask].tolist()
                invalid_indices.update(bad_idx)
                issues.append(
                    ValidationIssue(
                        column=f"{SCHEMA.STUDENT_ID}+{SCHEMA.SEMESTER}",
                        severity=ValidationSeverity.ERROR,
                        issue_type="logical_duplicate",
                        message=f"Found {dup_count} conflicting duplicate records for student + semester combinations.",
                        affected_count=dup_count,
                        sample_indices=bad_idx[:5],
                    )
                )

        # 6. Target Nulls (For Supervised Training)
        if self.require_target and SCHEMA.TARGET_CGPA in df.columns:
            target_null_mask = df[SCHEMA.TARGET_CGPA].isna()
            target_null_count = int(target_null_mask.sum())
            if target_null_count > 0:
                bad_idx = df.index[target_null_mask].tolist()
                invalid_indices.update(bad_idx)
                issues.append(
                    ValidationIssue(
                        column=SCHEMA.TARGET_CGPA,
                        severity=ValidationSeverity.ERROR,
                        issue_type="missing_target",
                        message=f"Found {target_null_count} rows with missing target '{SCHEMA.TARGET_CGPA}' (must be excluded from training).",
                        affected_count=target_null_count,
                        sample_indices=bad_idx[:5],
                    )
                )

        total_records = len(df)
        invalid_count = len(invalid_indices)
        valid_count = total_records - invalid_count
        is_valid = len([i for i in issues if i.severity == ValidationSeverity.ERROR]) == 0

        return ValidationResult(
            is_valid=is_valid,
            total_records=total_records,
            valid_records_count=valid_count,
            invalid_records_count=invalid_count,
            issues=issues,
            invalid_row_indices=invalid_indices,
        )
