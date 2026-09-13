"""
Grounding, anti-injection, and consistency guardrails for the assistant.

Responsibilities:
1. Scan user messages for prompt-injection / jailbreak attempts.
2. Scan LLM outputs for leaked secrets (API keys, system secrets).
3. Validate that any numeric claims the LLM produced match the verified
   Phase 3-8 context values (the assistant may never invent numbers).

The guard is deliberately conservative: any suspicious signal downgrades the
LLM response in favor of a deterministic, verifiably grounded answer.
"""

import re
from dataclasses import dataclass, field
from typing import Collection, List, Optional, Set, Tuple

# ---- Prompt injection / jailbreak signatures --------------------------------
INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"ignore\b[^\n]{0,40}\b(rules?\b|constraints?\b|instructions?\b)", re.IGNORECASE),
    re.compile(r"\b(print|output|display|repeat)\b[^\n]{0,40}\b(system|your|developer|inner|source)\s*(instructions?|prompts?|messages?|text)\b", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above|system|instructions?|rules?)", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"reveal\s+(your|the|system)\s*(instructions?|prompt|rules|logic)?", re.IGNORECASE),
    re.compile(r"show\s*(me\s+|us\s+)?(your\s+|the\s+)?(system\s+)?(instructions?|prompt|rules|source|internal)", re.IGNORECASE),
    re.compile(r"forget\s+(your\s+|all\s+)?(instructions?|rules|training|prompt)", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
    re.compile(r"\bdan\s+(mode|mode on|do anything now)\b", re.IGNORECASE),
    re.compile(r"\bdeveloper\s+mode\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(an?\s+)?(unrestricted|jailbroken|god|superuser|admin|developer)\b", re.IGNORECASE),
    re.compile(r"\bpretend\s+(to\s+be\s+)?(unrestricted|jailbroken|an?\s+admin|a\s+(god|superuser))\b", re.IGNORECASE),
    re.compile(r"access\s+[^\n]{0,40}\b(database|api|admin|all\s+students|records)\b", re.IGNORECASE),
    re.compile(r"(show|list|print|reveal)\s+(me\s+|us\s+)?(all|other|every|any)\s+(students|student|users|records)", re.IGNORECASE),
    re.compile(r"\bapi\s*key\b", re.IGNORECASE),
    re.compile(r"\btoken\b[\s\S]{0,40}\(?(bearer|jwt|secret)\)?", re.IGNORECASE),
    re.compile(r"\bwhat\s+(instructions?|rules|prompts?|guidelines?|prompt\s*text)\s+(were\s+you\s+)?(given|followed?|have|are)\b", re.IGNORECASE),
    re.compile(r"\btell\s+me\s+(your\s+)?(instructions?|internal|system|rules)", re.IGNORECASE),
]

# Common API key prefixes (Gemini AIza..., OpenAI sk-..., generic)
SECRET_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}\b"),
    re.compile(r"\bsk-[0-9A-Za-z_\-]{15,}\b"),
    re.compile(r"\bbearer\s+[0-9A-Za-z._\-]{15,}\b", re.IGNORECASE),
    re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),
]

# Generic numbers that are always safe to mention regardless of context.
GENERIC_ALLOWED = frozenset({0.0, 100.0})

_NUMERIC_TOKEN_RE = re.compile(r"-?\d+(?:\.\d+)?")

# Absolute tolerance per magnitude band: small values (CGPA ~0-10) need tighter
# bounds than percentages (~0-100).
_NUMERIC_TOLERANCE = 0.02
_PERCENT_TOLERANCE = 1.0


@dataclass(frozen=True)
class ScanResult:
    blocked: bool
    reason: Optional[str] = None
    description: str = ""

    @property
    def passed(self) -> bool:
        return not self.blocked


@dataclass(frozen=True)
class ConsistencyReport:
    inconsistent_numbers: Tuple[float, ...] = field(default_factory=tuple)
    matched_count: int = 0

    @property
    def is_consistent(self) -> bool:
        return len(self.inconsistent_numbers) == 0


def _is_close_to_any(value: float, verified: Collection[float]) -> Tuple[bool, float]:
    """Returns (matched, best_tolerance) against the verified values."""
    for v in verified:
        tol = _NUMERIC_TOLERANCE if abs(v) <= 15.0 else _PERCENT_TOLERANCE
        if abs(value - v) <= tol:
            return True, tol
    return False, 0.0


class GroundingGuard:
    """Stateless guardrails for the GenAI assistant pipeline."""

    def scan_user_input(self, text: str) -> ScanResult:
        """Detect prompt-injection / jailbreak attempts in a user message."""
        if not text or not text.strip():
            return ScanResult(blocked=True, reason="EMPTY_MESSAGE", description="Empty input is rejected.")

        for pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                return ScanResult(
                    blocked=True,
                    reason="PROMPT_INJECTION_SUSPECTED",
                    description=f"Input matched a prompt-injection signature: {pattern.pattern}.",
                )

        secret_hit = self.find_secret(text)
        if secret_hit:
            return ScanResult(
                blocked=True,
                reason="SECRET_CREDENTIALS_DETECTED",
                description="Input appeared to contain credential material.",
            )
        return ScanResult(blocked=False)

    def find_secret(self, text: str) -> Optional[str]:
        """Return a redacted label if the text looks like a credential/secrets leak."""
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                return pattern.pattern
        return None

    def contains_configured_secret(self, text: str, configured_secrets: Collection[str]) -> Optional[str]:
        """Check if the text contains any of our configured secrets (keys, JWT secret)."""
        for secret in configured_secrets:
            if secret and len(secret) >= 12 and secret in text:
                return secret
        return None

    def validate_numeric_consistency(
        self,
        text: str,
        verified_numbers: Collection[float],
        generic_allowed: Collection[float] = GENERIC_ALLOWED,
    ) -> ConsistencyReport:
        """
        Verify that every numeric mention in `text` is attributable to a
        verified context value (or a whitelisted generic value).

        Numbers that match no verified value are flagged as potentially
        fabricated so the caller can fall back to a deterministic answer.
        """
        cleaned = text.replace(",", "").replace("%", " ")
        tokens = _NUMERIC_TOKEN_RE.findall(cleaned)
        if not tokens:
            return ConsistencyReport()

        verified_set: Set[float] = set(round(float(v), 3) for v in verified_numbers)
        allowed_set: Set[float] = set(round(float(v), 3) for v in generic_allowed)

        inconsistent: List[float] = []
        matched = 0
        seen: Set[float] = set()

        for raw in tokens:
            try:
                value = round(float(raw), 3)
            except ValueError:
                continue
            if value in seen:
                continue
            seen.add(value)

            if value in allowed_set or value in verified_set:
                matched += 1
                continue
            is_close, _ = _is_close_to_any(value, verified_set)
            if is_close:
                matched += 1
                continue
            # A value that is far from every verified value -> potential fabrication.
            inconsistent.append(value)

        return ConsistencyReport(inconsistent_numbers=tuple(inconsistent), matched_count=matched)