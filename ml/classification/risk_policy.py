"""
Authoritative Deterministic Risk Policy Engine & Institutional Scoring Rules.

Defines:
1. Ground-truth labeling policy for academic risk (LOW, MEDIUM, HIGH, CRITICAL)
   with explicit severity precedence (CRITICAL > HIGH > MEDIUM > LOW).
2. Institutional performance category mapping (EXCELLENT, GOOD, AVERAGE, AT_RISK).
3. Institutional grade mapping (O, A+, A, B, C).
4. Probability-weighted continuous normalized risk score calculation.
5. Deterministic 5-factor risk breakdown (Attendance, Backlogs, Mid-Terms, CGPA, Trend).
"""

from enum import Enum
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PerformanceCategory(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    AVERAGE = "AVERAGE"
    AT_RISK = "AT_RISK"


# Severity rank ordering: higher index = higher severity precedence
SEVERITY_ORDER: Dict[RiskLevel, int] = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}

RISK_CLASSES: List[str] = [RiskLevel.LOW.value, RiskLevel.MEDIUM.value, RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]

# Probability weights for continuous risk score computation
RISK_PROBABILITY_WEIGHTS: Dict[str, float] = {
    RiskLevel.LOW.value: 0.00,
    RiskLevel.MEDIUM.value: 0.33,
    RiskLevel.HIGH.value: 0.67,
    RiskLevel.CRITICAL.value: 1.00,
}


def calculate_normalized_risk_score(probabilities: Dict[str, float]) -> float:
    """
    Computes normalized continuous risk score in [0.0, 100.0] using probability weights:
    Score = 100 * (0.00 * P(LOW) + 0.33 * P(MEDIUM) + 0.67 * P(HIGH) + 1.00 * P(CRITICAL))
    """
    score = 100.0 * sum(
        RISK_PROBABILITY_WEIGHTS.get(k, 0.0) * float(probabilities.get(k, 0.0))
        for k in RISK_CLASSES
    )
    return float(np.clip(round(score, 2), 0.0, 100.0))


def map_cgpa_to_performance_category(cgpa: float) -> str:
    """
    Maps CGPA to institutional performance category:
    - EXCELLENT: >= 8.5
    - GOOD: 7.0 <= CGPA < 8.5
    - AVERAGE: 5.5 <= CGPA < 7.0
    - AT_RISK: < 5.5
    """
    if cgpa >= 8.5:
        return PerformanceCategory.EXCELLENT.value
    elif cgpa >= 7.0:
        return PerformanceCategory.GOOD.value
    elif cgpa >= 5.5:
        return PerformanceCategory.AVERAGE.value
    else:
        return PerformanceCategory.AT_RISK.value


def map_cgpa_to_grade(cgpa: float) -> str:
    """
    Maps CGPA to institutional grade:
    - O:  >= 9.0
    - A+: 8.0 <= CGPA < 9.0
    - A:  7.0 <= CGPA < 8.0
    - B:  5.5 <= CGPA < 7.0
    - C:  < 5.5
    """
    if cgpa >= 9.0:
        return "O"
    elif cgpa >= 8.0:
        return "A+"
    elif cgpa >= 7.0:
        return "A"
    elif cgpa >= 5.5:
        return "B"
    else:
        return "C"


