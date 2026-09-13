"""
Deterministic intent detector for the GenAI Academic Assistant.

Classifies natural-language student questions into the AssistantIntent taxonomy
using fast, rule-based keyword/phrase matching. No ML model is involved here;
the classifier exists purely to route the request toward the correct verified
context slice and the right deterministic answer template.
"""

import re
from typing import Dict, List

from backend.app.schemas.assistant import AssistantIntent

# What-If / hypothetical phrasing
_WHAT_IF_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bwhat\s+if\b", re.IGNORECASE),
    re.compile(r"what\s+would\s+happen\s+if\b", re.IGNORECASE),
    re.compile(r"\b(if|when)\s+i\s+(improve|increase|raise|reduce|lower|decrease|boost|clear|fix|get|achieve|work)", re.IGNORECASE),
    re.compile(r"\bhypothetical\b", re.IGNORECASE),
    re.compile(r"\bsimulat(e|ion|ing|ed)?\b", re.IGNORECASE),
    re.compile(r"\bwould\s+my\s+(cgpa|gpa|risk|performance|grade|score)\s+(improve|become|be)\b", re.IGNORECASE),
]

_EXPLAINABILITY_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bwhy\b", re.IGNORECASE),
    re.compile(r"\bexplain\b", re.IGNORECASE),
    re.compile(r"\bbecause\b", re.IGNORECASE),
    re.compile(r"\breason(s)?\b", re.IGNORECASE),
    re.compile(r"\bshap\b", re.IGNORECASE),
    re.compile(r"\bfactor(s)?\b", re.IGNORECASE),
    re.compile(r"\bcontribut(e|ed|es|ion|ing)\b", re.IGNORECASE),
    re.compile(r"\battribut(e|ed|es|es)\b", re.IGNORECASE),
]

_RISK_PATTERNS: List[re.Pattern] = [
    re.compile(r"\brisk(s)?\b", re.IGNORECASE),
    re.compile(r"\blikely\s+to\s+fail\b", re.IGNORECASE),
    re.compile(r"\bin\s+danger\b", re.IGNORECASE),
    re.compile(r"\b(at\s+)?risk\s+score\b", re.IGNORECASE),
    re.compile(r"\bdrop\s*out\b", re.IGNORECASE),
]

_PREDICTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(predict|predicted|projection|projected|estimate|estimated|forecast)\b", re.IGNORECASE),
]

_ATTENDANCE_PATTERNS: List[re.Pattern] = [
    re.compile(r"\battendance\b", re.IGNORECASE),
    re.compile(r"\battend\b", re.IGNORECASE),
]

_BACKLOG_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bbacklog(s)?\b", re.IGNORECASE),
    re.compile(r"\barrear(s)?\b", re.IGNORECASE),
    re.compile(r"\bsuppl(y|ies)\b", re.IGNORECASE),
    re.compile(r"\bfailed\s+(subject|courses?|units?)\b", re.IGNORECASE),
]

_CGPA_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bcgpa\b", re.IGNORECASE),
    re.compile(r"\bgpa\b", re.IGNORECASE),
    re.compile(r"\bgrade\s+point\b", re.IGNORECASE),
]

_RECOMMENDATION_PATTERNS: List[re.Pattern] = [
    re.compile(r"\brecommend", re.IGNORECASE),
    re.compile(r"\bsuggest", re.IGNORECASE),
    re.compile(r"\badvice\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+should\s+i\b", re.IGNORECASE),
    re.compile(r"\bhow\s+(can|should|do)\s+i\b", re.IGNORECASE),
    re.compile(r"\bimprove\b", re.IGNORECASE),
    re.compile(r"\baction\s+plan\b", re.IGNORECASE),
    re.compile(r"\bpriority\b", re.IGNORECASE),
    re.compile(r"\bfirst\b", re.IGNORECASE),
]

_TREND_PATTERNS: List[re.Pattern] = [
    re.compile(r"\btrend(s|ed|ing)?\b", re.IGNORECASE),
    re.compile(r"\bover\s+time\b", re.IGNORECASE),
    re.compile(r"\bhistory\b", re.IGNORECASE),
    re.compile(r"\bprogress(ed|ing|ion)?\b", re.IGNORECASE),
    re.compile(r"\bimprov(ing|ed|ement)?\b", re.IGNORECASE),
    re.compile(r"\bdeclin(ing|ed)?\b", re.IGNORECASE),
    re.compile(r"\bsemester[s]?\s+(over|by|to)?\s*semester[s]?\b", re.IGNORECASE),
    re.compile(r"\bchanged?\b", re.IGNORECASE),
]

_PERFORMANCE_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bperform(ance|ing)?\b", re.IGNORECASE),
    re.compile(r"\bhow\s+am\s+i\s+doing\b", re.IGNORECASE),
    re.compile(r"\bdoing\s+well\b", re.IGNORECASE),
    re.compile(r"\bstanding\b", re.IGNORECASE),
]

_GENERAL_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bstudy\s+tips?\b", re.IGNORECASE),
    re.compile(r"\bhow\s+to\s+study\b", re.IGNORECASE),
    re.compile(r"\bexam\s+prep(aration)?\b", re.IGNORECASE),
    re.compile(r"\bprepare\b", re.IGNORECASE),
    re.compile(r"\btime\s+management\b", re.IGNORECASE),
    re.compile(r"\bmotivat\w*\b", re.IGNORECASE),
]

# ---- What-If override parsing -------------------------------------------------

