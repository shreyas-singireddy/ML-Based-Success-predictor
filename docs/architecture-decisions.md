# Student Success Predictor — Architecture Decision Records (ADRs)
**Document Version:** 1.0.0  
**Phase:** 0 (Architecture & Planning)  
**Status:** Approved ADRs  

---

## ADR-001: Backend Framework Selection — Python FastAPI

### Status
Accepted

### Context
The application requires a robust web API capable of serving relational CRUD operations, handling asynchronous I/O, validating complex nested payloads, and integrating directly with machine learning pipelines (Scikit-Learn, XGBoost, SHAP) and GenAI SDKs.

### Alternatives Considered
1. **Django + Django REST Framework (DRF):**
   - *Pros:* Batteries-included, built-in ORM, admin dashboard.
   - *Cons:* Heavyweight, synchronous blocking defaults, awkward integration with modern asynchronous LLM streaming and modern typed Pydantic workflows.
2. **Node.js (Express / NestJS):**
   - *Pros:* High concurrent I/O throughput, unified JavaScript/TypeScript across frontend and backend.
   - *Cons:* Requires separate Python microservice or inter-process IPC/gRPC calls to run Scikit-Learn/XGBoost inference and Python-native GenAI libraries, dramatically increasing operational complexity.
3. **Python FastAPI:**
   - *Pros:* Built on Starlette (async I/O) and Pydantic v2 (type validation), native automatic OpenAPI documentation generation, dependency injection for clean RBAC, and zero IPC overhead when calling Python ML and GenAI routines.

### Decision
Adopt **Python 3.11 with FastAPI** as the single unified backend framework.

### Consequences
- **Positive:** ML models and GenAI SDKs can be executed in-process with zero network overhead. Fast development velocity with high runtime performance. Native OpenAPI schema export.
- **Negative:** Async SQLAlchemy requires careful session management; team must follow clean async/await patterns.

---

## ADR-002: Modular Monolith Architecture vs. Microservices

### Status
Accepted

### Context
Educational institutions require reliable, maintainable software. We must decide whether to decompose the application into microservices (e.g. Auth Service, Student Service, ML Inference Service, GenAI Service) or build a modular monolithic architecture.

### Alternatives Considered
1. **Distributed Microservices:**
   - *Pros:* Independent scaling of ML inference or GenAI workers.
   - *Cons:* High operational overhead, network latency between services, distributed transaction complexities, multiple deployment pipelines, difficult local developer experience.
2. **Modular Monolith (Single Containerized Process with Internal Domain Boundaries):**
   - *Pros:* Single deployment unit, atomic database transactions, zero inter-service network latency, simple local development, clear directory boundaries (`api/`, `services/`, `models/`, `ml/`, `genai/`).
   - *Cons:* Services scale together as a unit.

### Decision
Adopt a **Modular Monolith** architecture. The codebase will be partitioned into isolated domain services within a single backend application, with ML inference loaded in-process.

### Consequences
- **Positive:** Dramatically reduced infrastructure complexity, easier testing, simplified debugging, and fast response times. Can easily be decoupled into microservices later if institutional scale demands it.
- **Negative:** High ML CPU usage could temporarily contend with web threads if not properly threaded or worker-limited (mitigated by running multi-worker Uvicorn configurations).

---

## ADR-003: Database Engine — PostgreSQL 16 with Relational Modeling

### Status
Accepted

### Context
The data domain consists of highly structured, interrelated educational records: students, faculty, departments, courses, term enrollments, attendance percentages, assessment scores, and formal intervention workflows.

### Alternatives Considered
1. **Document Database (MongoDB):**
   - *Pros:* Schema flexibility for diverse course metrics.
   - *Cons:* Lacks native ACID multi-table constraints, prone to orphaned records during enrollment adjustments, poor relational querying across faculty rosters and student records.
2. **PostgreSQL 16 (Relational with JSONB support):**
   - *Pros:* Industry standard ACID transactions, robust foreign key cascades, powerful indexing (B-tree, GIN), and native JSONB columns allowing flexible storage for model hyperparameters, SHAP attribution dictionaries, and What-If simulation inputs.

### Decision
Adopt **PostgreSQL 16** with **SQLAlchemy 2.0** and **Alembic** migrations.

### Consequences
- **Positive:** Uncompromised data integrity, strict relational guarantees, fast analytical queries across semesters, and flexible JSONB support for ML feature vectors.
- **Negative:** Schema changes require managed Alembic migration scripts.

---

## ADR-004: In-Process ML Inference vs. External Dedicated Model Servers

### Status
Accepted

### Context
The system predicts student risk levels and CGPA using tabular machine learning models (XGBoost, Scikit-Learn). We must decide how to execute model inference.

