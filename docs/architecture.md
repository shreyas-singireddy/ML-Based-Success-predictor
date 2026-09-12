# Student Success Predictor — System Architecture Specification
**Document Version:** 1.0.0  
**Phase:** 0 (Architecture & Planning)  
**Status:** Approved Architecture Baseline  

---

## 1. Executive Summary & System Mission

The **Student Academic Performance & CGPA Prediction System** is an enterprise-grade educational intelligence platform. It bridges historical academic performance tracking with predictive machine learning and grounded Generative AI to provide:
1. **Early Risk Identification:** Early warning signals for students at risk of academic failure, probation, or dropping out.
2. **Performance & CGPA Forecasting:** Calibrated classification (Risk Categories: *Low, Moderate, High, Critical*) and regression (Estimated CGPA / Final Grade ranges) based on longitudinal attendance, continuous assessment, engagement, and historical coursework data.
3. **Actionable Interventions:** Role-specific workflows enabling faculty and advisors to assign, monitor, and measure personalized academic interventions.
4. **Student Self-Empowerment:** A student portal featuring secure performance tracking, counterfactual "What-If" simulations, and a grounded AI Academic Assistant that generates study plans without hallucinating grades or exposing peer data.

---

## 2. High-Level System Architecture

The system is organized as a modular, containerized multi-tier web application designed for high reliability, strict role-based access control, reproducible ML inference, and grounded GenAI orchestration.

```
                                  ┌─────────────────────────────┐
                                  │      Client Tier (Web)      │
                                  │   React 18 + TypeScript     │
                                  │  Role-Specific Portals      │
                                  └──────────────┬──────────────┘
                                                 │
                                                 │ HTTPS / REST (JSON)
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │  API Gateway & Reverse Proxy│
                                  │      Nginx (TLS / SSL)      │
                                  └──────────────┬──────────────┘
                                                 │
                                                 │ Reverse Proxy
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 Backend Application Tier (FastAPI)                      │
│                                                                                         │
│  ┌───────────────────────┐  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │   Auth & RBAC Module  │  │ Student Data Service │  │  Academic Records Service    │  │
│  │  OAuth2 / JWT Bearer  │  │ Profile & Ownership  │  │  Attendance, Assessments     │  │
│  └───────────────────────┘  └──────────────────────┘  └──────────────────────────────┘  │
│                                                                                         │
│  ┌───────────────────────┐  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │  Intervention Service │  │ Analytics & Reporting│  │ Audit & Compliance Service   │  │
│  │ Action Plans & Logs   │  │ Institution Metrics  │  │ Immutable Activity Logger    │  │
│  └───────────────────────┘  └──────────────────────┘  └──────────────────────────────┘  │
│                                                                                         │
│  ┌─────────────────────────────────────────────────┐  ┌──────────────────────────────┐  │
│  │            ML Inference Service                 │  │       GenAI Engine           │  │
│  │  - Pipeline Preprocessor                        │  │  - Grounded Context Injector │  │
│  │  - Model Registry Loader (.joblib/.onnx)        │  │  - Prompt Safety Guards      │  │
│  │  - Calibrated Confidence Scorer                 │  │  - Study Plan Generator      │  │
│  │  - SHAP Feature Attribution Explainer           │  │  - LLM Adapter (Gemini/OpenAI)│ │
│  └─────────────────────────────────────────────────┘  └──────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────────┬───────────────┘
                               │                                          │
                               ▼                                          ▼
┌────────────────────────────────────────────────┐  ┌─────────────────────────────────────┐
│          Database Tier (PostgreSQL 16)         │  │       Storage Tier & Registry       │
│  - Relational Core (Users, Students, Courses)  │  │  - Model Registry (Pipelines/JSON)  │
│  - Academic Records & Interventions            │  │  - Dataset Version Storage (CSV/PQT)│
│  - Prediction History & Audit Logs             │  │  - Local Object/Blob Storage        │
└────────────────────────────────────────────────┘  └─────────────────────────────────────┘
```

---

## 3. Technology Stack & Technical Justifications

