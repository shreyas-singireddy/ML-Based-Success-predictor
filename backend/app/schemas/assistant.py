"""
Pydantic V2 Schemas for Phase 9 GenAI Academic Assistant.

The assistant is a grounded translation layer: it NEVER computes predictions,
risk scores, SHAP values, or recommendations independently. Every numeric
claim is drawn verbatim from verified Phase 3-8 engine outputs provided in the
context. These schemas define the chat contract, structured evidence telemetry,
and intent taxonomy exposed to the frontend.
"""

from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

MAX_HISTORY_MESSAGES = 20
MAX_CHAT_MESSAGE_LENGTH = 2000
MAX_CHAT_REQUEST_LENGTH = 1000


class AssistantIntent(str, Enum):
    """Detected intent taxonomy for routing grounded answers."""

    PERFORMANCE = "PERFORMANCE"
    PREDICTION = "PREDICTION"
    RISK = "RISK"
    EXPLAINABILITY = "EXPLAINABILITY"
    RECOMMENDATION = "RECOMMENDATION"
    WHAT_IF = "WHAT_IF"
    ATTENDANCE = "ATTENDANCE"
    BACKLOG = "BACKLOG"
    CGPA = "CGPA"
    TREND = "TREND"
    GENERAL_ACADEMIC_GUIDANCE = "GENERAL_ACADEMIC_GUIDANCE"
    UNKNOWN = "UNKNOWN"


class ChatRole(str, Enum):
    """Roles accepted inside a conversation history."""
    user = "user"
    assistant = "assistant"
    system = "system"


class ChatMessage(BaseModel):
    """A single conversational turn supplied by the client for context."""

    role: ChatRole
    content: str = Field(..., min_length=1, max_length=MAX_CHAT_MESSAGE_LENGTH)
    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Optional timestamp of the message turn.",
    )

    model_config = ConfigDict(protected_namespaces=())


class ChatRequest(BaseModel):
    """Authenticated chat request payload."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=MAX_CHAT_REQUEST_LENGTH,
        description="Natural-language question from the student.",
        json_schema_extra={"example": "Why is my academic risk high?"},
    )
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        max_length=MAX_HISTORY_MESSAGES,
        description="Prior user/assistant turns used as conversational context (user-provided, never authoritative).",
    )

    model_config = ConfigDict(protected_namespaces=())


class EvidenceSourceRef(BaseModel):
    """Structured citation pointing at the verified engine that produced a fact."""

    phase: int = Field(..., description="Pipeline phase that is the source of truth (2-8).")
    title: str = Field(..., description="Short human-readable source title.")
    description: str = Field(..., description="What the source contributed to the answer.")


class ChatResponse(BaseModel):
    """Grounded assistant answer with full evidence telemetry."""

    message: str = Field(..., description="The generated, grounded answer text.")
    intent: AssistantIntent = Field(default=AssistantIntent.UNKNOWN, description="Detected intent of the user message.")
    sources_used: List[str] = Field(
        default_factory=list,
        description="Phase labels of verified engines actually consulted for this answer.",
    )
    evidence_references: List[EvidenceSourceRef] = Field(
        default_factory=list,
        description="Structured per-phase evidence citations for transparency.",
    )
    suggested_prompts: List[str] = Field(
        default_factory=list,
        description="Deterministic follow-up prompt suggestions.",
    )
    disclaimer: str = Field(
        default=(
            "This assistant is a decision-support translator built on your verified academic record "
            "and production ML outputs. It does not compute or alter any predictions, grades, or "
            "records, and is not a substitute for institutional academic advising."
        ),
        description="Transparency and fairness disclaimer.",
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 generation timestamp.",
    )
    status: str = Field(default="success", description="success | refuted | unavailable | error")

    model_config = ConfigDict(protected_namespaces=())


class AssistantSuggestion(BaseModel):
    """A single personalized starter suggestion derived from the student's real standing."""

    prompt: str = Field(..., description="Natural-language prompt that triggers a grounded answer.", json_schema_extra={"example": "What is my predicted CGPA?"})
    intent: AssistantIntent = Field(default=AssistantIntent.UNKNOWN, description="Intent the prompt will map to.")
    label: str = Field(..., description="Short UI label for the suggestion pill.")


class SuggestionsResponse(BaseModel):
    """Personalized starter suggestions for the chat UI."""

    items: List[AssistantSuggestion] = Field(default_factory=list, description="Ordered list of starter prompts.")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 generation timestamp.",
    )

    model_config = ConfigDict(protected_namespaces=())