### Alternatives Considered
1. **Dedicated Model Server (Triton / TorchServe / BentoML):**
   - *Pros:* GPU acceleration, dynamic batching, isolated model scaling.
   - *Cons:* Immense overkill for lightweight tabular models (<50 MB memory, sub-15ms CPU inference time); introduces extra network hops and heavy infrastructure dependencies.
2. **In-Process Inference Service (Joblib / Scikit-Learn Pipeline loaded in FastAPI memory):**
   - *Pros:* Sub-millisecond memory lookup, zero network latency, trivial local testing, pipeline serialization with built-in preprocessing.
   - *Cons:* Model artifacts are loaded into Uvicorn worker memory.

### Decision
Implement **In-Process ML Inference** via a singleton `ModelInferenceService` that loads the active `.joblib` pipeline into memory upon application startup.

### Consequences
- **Positive:** Zero latency overhead, no external model server to manage, robust pipeline portability.
- **Negative:** Worker memory usage increases by ~80MB per worker (negligible on modern servers).

---

## ADR-005: Decoupled GenAI Architecture with Strict Grounding

### Status
Accepted

### Context
The application includes an AI Academic Assistant to provide study guidance, explain predictions, and suggest interventions. Generative LLMs are prone to hallucinations (e.g. inventing false grades, calculating erroneous risk metrics, or leaking private peer information).

### Alternatives Considered
1. **End-to-End LLM Predictor (Prompting LLM with Student Data to Predict Risk):**
   - *Pros:* Fast to prompt.
   - *Cons:* Catastrophic lack of determinism, uncontrollable hallucinations, unverified risk scores, impossible to calibrate probabilities or audit.
2. **Decoupled Architecture with Strict Context Grounding:**
   - *Predictive ML* performs deterministic, calibrated risk classification and CGPA regression.
   - *GenAI Layer* is strictly an advisory interface. It receives verified ML predictions, SHAP factors, and student profile facts from the database and operates under strict negative constraints ("Do not calculate grades; do not contradict the ML risk category; provide actionable study strategies").

### Decision
Adopt the **Decoupled Architecture with Strict Context Grounding**. The LLM is strictly prohibited from generating quantitative risk metrics or querying raw database tables directly.

### Consequences
- **Positive:** Elimination of hallucinated grades or conflicting risk assessments. Complete mathematical auditability of predictions, while preserving natural language explanations.
- **Negative:** Requires careful prompt engineering and backend context assembly for every LLM invocation.

---

## ADR-006: Frontend Architecture — React 18 + Vite + TypeScript + Modern CSS Tokens

### Status
Accepted

### Context
The frontend must provide distinct interfaces for Administrators, Faculty, and Students with high aesthetic polish, fast interaction, and strict type safety matching backend API contracts.

### Alternatives Considered
1. **Server-Side Rendered (Next.js / Nuxt):**
   - *Pros:* SEO optimization.
   - *Cons:* System is an authenticated portal behind a login screen; SEO is irrelevant. Adds unnecessary Node server runtime complexity.
2. **React 18 + Vite + TypeScript with Custom CSS Design System:**
   - *Pros:* Instant development HMR, static single-page application (SPA) easily served via Nginx, strict TypeScript interface sharing with backend Pydantic models, custom CSS variable tokens (glassmorphism, vibrant dark/light themes, zero utility-class bloat).

### Decision
Adopt **React 18 + Vite + TypeScript** with a **Custom CSS Token Design System**.

### Consequences
- **Positive:** Blazing fast load times, completely decoupled static build artifact, beautiful bespoke UI without generic framework styles, end-to-end type safety.
- **Negative:** UI components (modals, dropdowns, tables) are crafted cleanly rather than pulled from heavy off-the-shelf component dumps.

---

## ADR-007: Isolation of Counterfactual "What-If" Simulations

### Status
Accepted

### Context
Students and advisors need to simulate hypothetical scenarios (e.g., "What happens if my attendance increases from 65% to 85%?"). We must ensure hypothetical data never contaminates true student records.

### Alternatives Considered
1. **Branching Database Records / Temporary Flags:**
   - *Pros:* Uses existing database queries.
   - *Cons:* Extremely high risk of data corruption, race conditions, or accidental exposure of hypothetical grades as official grades.
2. **In-Memory Deep-Copy & Dedicated Simulation Table:**
   - Real student records are retrieved read-only from PostgreSQL.
   - Overrides are applied strictly in-memory to an isolated feature vector.
   - ML inference runs on the modified vector.
   - The result is stored in an isolated `what_if_simulations` table for user reference and returned directly to the client.

### Decision
Adopt the **In-Memory Deep-Copy with Isolated Simulation Table**.

### Consequences
- **Positive:** Zero risk of database contamination. Official student academic records remain strictly immutable to simulation runs.
- **Negative:** Requires explicit cloning and validation of hypothetical feature vectors.
