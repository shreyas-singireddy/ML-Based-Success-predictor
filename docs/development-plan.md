# Student Success Predictor — Multi-Phase Development Roadmap
**Document Version:** 1.0.0  
**Phase:** 0 (Architecture & Planning)  
**Status:** Approved Roadmap Baseline  

---

## 1. Roadmap Overview & Phased Strategy

To guarantee engineering excellence, prevent premature complexity, and eliminate rework, the implementation of the **Student Academic Performance & CGPA Prediction System** is partitioned into six distinct, sequentially gated phases.

Each phase has strict entry criteria, concrete implementation objectives, measurable verification steps, and automated acceptance gates.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 0: Architecture & Planning (CURRENT)                                                  │
│ Baseline architecture, schema, REST API, RBAC, ML/GenAI guardrails, deployment topology   │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Backend Foundation & Database Layer                                                │
│ FastAPI core, SQLAlchemy models, Alembic migrations, Seed data, Auth/RBAC, Unit tests       │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: ML Pipeline & Inference Service                                                    │
│ Feature engineering, Scikit-Learn/XGBoost training, Calibration, SHAP explainer, Registry   │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Business Logic Services, What-If Engine & GenAI                                    │
│ Student/Academic CRUD, Prediction API, What-If simulation, Grounded AI Assistant (No Halluc)│
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: Frontend Development (React + TypeScript)                                          │
│ Auth UI, Admin Portal, Faculty Advisory Cockpit, Student Dashboard & Simulation Console    │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: Integration, End-to-End Testing & Security Hardening                              │
│ Integration tests, OWASP vulnerability audit, RBAC boundary verification, Load testing       │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 6: Production Packaging & DevOps Deployment                                           │
│ Multi-stage Dockerfiles, Docker Compose production stack, CI/CD pipeline, Monitoring/Alerts  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Phase Specifications

### Phase 1: Backend Foundation & Database Layer
* **Objective:** Establish the core application runtime, database models, database migrations, authentication, and RBAC authorization infrastructure.
* **Key Tasks:**
  1. Initialize `backend/` directory structure with modular FastAPI application (`backend/app/`).
  2. Implement SQLAlchemy 2.0 ORM models as specified in `docs/database-design.md`.
  3. Configure Alembic migration environment; generate initial migration `001_initial_schema.py`.
  4. Implement authentication system:
     - Password hashing with `bcrypt` / `passlib` or `argon2-cffi`.
     - JWT token generator and validator (short-lived access tokens + refresh tokens).
     - FastAPI dependencies: `get_current_user`, `require_roles(Role.ADMIN, Role.FACULTY, Role.STUDENT)`.
  5. Implement database seeder script (`scripts/seed_db.py`) providing:
     - 1 Admin user, 3 Faculty users, 25 Student users.
     - 4 Departments, 12 Courses, complete enrollments, attendance, and assessment records.
  6. Write automated unit tests for authentication and RBAC boundary enforcement (`backend/tests/unit/test_auth.py`).
* **Exit Gate:** All Alembic migrations run cleanly up and down; test suite passes with >90% code coverage on core auth/RBAC modules.

---

### Phase 2: ML Pipeline & Model Inference Service
* **Objective:** Construct a modular, verifiable tabular ML training and inference pipeline with strict feature validation, cross-validation, calibrated confidence, and local feature attribution (SHAP).
* **Key Tasks:**
  1. Structure `ml/` workspace:
     - `ml/pipelines/`: Preprocessing, feature transformation, training script, inference pipeline.
     - `ml/registry/`: Versioned model storage for serialized artifacts (`.joblib`) and metadata (`.json`).
  2. Implement feature engineering & preprocessing pipeline using `scikit-learn`:
     - Continuous feature scaling (RobustScaler/StandardScaler).
     - Categorical encoding (OneHotEncoder).
     - Missing value imputation (SimpleImputer with verified domain defaults).
  3. Train baseline and production candidate models on validated student benchmark data:
     - Logistic Regression / Random Forest (Baseline).
     - XGBoost Classifier (Risk Classification: Low, Moderate, High, Critical).
     - Ridge / XGBoost Regressor (CGPA / Score Prediction).
  4. Implement calibration via `CalibratedClassifierCV` to ensure predicted class probabilities match observed empirical frequencies.
  5. Implement TreeSHAP explainability engine to extract top positive and negative local feature drivers for each individual inference.
  6. Package production pipeline artifact with metadata JSON:
     - `model_version`, `training_timestamp`, `dataset_checksum`, `metrics` (Accuracy, F1-macro, ROC-AUC, RMSE), `feature_names`.
  7. Implement in-memory `ModelInferenceService` inside `backend/app/services/ml_service.py` to serve real-time predictions without spinning up separate heavy microservices.
  8. Write ML unit tests (`ml/tests/test_pipeline.py`) validating zero data leakage and invariant input handling.
* **Exit Gate:** Model artifact saved in `ml/registry/`; inference service returns valid probabilities, confidence intervals, and SHAP attributions within <30ms latency.

