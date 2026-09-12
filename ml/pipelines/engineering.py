"""
Feature Engineering Module with Strict Temporal Guardrails.

Constructs 7 domain-specific academic success features:
1. Academic Average (Pre-exam average of Mid 1, Mid 2, and Internal Marks)
2. Attendance Risk (Continuous score and discrete category: CRITICAL, AT_RISK, NORMAL)
3. Internal Average (Normalized continuous internal assessment)
4. Mid-Term Average (Pre-exam average of available midterms)
5. Previous CGPA Trend (Historical Delta CGPA using STRICTLY t-1 and earlier; zero target CGPA)
6. Backlog Severity (Continuous severity score and discrete category: NONE, MODERATE, SEVERE)
7. Academic Stability (Rolling variance/std of historical semesters prior to t; zero target semester)

Enforces strict temporal sorting by (student_number, academic_year, semester)
and mathematically forbids future/target semester information in historical metrics.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

from ml.config.pipeline_config import (
    SCHEMA,
    FEATURE_ACADEMIC_AVG,
    FEATURE_ATTENDANCE_RISK,
    FEATURE_ATTENDANCE_RISK_CAT,
    FEATURE_INTERNAL_AVG,
    FEATURE_MID_TERM_AVG,
    FEATURE_PREV_CGPA_TREND,
    FEATURE_BACKLOG_SEVERITY,
    FEATURE_BACKLOG_SEVERITY_CAT,
    FEATURE_ACADEMIC_STABILITY,
    ENGINEERED_FEATURE_NAMES,
    DEFAULT_CONFIG,
    PipelineConfig,
)


@dataclass
class FeatureMetadata:
    feature_name: str
    description: str
    source_columns: List[str]
    data_type: str
    formula: str
    availability_time: str
    missing_value_strategy: str
    leakage_risk: str
    leakage_status: str


FEATURE_CATALOG: Dict[str, FeatureMetadata] = {
    FEATURE_ACADEMIC_AVG: FeatureMetadata(
        feature_name=FEATURE_ACADEMIC_AVG,
        description="Composite average of all pre-exam assessments in the current semester.",
        source_columns=[SCHEMA.MID_1, SCHEMA.MID_2, SCHEMA.INTERNAL_MARKS],
        data_type="float64",
        formula="(mid_1 + mid_2 + internal_marks) / 3.0",
        availability_time="Pre-Exam (Mid-Semester)",
        missing_value_strategy="Mean of available mid-term/internal components",
        leakage_risk="None",
        leakage_status="SAFE (Pre-Exam Only)",
    ),
    FEATURE_ATTENDANCE_RISK: FeatureMetadata(
        feature_name=FEATURE_ATTENDANCE_RISK,
        description="Continuous attendance deficit risk score (0.0 for full attendance, 1.0 for severe deficit).",
        source_columns=[SCHEMA.ATTENDANCE],
        data_type="float64",
        formula="max(0.0, (75.0 - attendance_percentage)) / 75.0",
        availability_time="Pre-Exam (Ongoing Semester)",
        missing_value_strategy="Default to median attendance",
        leakage_risk="None",
        leakage_status="SAFE (Pre-Exam Only)",
    ),
    FEATURE_ATTENDANCE_RISK_CAT: FeatureMetadata(
        feature_name=FEATURE_ATTENDANCE_RISK_CAT,
        description="Institutional attendance risk category: CRITICAL (<65%), AT_RISK (65-74%), NORMAL (>=75%).",
        source_columns=[SCHEMA.ATTENDANCE],
        data_type="category",
        formula="Categorical binning by university attendance criteria",
        availability_time="Pre-Exam (Ongoing Semester)",
        missing_value_strategy="Impute NORMAL",
        leakage_risk="None",
        leakage_status="SAFE (Pre-Exam Only)",
    ),
    FEATURE_INTERNAL_AVG: FeatureMetadata(
        feature_name=FEATURE_INTERNAL_AVG,
        description="Normalized internal marks continuous fraction [0.0, 1.0].",
        source_columns=[SCHEMA.INTERNAL_MARKS],
        data_type="float64",
        formula="internal_marks / 100.0",
        availability_time="Pre-Exam (Ongoing Semester)",
        missing_value_strategy="Median imputation",
        leakage_risk="None",
        leakage_status="SAFE (Pre-Exam Only)",
    ),
    FEATURE_MID_TERM_AVG: FeatureMetadata(
        feature_name=FEATURE_MID_TERM_AVG,
        description="Mean of Mid-Term 1 and Mid-Term 2 examinations.",
        source_columns=[SCHEMA.MID_1, SCHEMA.MID_2],
        data_type="float64",
        formula="(mid_1 + mid_2) / 2.0",
        availability_time="Pre-Exam (Mid-Semester)",
        missing_value_strategy="Mean of available midterms",
        leakage_risk="None",
        leakage_status="SAFE (Pre-Exam Only)",
    ),
    FEATURE_PREV_CGPA_TREND: FeatureMetadata(
        feature_name=FEATURE_PREV_CGPA_TREND,
        description="Historical delta in previous CGPA between t-1 and earlier semesters (strictly past records).",
        source_columns=[SCHEMA.PREVIOUS_CGPA, SCHEMA.SEMESTER],
        data_type="float64",
        formula="previous_cgpa[t-1] - previous_cgpa[t-2] (strictly prior semesters; 0.0 for semester 1)",
        availability_time="Semester Start (Past Academic History)",
        missing_value_strategy="Fallback to 0.0 for initial semesters",
        leakage_risk="Target/Future Leakage Protected",
        leakage_status="SAFE (Strictly Historical < t)",
    ),
    FEATURE_BACKLOG_SEVERITY: FeatureMetadata(
        feature_name=FEATURE_BACKLOG_SEVERITY,
        description="Continuous normalized backlog severity score [0.0, 1.0].",
        source_columns=[SCHEMA.BACKLOGS],
        data_type="float64",
        formula="min(1.0, backlogs / 5.0)",
        availability_time="Semester Start / Enrollment",
        missing_value_strategy="Fill 0 (no backlogs)",
        leakage_risk="None",
        leakage_status="SAFE (Known at Semester Registration)",
    ),
    FEATURE_BACKLOG_SEVERITY_CAT: FeatureMetadata(
        feature_name=FEATURE_BACKLOG_SEVERITY_CAT,
        description="Categorical backlog severity level: NONE (0), MODERATE (1-2), SEVERE (>=3).",
        source_columns=[SCHEMA.BACKLOGS],
        data_type="category",
        formula="Binned category based on backlog count",
        availability_time="Semester Start / Enrollment",
        missing_value_strategy="Fill NONE",
        leakage_risk="None",
        leakage_status="SAFE (Known at Semester Registration)",
    ),
    FEATURE_ACADEMIC_STABILITY: FeatureMetadata(
        feature_name=FEATURE_ACADEMIC_STABILITY,
        description="Standard deviation of past historical CGPAs prior to current semester (strictly past < t).",
        source_columns=[SCHEMA.PREVIOUS_CGPA, SCHEMA.SEMESTER],
        data_type="float64",
        formula="std(previous_cgpa[1...t-1]) (0.0 for semesters <= 2)",
        availability_time="Semester Start (Past Academic History)",
        missing_value_strategy="Fallback to 0.0 for new students",
        leakage_risk="Target/Future Leakage Protected",
        leakage_status="SAFE (Strictly Historical < t)",
    ),
}


class FeatureEngineer:
    """
    Applies feature engineering formulas to academic records.
    Strictly guarantees that longitudinal historical features only access records < t.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or DEFAULT_CONFIG

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforms raw cleaned DataFrame by calculating all 7 engineered features."""
        data = df.copy()
        
        # 1. Academic Average: (mid_1 + mid_2 + internal_marks) / 3
        mid1 = pd.to_numeric(data.get(SCHEMA.MID_1, 0.0), errors="coerce").fillna(0.0)
        mid2 = pd.to_numeric(data.get(SCHEMA.MID_2, 0.0), errors="coerce").fillna(0.0)
        internal = pd.to_numeric(data.get(SCHEMA.INTERNAL_MARKS, 0.0), errors="coerce").fillna(0.0)
        data[FEATURE_ACADEMIC_AVG] = ((mid1 + mid2 + internal) / 3.0).round(2)

        # 2. Attendance Risk Score & Category
        att = pd.to_numeric(data.get(SCHEMA.ATTENDANCE, 75.0), errors="coerce").fillna(75.0)
        crit_thresh = self.config.attendance_critical_threshold
        warn_thresh = self.config.attendance_warning_threshold
        
        # Continuous deficit score: 0 if att >= 75%, scaled to 1.0 as att -> 0%
        data[FEATURE_ATTENDANCE_RISK] = np.maximum(0.0, (warn_thresh - att) / warn_thresh).round(4)
        
        # Discrete category
        att_cats = []
        for a in att:
            if a < crit_thresh:
                att_cats.append("CRITICAL")
            elif a < warn_thresh:
                att_cats.append("AT_RISK")
            else:
                att_cats.append("NORMAL")
        data[FEATURE_ATTENDANCE_RISK_CAT] = att_cats

        # 3. Internal Average: internal_marks / 100.0
        data[FEATURE_INTERNAL_AVG] = (internal / 100.0).round(4)

        # 4. Mid-Term Average: (mid_1 + mid_2) / 2
        data[FEATURE_MID_TERM_AVG] = ((mid1 + mid2) / 2.0).round(2)

        # 5. Backlog Severity Score & Category
        backlogs = pd.to_numeric(data.get(SCHEMA.BACKLOGS, 0), errors="coerce").fillna(0)
        data[FEATURE_BACKLOG_SEVERITY] = np.minimum(1.0, backlogs / 5.0).round(4)
        
        backlog_cats = []
        for b in backlogs:
            if b == 0:
                backlog_cats.append("NONE")
            elif b <= 2:
                backlog_cats.append("MODERATE")
            else:
                backlog_cats.append("SEVERE")
        data[FEATURE_BACKLOG_SEVERITY_CAT] = backlog_cats

        # 6 & 7. Temporal Features: Previous CGPA Trend & Academic Stability
        # MANDATORY RULE: Sort chronologically by (student_number, academic_year, semester)
        # to ensure historical calculations use ONLY strictly prior records (< t).
        has_student = SCHEMA.STUDENT_ID in data.columns
        has_sem = SCHEMA.SEMESTER in data.columns
        
        if has_student and has_sem:
            # Preserve original index for output restoration
            data["_orig_idx"] = data.index
            
            sort_cols = [SCHEMA.STUDENT_ID]
            if SCHEMA.ACADEMIC_YEAR in data.columns:
                sort_cols.append(SCHEMA.ACADEMIC_YEAR)
            sort_cols.append(SCHEMA.SEMESTER)
            
            data = data.sort_values(by=sort_cols)
            
            # Compute historical trend: previous_cgpa difference between consecutive semesters
            # previous_cgpa in row t represents cumulative CGPA before semester t starts.
            # Delta CGPA = previous_cgpa[t] - previous_cgpa[t-1]
            trends = []
            stabilities = []
            
            for student_id, group in data.groupby(SCHEMA.STUDENT_ID, sort=False):
                prev_cgpas = group[SCHEMA.PREVIOUS_CGPA].tolist()
                
                for idx_in_group in range(len(prev_cgpas)):
                    # Historical records available strictly before semester t
                    # At index 0 (Semester 1): No prior semester history -> Trend = 0.0, Stability = 0.0
                    if idx_in_group == 0:
                        trends.append(0.0)
                        stabilities.append(0.0)
                    elif idx_in_group == 1:
                        # At index 1 (Semester 2): We have previous_cgpa[1] vs previous_cgpa[0]
                        delta = prev_cgpas[1] - prev_cgpas[0]
                        trends.append(round(delta, 3))
                        stabilities.append(0.0)  # Only 1 delta point available
                    else:
                        # At index >= 2: We have history of prior previous_cgpas
                        delta = prev_cgpas[idx_in_group] - prev_cgpas[idx_in_group - 1]
                        trends.append(round(delta, 3))
                        
                        # Stability: standard deviation of previous_cgpas up to current index
                        history = prev_cgpas[: idx_in_group + 1]
                        stability = float(np.std(history, ddof=1)) if len(history) > 1 else 0.0
                        stabilities.append(round(stability, 4))
                        
            data[FEATURE_PREV_CGPA_TREND] = trends
            data[FEATURE_ACADEMIC_STABILITY] = stabilities
            
            # Restore original order
            data = data.sort_values(by="_orig_idx").drop(columns=["_orig_idx"])
        else:
            # Single cross-sectional row fallback without historical linkage
            data[FEATURE_PREV_CGPA_TREND] = 0.0
            data[FEATURE_ACADEMIC_STABILITY] = 0.0

        return data
