"""
Centralized Configuration, Taxonomies, and Institutional Policy Thresholds for Phase 8.

Defines:
1. Recommendation taxonomies (Categories, Priorities, Sources, Impact, Time Horizons).
2. Institutional benchmark thresholds aligned with Phase 4 Risk Policy and Phase 7 Simulator.
3. System parameters (maximum recommendations returned, ranking weights).
"""

from enum import Enum
from typing import Dict, Any


class RecommendationCategory(str, Enum):
    ATTENDANCE = "ATTENDANCE"
    BACKLOG_RECOVERY = "BACKLOG_RECOVERY"
    EXAM_PREPARATION = "EXAM_PREPARATION"
    INTERNAL_ASSESSMENT = "INTERNAL_ASSESSMENT"
    STUDY_IMPROVEMENT = "STUDY_IMPROVEMENT"
    CGPA_IMPROVEMENT = "CGPA_IMPROVEMENT"
    ACADEMIC_HABITS = "ACADEMIC_HABITS"
    MAINTAIN_STRENGTH = "MAINTAIN_STRENGTH"


class RecommendationPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


PRIORITY_SEVERITY_ORDER: Dict[RecommendationPriority, int] = {
    RecommendationPriority.CRITICAL: 4,
    RecommendationPriority.HIGH: 3,
    RecommendationPriority.MEDIUM: 2,
    RecommendationPriority.LOW: 1,
}


class RecommendationSource(str, Enum):
    ACADEMIC_DATA = "ACADEMIC_DATA"
    RISK_POLICY = "RISK_POLICY"
    XAI = "XAI"
    WHAT_IF_SIMULATION = "WHAT_IF_SIMULATION"
    COMBINED = "COMBINED"


class ExpectedImpact(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class TimeHorizon(str, Enum):
    THIS_WEEK = "THIS_WEEK"
    NEXT_30_DAYS = "NEXT_30_DAYS"
    LONGER_TERM = "LONGER_TERM"


class RecommendationPolicyConfig:
    """
    Centralized Institutional Policy Thresholds for Academic Decision Support.
    Aligned with Phase 4 Risk Policy thresholds and academic benchmarks.
    """
    POLICY_VERSION = "1.0.0"
    MAX_RECOMMENDATIONS_DEFAULT = 5

    # Attendance Thresholds (%)
    ATTENDANCE_CRITICAL_THRESHOLD = 65.0
    ATTENDANCE_WARNING_THRESHOLD = 75.0
    ATTENDANCE_SAFE_TARGET = 80.0
    ATTENDANCE_EXCELLENCE_THRESHOLD = 90.0

    # Backlog Thresholds
    BACKLOG_CRITICAL_THRESHOLD = 3
    BACKLOG_WARNING_THRESHOLD = 1

    # Examination & Assessment Targets (0 - 100)
    MIDTERM_CRITICAL_THRESHOLD = 45.0
    MIDTERM_WARNING_THRESHOLD = 60.0
    MIDTERM_TARGET = 75.0
    MIDTERM_EXCELLENCE_THRESHOLD = 85.0

    INTERNAL_CRITICAL_THRESHOLD = 50.0
    INTERNAL_WARNING_THRESHOLD = 65.0
    INTERNAL_TARGET = 75.0
    INTERNAL_EXCELLENCE_THRESHOLD = 85.0

    # CGPA Benchmarks (0 - 10.0)
    CGPA_CRITICAL_THRESHOLD = 5.5
    CGPA_WARNING_THRESHOLD = 6.5
    CGPA_TARGET = 7.5
    CGPA_EXCELLENCE_THRESHOLD = 8.5

    # Trajectory / Trend Thresholds
    TREND_SHARP_DROP_THRESHOLD = -0.5
    TREND_MILD_DROP_THRESHOLD = -0.1
    TREND_STABLE_OR_IMPROVING = 0.0

    # Simulation delta thresholds for impact categorization
    SIMULATION_HIGH_IMPACT_CGPA_DELTA = 0.30
    SIMULATION_MED_IMPACT_CGPA_DELTA = 0.10
    SIMULATION_HIGH_IMPACT_RISK_SCORE_DELTA = 15.0
    SIMULATION_MED_IMPACT_RISK_SCORE_DELTA = 5.0
