"""
Tests for the deterministic intent detector of the GenAI Academic Assistant.
"""

import pytest

from backend.app.schemas.assistant import AssistantIntent
from backend.app.services.assistant.intent_detector import (
    detect_intent,
    parse_what_if_overrides,
)


@pytest.mark.parametrize(
    "question,expected",
    [
        ("How am I performing this semester?", AssistantIntent.PERFORMANCE),
        ("What is my overall standing?", AssistantIntent.PERFORMANCE),
        ("What is my predicted CGPA?", AssistantIntent.PREDICTION),
        ("What CGPA is predicted for me?", AssistantIntent.PREDICTION),
        ("What is my projected score?", AssistantIntent.PREDICTION),
        ("Is my academic risk high?", AssistantIntent.RISK),
        ("Am I likely to fail?", AssistantIntent.RISK),
        ("What is my risk score?", AssistantIntent.RISK),
        ("Why is my predicted CGPA so low?", AssistantIntent.EXPLAINABILITY),
        ("Explain the factors behind my score", AssistantIntent.EXPLAINABILITY),
        ("What do the SHAP values mean for my prediction?", AssistantIntent.EXPLAINABILITY),
        ("Why is my attendance flagged?", AssistantIntent.EXPLAINABILITY),
        ("What is my attendance percentage?", AssistantIntent.ATTENDANCE),
        ("Do I attend enough classes?", AssistantIntent.ATTENDANCE),
        ("How many backlogs do I have?", AssistantIntent.BACKLOG),
        ("How do I clear my backlog?", AssistantIntent.BACKLOG),
        ("What should I improve first?", AssistantIntent.RECOMMENDATION),
        ("What do you recommend I do?", AssistantIntent.RECOMMENDATION),
        ("Give me advice to improve my CGPA", AssistantIntent.RECOMMENDATION),
        ("What is my CGPA?", AssistantIntent.CGPA),
        ("Show me my current CGPA", AssistantIntent.CGPA),
        ("What happens if I improve my attendance to 80%?", AssistantIntent.WHAT_IF),
        ("If I clear my backlogs, will my score improve?", AssistantIntent.WHAT_IF),
        ("Simulate what happens if I raise my internal marks", AssistantIntent.WHAT_IF),
        ("How has my CGPA trended over time?", AssistantIntent.TREND),
        ("How has my performance changed by semester?", AssistantIntent.TREND),
        ("Do you have study tips?", AssistantIntent.GENERAL_ACADEMIC_GUIDANCE),
        ("How do I prepare for exams?", AssistantIntent.GENERAL_ACADEMIC_GUIDANCE),
        ("hello there", AssistantIntent.UNKNOWN),
        ("What is the meaning of life?", AssistantIntent.UNKNOWN),
    ],
)
def test_detect_intent_categories(question: str, expected: AssistantIntent):
    assert detect_intent(question) == expected


def test_detect_intent_empty_message_is_unknown():
    assert detect_intent("") == AssistantIntent.UNKNOWN
    assert detect_intent("   ") == AssistantIntent.UNKNOWN


def test_what_if_beats_risk_explainability_precedence():
    # "why" triggers EXPLAINABILITY but WHAT_IF is more specific.
    assert detect_intent("If I improve attendance, why would my risk drop?") == AssistantIntent.WHAT_IF


@pytest.mark.parametrize(
    "question,expected",
    [
        ("What happens if I improve my attendance to 80%?", {"attendance_percentage": 80.0}),
        ("If I boost my attendance to 90%, what changes?", {"attendance_percentage": 90.0}),
        ("What if I clear my backlogs?", {"backlogs": 0}),
        ("If I clear backlogs to zero, what happens?", {"backlogs": 0}),
        ("What if my mid-term 1 becomes 72?", {"mid_1": 72.0}),
        ("If my mid terms improve to 80, what is my CGPA?", {"mid_1": 80.0, "mid_2": 80.0}),
        ("What if my internal marks rise to 85?", {"internal_marks": 85.0}),
        ("What happens if I study harder?", {}),
    ],
)
def test_parse_what_if_overrides(question: str, expected: dict):
    overrides = parse_what_if_overrides(question)
    assert overrides == expected


def test_parse_what_if_overrides_no_crash_on_mixed_content():
    overrides = parse_what_if_overrides("What if I improve attendance to 80% and clear 2 backlogs?")
    assert overrides.get("attendance_percentage") == 80.0
    assert overrides.get("backlogs") == 0