class RiskPolicyEngine:
    """
    Deterministic rule engine that assigns academic risk labels
    and generates multi-indicator policy breakdowns.
    """

    POLICY_VERSION = "1.0.0"
    TARGET_SOURCE = "policy_derived"

    # Configurable thresholds
    ATTENDANCE_CRITICAL = 65.0
    ATTENDANCE_HIGH = 75.0
    ATTENDANCE_LOW = 80.0

    BACKLOGS_CRITICAL = 3
    BACKLOGS_HIGH = 1

    CGPA_CRITICAL = 5.5
    CGPA_HIGH = 6.5
    CGPA_LOW = 7.5

    TREND_NEGATIVE_THRESHOLD = -0.5
    MIDTERM_WARNING_THRESHOLD = 60.0
    MIDTERM_CRITICAL_THRESHOLD = 45.0

    @classmethod
    def evaluate_risk_level(
        cls,
        attendance: float,
        backlogs: int,
        cgpa: float,
        trend: float = 0.0,
    ) -> RiskLevel:
        """
        Evaluates risk level with strict severity precedence.
        Whenever multiple conditions trigger, the highest severity wins:
        LOW < MEDIUM < HIGH < CRITICAL
        """
        applicable_levels: List[RiskLevel] = []

        # 1. Check CRITICAL conditions
        if (
            attendance < cls.ATTENDANCE_CRITICAL
            or backlogs >= cls.BACKLOGS_CRITICAL
            or cgpa < cls.CGPA_CRITICAL
        ):
            applicable_levels.append(RiskLevel.CRITICAL)

        # 2. Check HIGH conditions
        if (
            attendance < cls.ATTENDANCE_HIGH
            or backlogs >= cls.BACKLOGS_HIGH
            or cgpa < cls.CGPA_HIGH
            or trend < cls.TREND_NEGATIVE_THRESHOLD
        ):
            applicable_levels.append(RiskLevel.HIGH)

        # 3. Check MEDIUM baseline conditions
        if (
            backlogs == 0
            and attendance >= cls.ATTENDANCE_HIGH
            and cls.CGPA_HIGH <= cgpa < cls.CGPA_LOW
        ):
            applicable_levels.append(RiskLevel.MEDIUM)

        # 4. Check LOW conditions
        if (
            backlogs == 0
            and attendance >= cls.ATTENDANCE_LOW
            and cgpa >= cls.CGPA_LOW
            and trend >= cls.TREND_NEGATIVE_THRESHOLD
        ):
            applicable_levels.append(RiskLevel.LOW)

        # If no explicit category matched (e.g. attendance 76%, backlogs 0, cgpa 7.8, trend 0), default to MEDIUM if not meeting full LOW
        if not applicable_levels:
            if cgpa >= cls.CGPA_LOW and attendance >= cls.ATTENDANCE_HIGH:
                applicable_levels.append(RiskLevel.MEDIUM)
            else:
                applicable_levels.append(RiskLevel.MEDIUM)

        # Highest severity precedence
        selected_level = max(applicable_levels, key=lambda l: SEVERITY_ORDER[l])
        return selected_level

    @classmethod
    def generate_policy_labels(cls, df: pd.DataFrame) -> pd.Series:
        """
        Generates deterministic ground truth risk target series for a DataFrame.
        Expects columns: attendance_percentage, backlogs, previous_cgpa, and optionally previous_cgpa_trend.
        """
        labels = []
        for _, row in df.iterrows():
            att = float(row.get("attendance_percentage", 80.0))
            bl = int(row.get("backlogs", 0))
            cgpa = float(row.get("previous_cgpa", 7.0))
            trend = float(row.get("previous_cgpa_trend", 0.0))
            lvl = cls.evaluate_risk_level(att, bl, cgpa, trend)
            labels.append(lvl.value)
        return pd.Series(labels, index=df.index, name="academic_risk_level")

    @classmethod
    def generate_risk_factor_breakdown(
        cls,
        attendance: float,
        backlogs: int,
        mid_terms: float,
        previous_cgpa: float,
        academic_trend: float,
    ) -> List[Dict[str, Any]]:
        """
        Produces 5 transparent deterministic risk factor indicators with observed values.
        """
        factors = []

        # 1. Attendance
        if attendance < cls.ATTENDANCE_CRITICAL:
            att_lvl = RiskLevel.CRITICAL.value
            att_detail = f"Attendance ({attendance:.1f}%) is critically low (< {cls.ATTENDANCE_CRITICAL}%)."
        elif attendance < cls.ATTENDANCE_HIGH:
            att_lvl = RiskLevel.HIGH.value
            att_detail = f"Attendance ({attendance:.1f}%) is below institutional threshold ({cls.ATTENDANCE_HIGH}%)."
        elif attendance < cls.ATTENDANCE_LOW:
            att_lvl = RiskLevel.MEDIUM.value
            att_detail = f"Attendance ({attendance:.1f}%) is moderate but near minimum requirements."
        else:
            att_lvl = RiskLevel.LOW.value
            att_detail = f"Attendance ({attendance:.1f}%) meets high institutional standards (>= {cls.ATTENDANCE_LOW}%)."

        factors.append({
            "factor": "Attendance",
            "level": att_lvl,
            "value": round(attendance, 1),
            "detail": att_detail,
        })

        # 2. Backlogs
        if backlogs >= cls.BACKLOGS_CRITICAL:
            bl_lvl = RiskLevel.CRITICAL.value
            bl_detail = f"Severe backlog accumulation: {backlogs} active backlogs (>= {cls.BACKLOGS_CRITICAL})."
        elif backlogs >= cls.BACKLOGS_HIGH:
            bl_lvl = RiskLevel.HIGH.value
            bl_detail = f"Active backlogs present: {backlogs} course(s) pending."
        else:
            bl_lvl = RiskLevel.LOW.value
            bl_detail = "Clean academic record with zero active backlogs."

        factors.append({
            "factor": "Backlogs",
            "level": bl_lvl,
            "value": backlogs,
            "detail": bl_detail,
        })

        # 3. Mid-Term Performance
        if mid_terms < cls.MIDTERM_CRITICAL_THRESHOLD:
            mid_lvl = RiskLevel.CRITICAL.value
            mid_detail = f"Average mid-term score ({mid_terms:.1f}) is critically low (< {cls.MIDTERM_CRITICAL_THRESHOLD})."
        elif mid_terms < cls.MIDTERM_WARNING_THRESHOLD:
            mid_lvl = RiskLevel.HIGH.value
            mid_detail = f"Mid-term performance ({mid_terms:.1f}) requires academic improvement (< {cls.MIDTERM_WARNING_THRESHOLD})."
        elif mid_terms < 75.0:
            mid_lvl = RiskLevel.MEDIUM.value
            mid_detail = f"Mid-term performance ({mid_terms:.1f}) is satisfactory."
        else:
            mid_lvl = RiskLevel.LOW.value
            mid_detail = f"Strong mid-term examination performance ({mid_terms:.1f})."

        factors.append({
            "factor": "Mid-Term Performance",
            "level": mid_lvl,
            "value": round(mid_terms, 1),
            "detail": mid_detail,
        })

        # 4. Cumulative/Previous CGPA
        if previous_cgpa < cls.CGPA_CRITICAL:
            cgpa_lvl = RiskLevel.CRITICAL.value
            cgpa_detail = f"Prior CGPA ({previous_cgpa:.2f}) is in critical at-risk range (< {cls.CGPA_CRITICAL})."
        elif previous_cgpa < cls.CGPA_HIGH:
            cgpa_lvl = RiskLevel.HIGH.value
            cgpa_detail = f"Prior CGPA ({previous_cgpa:.2f}) is below target average standard (< {cls.CGPA_HIGH})."
        elif previous_cgpa < cls.CGPA_LOW:
            cgpa_lvl = RiskLevel.MEDIUM.value
            cgpa_detail = f"Prior CGPA ({previous_cgpa:.2f}) indicates steady average standing."
        else:
            cgpa_lvl = RiskLevel.LOW.value
            cgpa_detail = f"Prior CGPA ({previous_cgpa:.2f}) demonstrates excellent academic mastery."

        factors.append({
            "factor": "Cumulative/Previous CGPA",
            "level": cgpa_lvl,
            "value": round(previous_cgpa, 2),
            "detail": cgpa_detail,
        })

        # 5. Academic Trend
        if academic_trend < cls.TREND_NEGATIVE_THRESHOLD:
            trend_lvl = RiskLevel.HIGH.value
            trend_detail = f"Sharp downward academic performance trajectory (trend: {academic_trend:+.2f})."
        elif academic_trend < 0.0:
            trend_lvl = RiskLevel.MEDIUM.value
            trend_detail = f"Slight negative academic performance trend ({academic_trend:+.2f})."
        else:
            trend_lvl = RiskLevel.LOW.value
            trend_detail = f"Stable or upward academic trajectory ({academic_trend:+.2f})."

        factors.append({
            "factor": "Academic Trend",
            "level": trend_lvl,
            "value": round(academic_trend, 2),
            "detail": trend_detail,
        })

        return factors
