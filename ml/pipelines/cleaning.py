"""
Data Cleaning and Imputation Module.

Handles:
1. Exact row deduplication
2. Logical deduplication (student_number + semester)
3. Exclusion of rows with missing prediction target (semester_cgpa)
4. Domain boundary enforcement (soft-clipping impossible marks/attendance)
5. Outlier tagging and domain validation
6. Missing value imputation with fit-time statistical tracking
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
import numpy as np
import pandas as pd

from ml.config.pipeline_config import (
    SCHEMA,
    VALIDATION_BOUNDS,
    ALLOWED_GENDERS,
    ALLOWED_DEPARTMENTS,
    DEFAULT_CONFIG,
    PipelineConfig,
)


@dataclass
class CleaningMetadata:
    initial_row_count: int
    final_row_count: int
    exact_duplicates_removed: int
    logical_duplicates_resolved: int
    missing_target_rows_removed: int
    out_of_bounds_values_clipped: int
    missing_imputed_counts: Dict[str, int] = field(default_factory=dict)
    imputation_statistics: Dict[str, Any] = field(default_factory=dict)


class DataCleaner:
    """
    Cleans raw academic data, removes corrupt/duplicate records,
    and applies domain bounds and imputation rules.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.bounds = VALIDATION_BOUNDS
        self.fitted_medians: Dict[str, float] = {}
        self.fitted_modes: Dict[str, str] = {}
        self.is_fitted: bool = False

    def fit(self, df: pd.DataFrame) -> "DataCleaner":
        """Learns imputation statistics exclusively from the provided (training) dataset."""
        # Learn numerical medians
        for col, (min_val, max_val) in self.bounds.items():
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce").dropna()
                if len(series) > 0:
                    self.fitted_medians[col] = float(series.median())
                else:
                    self.fitted_medians[col] = (min_val + max_val) / 2.0
                    
        # Learn categorical modes
        for cat_col in [SCHEMA.GENDER, SCHEMA.DEPARTMENT]:
            if cat_col in df.columns:
                series = df[cat_col].dropna().astype(str)
                if len(series) > 0:
                    self.fitted_modes[cat_col] = str(series.mode()[0])
                else:
                    self.fitted_modes[cat_col] = self.config.cat_fill_value
                    
        self.is_fitted = True
        return self

    def clean(self, df: pd.DataFrame, is_training: bool = True) -> Tuple[pd.DataFrame, CleaningMetadata]:
        """
        Cleans the DataFrame.
        If is_training=True, fits imputation statistics if not already fitted.
        """
        initial_count = len(df)
        data = df.copy()
        
        # 1. Exact Duplicate Removal
        exact_dups = int(data.duplicated().sum())
        if exact_dups > 0:
            data = data.drop_duplicates(keep="first")
            
        # 2. Logical Duplicate Resolution (student_number + semester)
        logical_dups_resolved = 0
        if SCHEMA.STUDENT_ID in data.columns and SCHEMA.SEMESTER in data.columns:
            dup_mask = data.duplicated(subset=[SCHEMA.STUDENT_ID, SCHEMA.SEMESTER], keep="first")
            logical_dups_resolved = int(dup_mask.sum())
            if logical_dups_resolved > 0:
                # Retain the first entry and discard duplicate conflicts
                data = data.drop_duplicates(subset=[SCHEMA.STUDENT_ID, SCHEMA.SEMESTER], keep="first")

        # 3. Missing Target Removal (Required for supervised training data)
        missing_target_count = 0
        if is_training and SCHEMA.TARGET_CGPA in data.columns:
            target_mask = data[SCHEMA.TARGET_CGPA].isna()
            missing_target_count = int(target_mask.sum())
            if missing_target_count > 0:
                data = data[~target_mask].copy()

        # 4. Domain Boundary Soft-Clipping (Protect against impossible exam marks/attendance entries)
        clipped_count = 0
        for col, (min_val, max_val) in self.bounds.items():
            if col in data.columns:
                numeric_series = pd.to_numeric(data[col], errors="coerce")
                oob_mask = numeric_series.notna() & ((numeric_series < min_val) | (numeric_series > max_val))
                clipped_count += int(oob_mask.sum())
                data[col] = numeric_series.clip(lower=min_val, upper=max_val)

        # 5. Fit if needed during training
        if is_training and not self.is_fitted:
            self.fit(data)

        # 6. Missing Value Imputation
        missing_counts: Dict[str, int] = {}
        
        # Numeric columns imputation
        for col in self.fitted_medians:
            if col in data.columns and col != SCHEMA.TARGET_CGPA:
                null_mask = data[col].isna()
                cnt = int(null_mask.sum())
                if cnt > 0:
                    fill_val = self.fitted_medians.get(col, 0.0)
                    data[col] = data[col].fillna(fill_val)
                    missing_counts[col] = cnt
                    
        # Categorical columns imputation
        for cat_col in [SCHEMA.GENDER, SCHEMA.DEPARTMENT]:
            if cat_col in data.columns:
                null_mask = data[cat_col].isna()
                cnt = int(null_mask.sum())
                if cnt > 0:
                    fill_val = self.config.cat_fill_value
                    data[cat_col] = data[cat_col].fillna(fill_val)
                    missing_counts[cat_col] = cnt
                    
                # Normalize text
                data[cat_col] = data[cat_col].astype(str).str.strip().str.upper()

        final_count = len(data)
        
        metadata = CleaningMetadata(
            initial_row_count=initial_count,
            final_row_count=final_count,
            exact_duplicates_removed=exact_dups,
            logical_duplicates_resolved=logical_dups_resolved,
            missing_target_rows_removed=missing_target_count,
            out_of_bounds_values_clipped=clipped_count,
            missing_imputed_counts=missing_counts,
            imputation_statistics={
                "medians": self.fitted_medians,
                "modes": self.fitted_modes,
            },
        )
        
        return data, metadata
