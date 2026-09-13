"""
Phase 8: AI Personalized Recommendation Engine package.
"""

from ml.recommendations.recommendation_config import (
    RecommendationCategory,
    RecommendationPriority,
    RecommendationSource,
    ExpectedImpact,
    TimeHorizon,
    RecommendationPolicyConfig,
    PRIORITY_SEVERITY_ORDER,
)
from ml.recommendations.rules import (
    CandidateRecommendation,
    CandidateEvidence,
    BaseRecommendationRule,
    AttendanceRecommendationRule,
    BacklogRecommendationRule,
    MidtermExamRecommendationRule,
    InternalAssessmentRecommendationRule,
    AcademicTrendRecommendationRule,
    StrengthMaintenanceRule,
    DEFAULT_RULES,
)

__all__ = [
    "RecommendationCategory",
    "RecommendationPriority",
    "RecommendationSource",
    "ExpectedImpact",
    "TimeHorizon",
    "RecommendationPolicyConfig",
    "PRIORITY_SEVERITY_ORDER",
    "CandidateRecommendation",
    "CandidateEvidence",
    "BaseRecommendationRule",
    "AttendanceRecommendationRule",
    "BacklogRecommendationRule",
    "MidtermExamRecommendationRule",
    "InternalAssessmentRecommendationRule",
    "AcademicTrendRecommendationRule",
    "StrengthMaintenanceRule",
    "DEFAULT_RULES",
]