_ATTENDANCE_RE = re.compile(
    r"attend[a-z]*[^0-9]{0,30}(?:to|at|of|around|about|:=)?\s*(\d{1,3})\s*%",
    re.IGNORECASE,
)
_BACKLOG_CLEAR_RE = re.compile(r"(?:clear|clear\s+up|reduce|remove|finish|work\s+on)\s+(?:\d+\s+)?(?:my\s+)?backlogs?", re.IGNORECASE)
_BACKLOG_ZERO_RE = re.compile(r"backlogs?\s+(?:to\s+|to\s+)?(?:zero|0)\b", re.IGNORECASE)
_MID1_RE = re.compile(r"mid[- ]?term\s*1[^0-9]{0,20}(?:to|=)?\s*(\d{1,3})", re.IGNORECASE)
_MID2_RE = re.compile(r"mid[- ]?term\s*2[^0-9]{0,20}(?:to|=)?\s*(\d{1,3})", re.IGNORECASE)
_MID_BOTH_RE = re.compile(r"(?:mid[- ]?terms?|both\s+mid[- ]?terms?)[^0-9]{0,15}(?:to|=|:)?\s*(\d{1,3})\s*%?", re.IGNORECASE)
_INTERNAL_RE = re.compile(r"internal[^0-9]{0,20}(?:to|=|:)?\s*(\d{1,3})", re.IGNORECASE)
_CGPA_TARGET_RE = re.compile(r"cgpa\s+(?:to\s+|of\s+)?(\d{1,2}(?:\.\d{1,2})?)", re.IGNORECASE)


def _matches_any(text: str, patterns: List[re.Pattern]) -> bool:
    return any(p.search(text) for p in patterns)


def detect_intent(message: str) -> AssistantIntent:
    """Classify a user message into an AssistantIntent deterministically."""
    text = message.strip()
    if not text:
        return AssistantIntent.UNKNOWN

    # Most specific intents first.
    if _matches_any(text, _WHAT_IF_PATTERNS):
        return AssistantIntent.WHAT_IF
    if _matches_any(text, _EXPLAINABILITY_PATTERNS):
        return AssistantIntent.EXPLAINABILITY

    has_risk = _matches_any(text, _RISK_PATTERNS)
    has_backlog = _matches_any(text, _BACKLOG_PATTERNS)
    has_attendance = _matches_any(text, _ATTENDANCE_PATTERNS)
    has_cgpa = _matches_any(text, _CGPA_PATTERNS)
    has_prediction = _matches_any(text, _PREDICTION_PATTERNS)

    if has_prediction and not (has_risk or has_attendance or has_backlog):
        return AssistantIntent.PREDICTION
    if has_risk:
        return AssistantIntent.RISK
    if has_attendance and not has_backlog:
        return AssistantIntent.ATTENDANCE
    if has_backlog:
        return AssistantIntent.BACKLOG
    if _matches_any(text, _TREND_PATTERNS):
        return AssistantIntent.TREND
    if _matches_any(text, _GENERAL_PATTERNS):
        return AssistantIntent.GENERAL_ACADEMIC_GUIDANCE
    if _matches_any(text, _RECOMMENDATION_PATTERNS):
        return AssistantIntent.RECOMMENDATION
    if has_cgpa:
        return AssistantIntent.CGPA
    if _matches_any(text, _PERFORMANCE_PATTERNS):
        return AssistantIntent.PERFORMANCE
    return AssistantIntent.UNKNOWN


def parse_what_if_overrides(message: str) -> Dict[str, object]:
    """
    Best-effort extraction of hypothetical overrides from a What-If question.

    Returns a dict keyed by CGPAPredictionRequest fields (attendance_percentage,
    backlogs, mid_1, mid_2, internal_marks, previous_cgpa). Unsupported or
    unparseable factors are simply omitted so the What-If engine falls back to
    the student's verified baseline for them.
    """
    text = message.strip()
    overrides: Dict[str, object] = {}

    att_match = _ATTENDANCE_RE.search(text)
    if att_match:
        val = float(att_match.group(1))
        if 0.0 <= val <= 100.0:
            overrides["attendance_percentage"] = val

    if _BACKLOG_CLEAR_RE.search(text) or _BACKLOG_ZERO_RE.search(text):
        overrides["backlogs"] = 0

    mid1_match = _MID1_RE.search(text)
    mid2_match = _MID2_RE.search(text)

    if mid1_match:
        overrides["mid_1"] = min(100.0, float(mid1_match.group(1)))
    if mid2_match:
        overrides["mid_2"] = min(100.0, float(mid2_match.group(1)))

    # Only apply the "both mid-terms" rule when neither specific one was given.
    if not mid1_match and not mid2_match:
        mid_both = _MID_BOTH_RE.search(text)
        if mid_both:
            val = min(100.0, float(mid_both.group(1)))
            overrides.setdefault("mid_1", val)
            overrides.setdefault("mid_2", val)

    internal_match = _INTERNAL_RE.search(text)
    if internal_match:
        overrides["internal_marks"] = min(100.0, float(internal_match.group(1)))

    cgpa_match = _CGPA_TARGET_RE.search(text)
    if cgpa_match and not _matches_any(text, [_PREDICTION_PATTERNS[0]]):
        val = float(cgpa_match.group(1))
        if 0.0 <= val <= 10.0 and hasattr(cgpa_match, "group"):
            overrides["previous_cgpa"] = val

    return overrides