---

### Phase 3: Business Logic, What-If Simulation & GenAI Integration
* **Objective:** Implement application services, REST endpoints, counterfactual What-If simulation engine, and grounded AI assistant without hallucinations.
* **Key Tasks:**
  1. Implement CRUD controllers and service layers:
     - Student profile service (`/api/v1/students`).
     - Academic coursework and attendance service (`/api/v1/academic-records`).
     - Intervention tracking service (`/api/v1/interventions`).
     - Institutional analytics service (`/api/v1/analytics`).
  2. Implement Prediction Controller (`/api/v1/predictions/generate/{student_id}`):
     - Dynamically extracts latest student records from database.
     - Dispatches to `ModelInferenceService`.
     - Persists results to `predictions` table with audit metadata.
  3. Implement Counterfactual "What-If" Simulation Engine (`/api/v1/simulations/run`):
     - Merges current student baseline with hypothetical overrides *in-memory*.
     - Disallows writes to `student_profiles` or `course_enrollments`.
     - Returns comparative delta (CGPA shift, risk mitigation status).
  4. Implement Grounded GenAI Service (`genai/` and `backend/app/services/ai_service.py`):
     - Strict prompt templates with prompt-injection defense.
     - Context injector: Feeds only verified DB records and active ML prediction/SHAP outputs.
     - Negative constraints: LLM is banned from creating numerical scores or changing risk classifications.
     - Structured JSON response parsing via Pydantic (`AIInterventionPlan`).
* **Exit Gate:** All Phase 3 REST endpoints conform strictly to `docs/api-specification.md`; What-If simulations never contaminate database records; GenAI generates grounded recommendations matching active student context.

---

### Phase 4: Frontend Development (React + TypeScript)
* **Objective:** Build a responsive, accessible, role-tailored frontend client delivering intuitive interfaces for Administrators, Faculty Advisors, and Students.
* **Key Tasks:**
  1. Initialize `frontend/` with Vite + React 18 + TypeScript.
  2. Implement core design system:
     - Modern CSS design tokens (`frontend/src/styles/design-tokens.css`).
     - Reusable component library: Cards, Data Tables, Modal Dialogs, Risk Badges, Metric Charts (Chart.js / Recharts), Form Inputs.
  3. Implement Authentication & State Management:
     - JWT token persistence and Axios/Fetch interceptor for auto-attaching Bearer headers and handling 401 token refreshes.
     - Role-based route guard (`ProtectedRoute.tsx`).
  4. Implement Role-Specific Portals:
     - **Admin Portal:** User management, student roster, dataset upload with checksum verification, model registry viewer with metrics comparison, system audit log.
     - **Faculty Portal:** Assigned student roster, risk triage filter (Critical/High/Moderate/Low), individual student academic drill-down, on-demand prediction trigger, intervention management console.
     - **Student Portal:** Self-performance dashboard, predicted CGPA interval, risk gauge, interactive What-If simulation sliders, grounded AI Academic Assistant chat interface.
* **Exit Gate:** Frontend builds cleanly without TypeScript or lint errors; all role views function with mock or live backend APIs; responsive design verified on mobile and desktop viewports.

---

### Phase 5: Integration, End-to-End Testing & Security Hardening
* **Objective:** Perform end-to-end system integration, rigorous security auditing, role boundary validation, and load testing.
* **Key Tasks:**
  1. Develop API integration test suite (`backend/tests/integration/`):
     - Test complete student lifecycle: Enrollment -> Assessment -> Prediction -> Intervention -> Re-assessment.
  2. Security & RBAC Penetration Testing:
     - Verify Student A cannot fetch Student B's records via URL tampering (`/api/v1/students/{student_b_id}`).
     - Verify Faculty cannot access Admin user management or dataset upload endpoints.
     - Test SQL injection immunity on search filters.
     - Test GenAI prompt injection resilience (e.g. attempting to extract system prompt or other student records).
  3. Performance & Stress Testing:
     - Measure API latency under concurrent load (target: <100ms for standard endpoints, <200ms for prediction inference).
* **Exit Gate:** 100% of integration and security test cases pass; zero critical/high OWASP vulnerabilities.

---

### Phase 6: Production Packaging & DevOps Deployment
* **Objective:** Package the multi-tier application into optimized, production-ready container images with production configuration and health checking.
* **Key Tasks:**
  1. Multi-stage `Dockerfile` for backend (Python minimal slim base, non-root user, optimized wheels).
  2. Multi-stage `Dockerfile` for frontend (Node build stage -> Nginx Alpine serving static bundle).
  3. Production `deployment/docker-compose.yml` orchestrating:
     - `postgres` with health check and persistent storage volume.
     - `backend` running Uvicorn workers.
     - `frontend` reverse-proxied via Nginx.
  4. Configure production environment templates (`.env.production.example`).
  5. Setup database backup and restore scripts (`scripts/backup_db.sh`).
* **Exit Gate:** `docker compose up` starts the entire system from scratch cleanly; migrations run automatically; health checks return `200 OK`.