| Component | Selected Technology | Technical Justification |
| :--- | :--- | :--- |
| **Backend Framework** | **Python 3.11 + FastAPI** | Native async capabilities, high performance (Starlette/Uvicorn), automatic OpenAPI (Swagger) generation, native Pydantic v2 data validation, and seamless direct integration with Python ML/AI ecosystem without inter-process IPC overhead. |
| **Data Persistence** | **PostgreSQL 16 + SQLAlchemy 2.0 + Alembic** | Enterprise relational integrity, ACID transactions, robust foreign key cascades, JSONB support for flexible simulation parameters, and migration reliability through Alembic. |
| **Predictive ML** | **Scikit-Learn, XGBoost, LightGBM, SHAP, Joblib** | Industry-standard tabular ML stack. Scikit-learn pipelines guarantee identical transformations across training and inference; tree-based algorithms (XGBoost/LightGBM) excel on tabular academic data; SHAP provides local feature explainability. |
| **Generative AI** | **Python GenAI SDK / LangChain Core + Pydantic Grounding** | Decoupled LLM integration. Strict grounding ensures the LLM never fabricates predictions; verified backend facts and SHAP explanations are injected into prompt templates. |
| **Frontend Framework**| **React 18 + Vite + TypeScript** | Strict compile-time typing matching backend Pydantic schemas, component modularity, rapid Vite build times, client-side routing, and predictable state management. |
| **Styling & Design**  | **Modern CSS Design System (Custom CSS Variables)** | High-fidelity, responsive, accessible, zero runtime bloat, customizable theme tokens (light/dark modes), glassmorphism accents, and no framework drift. |
| **Authentication**    | **OAuth2 Password Bearer + JWT + Argon2/Bcrypt** | Stateless token authentication with short-lived access tokens (15–30 min) and secure HTTP-only refresh tokens. Role claims embedded in payload. |
| **Containerization**  | **Docker & Docker Compose** | Reproducible multi-service development, staging, and production parity across frontend, backend, PostgreSQL, and testing environments. |

---

## 4. Separation of Concerns & Boundary Enforcement

The architecture enforces strict physical and logical boundaries:

1. **Predictive ML vs. Generative AI Isolation:**
   - **Predictive ML (Deterministic / Calibrated):** Receives numerical and categorical student records, executes deterministic feature transformations, outputs risk category, CGPA prediction interval, confidence probability, and SHAP attribution values.
   - **Generative AI (Synthesizing / Advisory):** Consumes *only* the verified outputs produced by the ML service and student profile data fetched by the backend service. The LLM is **never** permitted to calculate risk scores, predict grades, or access raw database tables directly.

2. **Backend API vs. Frontend Presentation:**
   - The frontend is an untrusted presentation layer. Every role-based UI restriction (e.g., hiding the Admin user management table or masking student records from peers) is **strictly enforced** at the backend controller level through FastAPI dependencies.

3. **Data Ownership & Privacy Boundary:**
   - Students can query exclusively their own records (`WHERE student_id == current_user.student_id`).
   - Faculty can query only students assigned to their departmental courses or advisor rosters.
   - Admins possess system-wide operational permissions, with all queries tracked in immutable audit logs.

---

## 5. End-to-End Data Flows

### A. Academic Prediction & Risk Assessment Flow
```
1. Client (Faculty/Admin/Student) triggers prediction request:
   POST /api/v1/predictions/generate/{student_id}
                                │
2. Backend Authentication & RBAC Check:
   - Validate JWT token & extract user identity.
   - Verify caller has permission to view target student.
                                │
3. Academic Record Aggregation:
   - Backend queries DB: Attendance records, internal assessment scores,
     assignment completion rates, historical term GPAs, backlog counts.
                                │
4. Feature Assembly & Validation:
   - Assemble raw feature vector into StudentFeaturePayload schema.
   - Validate numerical bounds (e.g., attendance: 0-100%, marks: 0-100).
                                │
5. ML Pipeline Execution (In-Process ML Service):
   - Pass vector through loaded Scikit-Learn Preprocessor (imputation, scaling, one-hot encoding).
   - Execute model inference (XGBoost / Random Forest Classifier + Regressor).
   - Generate predicted CGPA range, risk classification, and class probability distribution.
   - Calculate TreeSHAP values for top-3 positive and negative contributors.
                                │
6. Calibrated Confidence Evaluation:
   - If max class probability >= 0.80 -> High Confidence.
   - If 0.60 <= probability < 0.80 -> Moderate Confidence.
   - If probability < 0.60 -> Low Confidence (flagged for human advisor review).
                                │
7. Persistence & Response:
   - Store prediction record in `predictions` table linked to active `model_version`.
   - Log inference audit entry.
   - Return formatted `PredictionResponse` to client.
```

