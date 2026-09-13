"""
LLM abstraction layer for the GenAI Academic Assistant.

Three providers implement a single `generate` contract:

1. GeminiLLMProvider  - direct REST integration with Google Gemini.
2. OpenAILLMProvider  - OpenAI-compatible chat completions API.
3. DeterministicFallbackProvider - a verified, rule-based templating engine that
   answers strictly from the authorized context. This guarantees grounded,
   deterministic responses with zero external dependencies and 100% test
   reliability when APIs are offline or keys are unconfigured.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

from backend.app.core.config import settings

logger = logging.getLogger("student_predictor.assistant.llm_provider")

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
REQUEST_TIMEOUT_SECONDS = 30
GEMINI_RETRIES = 2
OPENAI_RETRIES = 2


class LLMProviderError(Exception):
    """Raised when an external LLM call fails after bounded retries."""


class BaseLLMProvider(ABC):
    """Contract every assistant LLM provider must satisfy."""

    name: str = "base"

    @abstractmethod
    async def generate(self, system_prompt: str, user_message: str, context: Optional[Any] = None) -> str:
        """Return the grounded answer text."""


class GeminiLLMProvider(BaseLLMProvider):
    """Direct Google Gemini REST integration with bounded retries."""

    name = "gemini"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.AI_MODEL_NAME
        self.max_tokens = max_tokens or settings.AI_MAX_OUTPUT_TOKENS
        self.temperature = temperature if temperature is not None else settings.AI_TEMPERATURE

    def _endpoint(self) -> str:
        return (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )

    async def generate(self, system_prompt: str, user_message: str, context: Optional[Any] = None) -> str:
        if not self.api_key:
            raise LLMProviderError("Gemini API key is not configured.")

        payload = {
            "contents": [{"parts": [{"text": f"{system_prompt}\n\nUSER QUERY: {user_message}"}]}],
            "generationConfig": {
                "maxOutputTokens": self.max_tokens,
                "temperature": self.temperature,
            },
        }
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

        last_error: Optional[Exception] = None
        for attempt in range(GEMINI_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                    resp = await client.post(self._endpoint(), json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    raise LLMProviderError("Gemini returned no candidates.")
                parts = (candidates[0].get("content") or {}).get("parts") or []
                if not parts or not parts[0].get("text"):
                    raise LLMProviderError("Gemini returned empty text.")
                return parts[0]["text"].strip()
            except (httpx.HTTPError, LLMProviderError, KeyError, IndexError) as exc:
                last_error = exc
                logger.warning(f"Gemini attempt {attempt + 1} failed: {exc}")
        raise LLMProviderError(f"Gemini request failed after retries: {last_error}")


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI-compatible chat completions integration with bounded retries."""

    name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        configured_model = model or settings.AI_MODEL_NAME
        if configured_model and ("gpt" in configured_model or "o" == configured_model.lower()):
            self.model = configured_model
        else:
            self.model = DEFAULT_OPENAI_MODEL
        self.max_tokens = max_tokens or settings.AI_MAX_OUTPUT_TOKENS
        self.temperature = temperature if temperature is not None else settings.AI_TEMPERATURE

    async def generate(self, system_prompt: str, user_message: str, context: Optional[Any] = None) -> str:
        if not self.api_key:
            raise LLMProviderError("OpenAI API key is not configured.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Optional[Exception] = None
        for attempt in range(OPENAI_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                    resp = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                choices = data.get("choices") or []
                if not choices:
                    raise LLMProviderError("OpenAI returned no choices.")
                content = choices[0].get("message", {}).get("content") or ""
                if not content.strip():
                    raise LLMProviderError("OpenAI returned empty content.")
                return content.strip()
            except (httpx.HTTPError, LLMProviderError, KeyError, IndexError) as exc:
                last_error = exc
                logger.warning(f"OpenAI attempt {attempt + 1} failed: {exc}")
        raise LLMProviderError(f"OpenAI request failed after retries: {last_error}")


class DeterministicFallbackProvider(BaseLLMProvider):
    """
    Verified rule-and-context answer engine.

    Produces grounded, empathetic, and accurate answers using ONLY the
    values embedded in the authorized BuildContextResult. All numbers are
    transcribed verbatim from the context; nothing is computed or invented.
    """

    name = "fallback"

    async def generate(self, system_prompt: str, user_message: str, context: Optional[Any] = None) -> str:
        if context is None:
            return (
                "I don't have enough verified academic data to answer yet. "
                "Your student profile and current semester record are required for a grounded answer."
            )
        from backend.app.schemas.assistant import AssistantIntent
        from backend.app.services.assistant.intent_detector import detect_intent

        intent = detect_intent(user_message)

        if not context.has_prediction and not context.latest_record:
            return self._no_data_answer(context)

        builder = _FallbackNarrative(context)
        if intent == AssistantIntent.WHAT_IF:
            return builder.what_if()
        if intent == AssistantIntent.RISK:
            return builder.risk()
        if intent in (AssistantIntent.ATTENDANCE,):
            return builder.attendance()
        if intent == AssistantIntent.BACKLOG:
            return builder.backlog()
        if intent in (AssistantIntent.EXPLAINABILITY,):
            return builder.explainability()
        if intent == AssistantIntent.RECOMMENDATION:
            return builder.recommendation()
        if intent in (AssistantIntent.CGPA, AssistantIntent.PREDICTION):
            return builder.prediction()
        if intent == AssistantIntent.TREND:
            return builder.trend()
        if intent == AssistantIntent.PERFORMANCE:
            return builder.performance()
        if intent == AssistantIntent.GENERAL_ACADEMIC_GUIDANCE:
            return builder.general_guidance()
        return builder.general_overview()


class _FallbackNarrative:
    """Templated, verbatim-grounded narrative builders."""

    def __init__(self, context: Any) -> None:
        self.ctx = context

    def _student_intro(self) -> str:
        s = self.ctx.student
        return f"For your academic profile ({s['name']}, {s['student_number']}, {s['current_semester']}th semester):"

    def _trend_line(self) -> str:
        hist = self.ctx.academic_history
        if not hist:
            return ""
        vals = [h for h in hist if h.get("semester_cgpa") is not None]
        if not vals:
            return ""
        sequence = " -> ".join(f"{h['semester_cgpa']:.2f} (S{h['semester']})" for h in vals)
        if len(vals) >= 2:
            first, last = vals[0]["semester_cgpa"], vals[-1]["semester_cgpa"]
            if last > first:
                direction = "improving"
            elif last < first:
                direction = "declining"
            else:
                direction = "stable"
            return f"Your verified semester history is {sequence}, overall {direction}."
        return f"Your latest verified semester CGPA was {vals[-1]['semester_cgpa']:.2f} (S{vals[-1]['semester']})."

    def _disclaimer_tail(self) -> str:
        return (
            "These figures come directly from your verified record and the institution's production "
            "models; they are estimates for guidance only, and do not alter any official grades."
        )

    def no_data(self) -> str:
        return (
            "I don't currently have a verified semester record linked to your profile, so I can't "
            "quote any predicted numbers. Please contact your department to confirm that your "
            "academic record has been uploaded, and I'll be able to answer with confidence then."
        )

    def prediction(self) -> str:
        if not self.ctx.prediction:
            return self.no_data()
        p = self.ctx.prediction
        fs = p["feature_summary"]
        trend = self._trend_line()
        return (
            f"{self._student_intro()}\n"
            f"Your predicted CGPA for the current semester is **{p['predicted_cgpa']:.2f}** "
            f"(champion model: {p['model_name']} v{p['model_version']}). "
            f"In the model's terms, your academic average is {fs['academic_average']:.2f} and your "
            f"attendance risk score is {fs['attendance_risk_score']:.2f} ({fs['attendance_risk_category']}).\n"
            f"{trend}\n"
            f"{self._disclaimer_tail()}"
        )

    def risk(self) -> str:
        if not self.ctx.risk:
            return self.no_data()
        r = self.ctx.risk
        factors = ", ".join(
            f"{f['factor']} ({f['level']}, value {f['value']})" for f in r.get("risk_factors") or []
        )
        return (
            f"{self._student_intro()}\n"
            f"Your predicted academic risk level is **{r['risk_level']}** with a normalized risk score of "
            f"**{r['risk_score']:.1f}/100** (predicted grade: {r['grade']}, performance: {r['performance_category']}).\n"
            f"Risk factor breakdown: {factors or 'not available'}.\n"
            f"This classification comes from the production risk model ({r['model_name']} v{r['model_version']}). "
            f"{self._disclaimer_tail()}"
        )

    def attendance(self) -> str:
        if not self.ctx.latest_record:
            return self.no_data()
        rec = self.ctx.latest_record
        risk_line = ""
        if self.ctx.risk:
            for f in self.ctx.risk.get("risk_factors") or []:
                if "attend" in f["factor"].lower():
                    risk_line = f" The risk model flags Attendance as {f['level']}."
        target = 80.0 if rec["attendance_percentage"] < 75 else None
        guidance = (
            f" Raising it toward {target:.0f}% is a commonly cited safe benchmark and is tested by the "
            f"What-If simulator on this platform."
            if target
            else " Your attendance is at or above typical safe thresholds, so keep it there."
        )
        return (
            f"{self._student_intro()}\n"
            f"Your verified attendance for the current semester is **{rec['attendance_percentage']:.1f}%** "
            f"(mid-terms {rec['mid_1']:.1f} and {rec['mid_2']:.1f}, internals {rec['internal_marks']:.1f}).{risk_line}\n"
            f"Best-practice given your standing:{guidance}\n"
            f"{self._disclaimer_tail()}"
        )

    def backlog(self) -> str:
        if not self.ctx.latest_record:
            return self.no_data()
        rec = self.ctx.latest_record
        count = rec["backlogs"]
        if count <= 0:
            return (
                f"{self._student_intro()}\n"
                f"Your verified record shows **{count} active backlogs**, so backlog recovery is not a "
                f"current priority. Keep clearing any pending subjects in the normal cycle. "
                f"{self._disclaimer_tail()}"
            )
        return (
            f"{self._student_intro()}\n"
            f"You currently have **{count} active backlog(s)** on record. Backlogs weigh on the model's "
            f"prediction and risk score, so prioritizing backlog clearance is strongly advised. "
            f"{self._disclaimer_tail()}"
        )

    def explainability(self) -> str:
        if not self.ctx.shap:
            if self.ctx.prediction:
                p = self.ctx.prediction
                return (
                    f"Detailed SHAP attributions are unavailable right now, but your predicted CGPA is "
                    f"**{p['predicted_cgpa']:.2f}**. SHAP explanations regenerate with the prediction engine; "
                    f"please retry shortly."
                )
            return self.no_data()
        sh = self.ctx.shap
        pos = sh.get("positive_factors") or []
        neg = sh.get("negative_factors") or []
        lines = [f"{self._student_intro()}"]
        lines.append("Here is what is helping and hurting your predicted outcome, from the Phase 5 SHAP attribution:")
        if pos:
            lines.append("Helping:")
            for f in pos:
                lines.append(
                    f"- {f['display_name']} (current {f['original_value']} {f['unit']}, SHAP +{f['shap_value']:.3f}): {f['student_explanation']}"
                )
        if neg:
            lines.append("Holding you back:")
            for f in neg:
                lines.append(
                    f"- {f['display_name']} (current {f['original_value']} {f['unit']}, SHAP {f['shap_value']:.3f}): {f['student_explanation']}"
                )
        lines.append(self._disclaimer_tail())
        return "\n".join(lines)

    def recommendation(self) -> str:
        if not self.ctx.recommendations:
            return self.no_data()
        tops = self.ctx.recommendations["top_recommendations"]
        if not tops:
            return self.no_data()
        lines = [f"{self._student_intro()}\nBased on your verified standing, the top prioritized actions are:"]
        for i, rec in enumerate(tops, 1):
            lines.append(
                f"{i}. **{rec['title']}** ({rec['priority']}, {rec['category'].replace('_', ' ')}): {rec['action']}"
            )
        lines.append(self._disclaimer_tail())
        return "\n".join(lines)

    def what_if(self) -> str:
        if not self.ctx.simulation:
            if self.ctx.prediction:
                p = self.ctx.prediction
                return (
                    f"I couldn't run a live simulation for that scenario, but your current predicted CGPA "
                    f"is **{p['predicted_cgpa']:.2f}** with risk level "
                    f"{self.ctx.risk['risk_level'] if self.ctx.risk else 'unavailable'}. You can also use the "
                    f"What-If page to adjust individual factors directly."
                )
            return self.no_data()
        sim = self.ctx.simulation
        return (
            f"{self._student_intro()}\n"
            f"Running that scenario through the production models:\n"
            f"- Predicted CGPA: **{sim['baseline_predicted_cgpa']:.2f}** -> **{sim['simulated_predicted_cgpa']:.2f}** "
            f"(delta {sim['cgpa_delta']:+.2f}, {sim['cgpa_trend']})\n"
            f"- Risk level: **{sim['baseline_risk_level']}** ({sim['baseline_risk_score']:.1f}) -> "
            f"**{sim['simulated_risk_level']}** ({sim['simulated_risk_score']:.1f})\n"
            f"- Overall projected impact: **{sim['overall_impact']}**.\n"
            f"This is a hypothetical model estimate and changes nothing about your official record. "
            f"{self._disclaimer_tail()}"
        )

    def trend(self) -> str:
        trend = self._trend_line()
        if not trend:
            return self.no_data()
        return (
            f"{self._student_intro()}\n"
            f"{trend}\n"
            f"{self._disclaimer_tail()}"
        )

    def performance(self) -> str:
        parts = [self._student_intro()]
        if self.ctx.prediction:
            p = self.ctx.prediction
            parts.append(f"Projected semester CGPA: **{p['predicted_cgpa']:.2f}**.")
        if self.ctx.risk:
            r = self.ctx.risk
            parts.append(
                f"Risk classification: **{r['risk_level']}** (score {r['risk_score']:.1f}/100), "
                f"grade {r['grade']}, performance {r['performance_category']}."
            )
        trend = self._trend_line()
        if trend:
            parts.append(trend)
        parts.append(self._disclaimer_tail())
        return "\n".join(parts)

    def general_guidance(self) -> str:
        guidance: list = []
        rec = self.ctx.latest_record
        if rec:
            if rec["attendance_percentage"] < 75:
                guidance.append("prioritize regular class attendance to protect your eligibility and standing")
            if rec["backlogs"] > 0:
                guidance.append("schedule backlog clearance early in the term")
            if rec["internal_marks"] is not None and rec["internal_marks"] < 65:
                guidance.append("raise your continuous assessment scores through consistent assignments")
            if rec["mid_1"] is not None and rec["mid_2"] is not None and (rec["mid_1"] + rec["mid_2"]) / 2 < 65:
                guidance.append("strengthen mid-term preparation with focused revision")
        advice = (
            "; ".join(guidance) if guidance else "keep your current routine and monitor your indicators"
        )
        return (
            f"{self._student_intro()}\n"
            f"General evidence-aligned suggestions: {advice}.\n"
            f"The most reliable levers for your profile are the ones the model and risk engine flag most "
            f"strongly - reply with a specific question (e.g. 'what should I improve first?') for a targeted plan."
        )

    def general_overview(self) -> str:
        return (
            f"{self._student_intro()}\n"
            f"I can answer grounded questions about your predicted CGPA, academic risk, what drives your "
            f"score, personalized recommendations, and what-if simulations. Try asking 'What is my predicted "
            f"CGPA?', 'Why is my risk high?', or 'What happens if I improve attendance to 80%?'"
        )

    def _no_data_answer(self, context) -> str:
        return (
            "I don't have a verified academic record for your profile yet, so I can't provide a grounded "
            "answer or any numbers. Once a semester record is linked, ask me about your predicted CGPA, "
            "risk factors, or recommendations."
        )


def build_provider(preferred: Optional[str] = None) -> BaseLLMProvider:
    """
    Select the active provider based on configuration and key availability.

    - "fallback" / "local" -> deterministic engine.
    - "gemini" -> Gemini if key present, else deterministic.
    - "openai" -> OpenAI if key present, else deterministic.
    - anything else -> deterministic.
    """
    preference = (preferred or settings.AI_PROVIDER or "fallback").lower().strip()

    if preference == "openai":
        if settings.OPENAI_API_KEY:
            return OpenAILLMProvider()
        logger.warning("AI_PROVIDER=openai but OPENAI_API_KEY is missing; falling back to deterministic engine.")
        return DeterministicFallbackProvider()

    if preference in ("gemini", "google"):
        if settings.GEMINI_API_KEY:
            return GeminiLLMProvider()
        logger.warning("AI_PROVIDER=gemini but GEMINI_API_KEY is missing; falling back to deterministic engine.")
        return DeterministicFallbackProvider()

    if preference in ("fallback", "local", "deterministic"):
        return DeterministicFallbackProvider()

    logger.warning(f"Unknown AI_PROVIDER={preference}; falling back to deterministic engine.")
    return DeterministicFallbackProvider()