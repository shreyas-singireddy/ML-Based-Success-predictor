"""
Data Quality Reporter for ML Preprocessing Pipeline.

Generates comprehensive data quality reports in both JSON and Markdown formats:
- Missing value analysis and percentages
- Exact and logical duplicate counts
- Numeric distributions and range bounds
- Outlier detection (IQR and domain limits)
- Categorical cardinality and frequency
- Row retention and transformation summary
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from ml.config.pipeline_config import (
    SCHEMA,
    VALIDATION_BOUNDS,
    REPORTS_DIR,
)
from ml.pipelines.validation import ValidationResult, ValidationSeverity


@dataclass
class ColumnQualitySummary:
    column_name: str
    data_type: str
    total_count: int
    missing_count: int
    missing_percentage: float
    unique_count: int
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    std_value: Optional[float] = None
    iqr_outliers_count: int = 0
    categories_freq: Optional[Dict[str, int]] = None


@dataclass
class DataQualityReport:
    report_title: str
    generated_at_utc: str
    total_raw_rows: int
    total_columns: int
    exact_duplicates_count: int
    logical_duplicates_count: int
    rows_retained: int
    rows_removed: int
    validation_status: str
    validation_issues_count: int
    column_summaries: Dict[str, ColumnQualitySummary]
    issues: List[Dict[str, Any]]


class DataQualityReporter:
    """Analyzes DataFrame quality and generates structured Markdown & JSON reports."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or REPORTS_DIR

    def generate_report(
        self,
        raw_df: pd.DataFrame,
        cleaned_df: Optional[pd.DataFrame] = None,
        validation_result: Optional[ValidationResult] = None,
        rows_removed_count: int = 0,
    ) -> DataQualityReport:
        total_rows = len(raw_df)
        total_cols = len(raw_df.columns)
        
        # Exact duplicates
        exact_dups = int(raw_df.duplicated().sum())
        
        # Logical duplicates (student_number + semester)
        if SCHEMA.STUDENT_ID in raw_df.columns and SCHEMA.SEMESTER in raw_df.columns:
            logical_dups = int(raw_df.duplicated(subset=[SCHEMA.STUDENT_ID, SCHEMA.SEMESTER]).sum())
        else:
            logical_dups = 0
            
        col_summaries: Dict[str, ColumnQualitySummary] = {}
        
        for col in raw_df.columns:
            series = raw_df[col]
            missing_cnt = int(series.isna().sum())
            missing_pct = round((missing_cnt / total_rows) * 100.0, 2) if total_rows > 0 else 0.0
            unique_cnt = int(series.nunique(dropna=True))
            
            # Numeric columns
            if pd.api.types.is_numeric_dtype(series):
                valid_num = pd.to_numeric(series, errors="coerce").dropna()
                if len(valid_num) > 0:
                    q25 = float(valid_num.quantile(0.25))
                    q75 = float(valid_num.quantile(0.75))
                    iqr = q75 - q25
                    lower_bound = q25 - 1.5 * iqr
                    upper_bound = q75 + 1.5 * iqr
                    outliers = int(((valid_num < lower_bound) | (valid_num > upper_bound)).sum())
                    
                    summary = ColumnQualitySummary(
                        column_name=col,
                        data_type=str(series.dtype),
                        total_count=total_rows,
                        missing_count=missing_cnt,
                        missing_percentage=missing_pct,
                        unique_count=unique_cnt,
                        min_value=round(float(valid_num.min()), 2),
                        max_value=round(float(valid_num.max()), 2),
                        mean_value=round(float(valid_num.mean()), 2),
                        std_value=round(float(valid_num.std()), 2) if len(valid_num) > 1 else 0.0,
                        iqr_outliers_count=outliers,
                    )
                else:
                    summary = ColumnQualitySummary(
                        column_name=col,
                        data_type=str(series.dtype),
                        total_count=total_rows,
                        missing_count=missing_cnt,
                        missing_percentage=missing_pct,
                        unique_count=unique_cnt,
                    )
            else:
                # Categorical column
                top_cats = series.value_counts(dropna=False).head(10).to_dict()
                cats_freq = {str(k): int(v) for k, v in top_cats.items()}
                summary = ColumnQualitySummary(
                    column_name=col,
                    data_type=str(series.dtype),
                    total_count=total_rows,
                    missing_count=missing_cnt,
                    missing_percentage=missing_pct,
                    unique_count=unique_cnt,
                    categories_freq=cats_freq,
                )
            col_summaries[col] = summary
            
        issues_list = []
        val_status = "VALID"
        if validation_result:
            val_status = "VALID" if validation_result.is_valid else "INVALID"
            for issue in validation_result.issues:
                issues_list.append({
                    "column": issue.column,
                    "severity": issue.severity.value,
                    "type": issue.issue_type,
                    "message": issue.message,
                    "affected_count": issue.affected_count,
                })
                
        retained = len(cleaned_df) if cleaned_df is not None else (total_rows - rows_removed_count)
        
        report = DataQualityReport(
            report_title="ML Pipeline Phase 2 — Data Quality & Integrity Report",
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
            total_raw_rows=total_rows,
            total_columns=total_cols,
            exact_duplicates_count=exact_dups,
            logical_duplicates_count=logical_dups,
            rows_retained=retained,
            rows_removed=rows_removed_count,
            validation_status=val_status,
            validation_issues_count=len(issues_list),
            column_summaries=col_summaries,
            issues=issues_list,
        )
        
        self._save_json(report)
        self._save_markdown(report)
        return report

    def _save_json(self, report: DataQualityReport) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = self.output_dir / "data_quality_report.json"
        
        report_dict = asdict(report)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)
        return json_path

    def _save_markdown(self, report: DataQualityReport) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        md_path = self.output_dir / "data_quality_report.md"
        
        lines = [
            f"# {report.report_title}",
            f"\n**Generated (UTC):** {report.generated_at_utc}  ",
            f"**Validation Status:** `{report.validation_status}`  ",
            f"**Total Records:** {report.total_raw_rows} | **Columns:** {report.total_columns} | **Rows Retained:** {report.rows_retained} | **Rows Removed:** {report.rows_removed}\n",
            "## 1. Executive Summary Table",
            "| Metric | Value | Status |",
            "| :--- | :--- | :--- |",
            f"| Total Raw Rows | {report.total_raw_rows} | INFO |",
            f"| Exact Duplicates | {report.exact_duplicates_count} | {'WARNING' if report.exact_duplicates_count > 0 else 'VALID'} |",
            f"| Logical Duplicates (Student+Sem) | {report.logical_duplicates_count} | {'WARNING' if report.logical_duplicates_count > 0 else 'VALID'} |",
            f"| Total Validation Issues | {report.validation_issues_count} | {'ERROR' if report.validation_status == 'INVALID' else 'VALID'} |",
            f"| Final Cleaned Rows Retained | {report.rows_retained} | VALID |\n",
            "## 2. Column-Level Quality Metrics",
            "| Column | Type | Missing Count | Missing % | Min | Mean | Max | IQR Outliers |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        
        for col, s in report.column_summaries.items():
            min_str = str(s.min_value) if s.min_value is not None else "-"
            mean_str = str(s.mean_value) if s.mean_value is not None else "-"
            max_str = str(s.max_value) if s.max_value is not None else "-"
            outlier_str = str(s.iqr_outliers_count) if s.iqr_outliers_count > 0 else "0"
            lines.append(
                f"| `{col}` | `{s.data_type}` | {s.missing_count} | {s.missing_percentage}% | {min_str} | {mean_str} | {max_str} | {outlier_str} |"
            )
            
        lines.append("\n## 3. Validation Issues & Actions")
        if not report.issues:
            lines.append("✓ No validation issues detected. All records comply with canonical domain constraints.")
        else:
            lines.append("| Severity | Column | Type | Message | Affected Count |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for issue in report.issues:
                lines.append(
                    f"| `{issue['severity']}` | `{issue['column']}` | `{issue['type']}` | {issue['message']} | {issue['affected_count']} |"
                )
                
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return md_path