### B. Grounded AI Intervention & Study Guidance Flow
```
1. Client requests AI study recommendation:
   POST /api/v1/ai/generate-study-plan
                                │
2. Grounded Context Assembly (Backend):
   - Retrieve latest verified prediction: Risk Level ("High"), Weak Subject ("Data Structures", 48%).
   - Retrieve SHAP top factors: "Low attendance in lab sessions (-0.24 SHAP effect)".
   - Retrieve verified curriculum syllabus topics for Weak Subject.
                                │
3. Prompt Sanitization & Guardrails:
   - Strip all PII (Name, Email, Student ID replaced with anonymous context tokens).
   - Inject context into strict System Prompt Template with negative constraints:
     "Do not calculate new grades. Do not contradict risk level 'High'.
      Provide 4 concrete, actionable study steps for Data Structures."
                                │
4. LLM API Invocation:
   - Call LLM via secure server-side SDK (API key strictly in backend environment).
                                │
5. Response Schema Validation:
   - Parse LLM output into structured Pydantic model (`AIInterventionPlan`).
   - Validate that suggestions reference only grounded context subjects.
                                │
6. Response Delivery:
   - Store generated recommendation in `recommendations` table.
   - Return structured response to student/faculty client.
```

### C. Counterfactual "What-If" Simulation Flow
```
1. Student accesses simulation UI and adjusts hypothetical sliders:
   (e.g., Hypothetical Attendance: 65% -> 85%, Midterm Score: 55 -> 78)
                                │
2. Request Submission:
   POST /api/v1/simulations/run
   Payload: { student_id, hypothetical_overrides: { attendance_rate: 85.0, internal_score: 78.0 } }
                                │
3. Baseline Merging (In-Memory Only):
   - Retrieve baseline student record from DB.
   - Deep-copy baseline and apply overrides.
   - STRICT CONSTRAINT: Do NOT write modified record to student database tables!
                                │
4. Parallel Model Inference:
   - Run active ML pipeline on baseline vector -> Baseline Prediction.
   - Run active ML pipeline on hypothetical vector -> Simulated Prediction.
                                │
5. Delta Calculation:
   - Calculate Delta CGPA (+0.42), Delta Risk Level ("High" -> "Moderate").
   - Extract primary feature drivers responsible for the shift.
                                │
6. Temporary Session Persistence:
   - Save simulation parameters in `what_if_simulations` table for student history.
   - Return comparison payload to UI for side-by-side rendering.
```

---

## 6. Security Architecture & Boundary Matrix

```
┌────────────────────────┬─────────────────────────────────────────────────────────────┐
│ Layer                  │ Security Controls                                           │
├────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Transport / Perimeter  │ TLS 1.3 encryption, CORS whitelist, Security HTTP Headers │
│                        │ (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)        │
├────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Identity & Auth        │ Argon2id/Bcrypt password hashing, OAuth2 Password Bearer,   │
│                        │ Stateless JWT access tokens (RS256/HS256), HttpOnly cookies │
├────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Authorization (RBAC)   │ Declarative FastAPI dependencies (`require_roles`),         │
│                        │ Row-Level Ownership filtering (Student/Faculty boundaries)  │
├────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Application / Input    │ Strict Pydantic v2 schema validation, SQL Injection immunity│
│                        │ via SQLAlchemy parameterization, Rate Limiting (slowapi)    │
├────────────────────────┼─────────────────────────────────────────────────────────────┤
│ GenAI Guardrails       │ PII stripping, prompt injection sanitization, system        │
│                        │ instruction grounding, strict JSON schema output validation │
├────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Audit & Logging        │ Structured JSON logging, masked sensitive fields (passwords,│
│                        │ tokens), immutable audit log table for admin/prediction ops │
└────────────────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 7. Operational & Deployment Architecture

1. **Local Development Environment:**
   - Fully containerized via `deployment/docker-compose.yml`.
   - Services:
     - `db`: PostgreSQL 16 on internal network with persistent volume.
     - `backend`: FastAPI with hot-reloading (Uvicorn).
     - `frontend`: Vite React dev server with proxy to backend.
2. **Production Deployment Topology:**
   - Nginx reverse proxy handling SSL termination and static asset caching.
   - Backend running multi-worker Uvicorn managed by Gunicorn process manager.
   - PostgreSQL running on managed database instance with daily automated backups.
   - Model storage hosted on local persistent volume or object store (S3/GCS compatible).
