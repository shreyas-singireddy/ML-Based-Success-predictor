# Phase 9 — GenAI Academic Assistant

## 1. Role of this component

The GenAI Academic Assistant is a **conversational reasoning layer** over the
Student Success Predictor. It orchestrates verified results produced by the
existing ML engines and translates them into clear, student-facing language.

> Phase 3, Phase 4, Phase 5, Phase 7 and Phase 8 remain authoritative for their
> respective outputs. The GenAI assistant explains and orchestrates these
> outputs. It never computes, predicts, simulates, or recommends anything.

| Capability | Source of truth | Assistant role |
| --- | --- | --- |
| Predicted CGPA | Phase 3 `prediction_service` | Explains / compares |
| Risk level, score, grade | Phase 4 `academic_risk_service` | Explains / flags drivers |
| Feature attributions | Phase 5 `explanation_service` (SHAP) | Explains in plain language |
| What-If results | Phase 7 `what_if_simulation_service` | Describes the verified delta |
| Recommendations | Phase 8 `recommendation_service` | Prioritizes / summarizes |
| Attendance, marks, backlogs, history | Phase 1/2 database | Quotes verbatim |

## 2. Architecture

```
Student Question
      -> Auth/RBAC (student, own data only)
      -> Prompt-injection scan (GroundingGuard)
      -> Intent detection (intent_detector)
      -> Verified context assembly, intent-scoped (context_builder)
      -> LLM provider (Gemini / OpenAI / Deterministic fallback)
      -> Numeric + secret validation (grounding_guard)
      -> Grounded response + evidence telemetry
```

The LLM has **no direct database, filesystem, shell, or tool access**.
All intelligence arrives as an authorized context payload; the LLM is only
allowed to rephrase it.

## 3. Intent detection & context selection

Intents: `PERFORMANCE`, `PREDICTION`, `RISK`, `EXPLAINABILITY`,
`RECOMMENDATION`, `WHAT_IF`, `ATTENDANCE`, `BACKLOG`, `CGPA`, `TREND`,
`GENERAL_ACADEMIC_GUIDANCE`, `UNKNOWN`.

Context selection is **per-intent and minimal** (`.ContextPolicy`):

| Intent | History | Prediction | Risk | SHAP | Recommendations | Simulation |
| --- | :-: | :-: | :-: | :-: | :-: | :-: |
| PERFORMANCE | yes | yes | — | — | — | — |
| PREDICTION / CGPA | yes | yes | — | — | — | — |
| RISK | — | yes | yes | — | — | — |
| EXPLAINABILITY | — | yes | yes | yes | — | — |
| RECOMMENDATION | — | yes | yes | — | yes | — |
| WHAT_IF | — | yes | yes | — | — | yes |
| ATTENDANCE | yes | yes | yes | — | — | — |
| BACKLOG | yes | yes | yes | — | yes | — |
| TREND | yes | yes | — | — | — | — |
| GENERAL / UNKNOWN | — | — | — | — | — | — |

Only the engines actually needed for the detected intent are invoked, so a
"current CGPA" question never triggers SHAP, recommendations, or the
simulator. General academic questions invoke **no ML engine**.

## 4. Verified context object

`context_builder.build()` resolves the authenticated user's own `StudentProfile`
and latest `SemesterAcademicRecord`, then runs the selected engines. Every
numeric value produced is collected into `verified_numbers` for the grounding
guard. Values are never invented: if an engine is unavailable the corresponding
slice is simply absent and the assistant says so.

## 5. Security model & prompt-injection defense

- Identity derives **only** from the authenticated JWT session; ad-hoc student
  numbers in the message are ignored.
- `GroundingGuard` scans user input for injection/evasion patterns and blocks
  them before any LLM call.
- System prompt forbids: computing numbers, revealing prompts/keys/internals,
  discussing other students, and following conflicting instructions.
- After generation, output is scanned for secrets and checked for numeric
  consistency against `verified_numbers`. Mismatched numbers downgrade the
  response to the deterministic fallback answer.
- The assistant never writes to the database (verified by tests).

## 6. LLM provider configuration

Providers: `gemini`, `openai`, `fallback` (deterministic). Selection is live per
request via `build_provider()`; missing keys silently degrade to the
deterministic engine.

| Variable | Purpose |
| --- | --- |
| `AI_PROVIDER` | `gemini`, `openai`, or `fallback` |
| `AI_MODEL_NAME` | Gemini model (e.g. `gemini-1.5-flash`) |
| `AI_MAX_OUTPUT_TOKENS` | Output cap |
| `AI_TEMPERATURE` | Sampling temperature |
| `AI_RATE_LIMIT_PER_MINUTE` | Per-user per-minute chat limit |
| `GEMINI_API_KEY` | Gemini REST key (never committed, never sent to browser) |
| `OPENAI_API_KEY` | OpenAI key (never committed, never sent to browser) |

## 7. Assistant API

- `POST /api/v1/assistant/chat` — authenticated, students only. Request:
  `{ "message", "conversation_history" }` (message ≤ 1000 chars, history ≤ 20
  turns). Response: `message`, `intent`, `sources_used`,
  `evidence_references`, `suggested_prompts`, `disclaimer`, `status`
  (`success | refuted | unavailable | error`). Returns `403` for
  non-students, `429` on rate-limit, `500` only after graceful internal failure.
- `GET /api/v1/assistant/suggestions` — deterministic personalized starter
  prompts; never invokes the LLM.

## 8. Conversation memory

The client may supply `conversation_history` of recent user/assistant turns.
The service keeps the last 8 turns, strips metadata, truncates each message to
1000 chars, and includes it as **informational only** (never authoritative).
Current backend data always takes precedence over anything in history.

## 9. Failure behavior

Provider timeouts/failures fall back to the deterministic answer built verbatim
from verified context. Missing records, models, or engines produce an explicit
"unavailable" response — never a fabricated one. Injectable or out-of-scope
messages are refused with a clear policy statement.

## 10. Current/Predicted/Simulated distinction

The assistant consistently labels values:

- **CURRENT** — from verified database records.
- **PREDICTED** — from the Phase 3/4 models ("the model predicts…").
- **SIMULATED** — from the Phase 7 simulator ("in this simulation the model
  estimates…").
- **RECOMMENDED** — from the Phase 8 engine.

No causality is claimed from model attributions; predictions are never
presented as guarantees.

## 11. Testing

`backend/tests/test_assistant_*.py` cover: RBAC and student isolation, intent
detection, per-intent context selection, grounding (no invented CGPA/risk/SHAP/
simulation values), numeric validation, prompt injection, zero-mutation, What-If
integration, Phase 8 grounding, rate limits, and failure fallbacks. Frontend
tests cover the chat page, bubbles, prompts, error/loading/empty states, and
responsive markup.

## 12. Production notes

- No API keys or secrets are committed; keys come from environment config.
- Logs record request/intent/latency/provider outcomes only — never full
  private records or conversation content.
- Cache keys (if introduced) and rate-limit keys are scoped per authenticated
  user id.