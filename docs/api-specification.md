# Student Success Predictor — REST API Specification
**Document Version:** 1.0.0  
**API Prefix:** `/api/v1`  
**Protocol:** HTTPS / JSON  
**Status:** Approved Specification Baseline  

---

## 1. Global API Standards & Protocols

### 1.1 Authentication & Authorization Headers
All protected endpoints require an HTTP `Authorization` header containing a valid Bearer JSON Web Token (JWT):
```http
Authorization: Bearer <access_token>
```

### 1.2 Common Error Response Format
All 4xx and 5xx errors return a standardized JSON structure:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable summary of error",
    "details": [
      {
        "field": "attendance_percentage",
        "issue": "Value must be between 0.00 and 100.00"
      }
    ],
    "timestamp": "2026-09-13T10:15:30Z",
    "path": "/api/v1/predictions/generate"
  }
}
```

### 1.3 Standard HTTP Status Codes
* `200 OK`: Request succeeded, returns requested payload.
* `201 Created`: Resource successfully created, returns created entity.
* `204 No Content`: Successful action with no return payload.
* `400 Bad Request`: Malformed syntax, invalid types.
* `401 Unauthorized`: Missing, expired, or invalid JWT token.
* `403 Forbidden`: Authenticated user lacks RBAC role or resource ownership.
* `404 Not Found`: Target entity does not exist.
* `409 Conflict`: Unique constraint violation (e.g. email or student_number already exists).
* `422 Unprocessable Entity`: Pydantic schema validation failure.
* `429 Too Many Requests`: Rate limit exceeded.
* `500 Internal Server Error`: Unhandled server exception (sanitized in production).

---

## 2. Authentication & Identity Endpoints (`/api/v1/auth`)

### 2.1 Login & Obtain Tokens
* **Endpoint:** `POST /api/v1/auth/login`
* **Auth Required:** No
* **Allowed Roles:** Public
* **Request:** `application/x-www-form-urlencoded` or `application/json`
```json
{
  "email": "faculty.smith@university.edu",
  "password": "SecurePassword#2026"
}
```
* **Validation:** Email format; password minimum 8 characters.
* **Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "c6a2b8e4-7d52-4f39-93b5-123456789abc",
    "email": "faculty.smith@university.edu",
    "full_name": "Dr. Jane Smith",
    "role": "FACULTY",
    "profile_id": "f8a1b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c"
  }
}
```
*(Also sets HttpOnly cookie `refresh_token` with 7-day expiration)*
* **Error Responses:** `400 Bad Request`, `401 Unauthorized` ("Invalid email or password").

### 2.2 Refresh Access Token
* **Endpoint:** `POST /api/v1/auth/refresh`
* **Auth Required:** No (reads HttpOnly cookie or body refresh token)
* **Allowed Roles:** Public
* **Success Response (200 OK):** New `access_token` and `expires_in`.
* **Error Responses:** `401 Unauthorized` ("Refresh token expired or revoked").

### 2.3 Current User Context
* **Endpoint:** `GET /api/v1/auth/me`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`, `STUDENT`
* **Success Response (200 OK):** Full user identity and associated profile details.

---

## 3. Student Management Endpoints (`/api/v1/students`)

### 3.1 List Students (Filtered & Paginated)
* **Endpoint:** `GET /api/v1/students`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`
* **Query Parameters:**
  - `page` (int, default: 1)
  - `limit` (int, default: 20, max: 100)
  - `department_id` (UUID, optional)
  - `semester` (int, optional)
  - `risk_level` (string: `LOW|MODERATE|HIGH|CRITICAL`, optional)
  - `search` (string: name or student_number, optional)
* **Authorization Scope:**
  - `ADMIN`: Receives system-wide list.
  - `FACULTY`: Filtered strictly to students enrolled in faculty courses or advised cohort.
* **Success Response (200 OK):**
```json
{
  "items": [
    {
      "id": "e3b0c442-98fc-1c14-9af0-2a3b4c5d6e7f",
      "student_number": "STU-2024-0012",
      "full_name": "Alice Johnson",
      "email": "alice.j@university.edu",
      "department_name": "Computer Science",
      "current_semester": 4,
      "cumulative_gpa": 7.45,
      "latest_risk_level": "MODERATE",
      "latest_prediction_date": "2026-09-10T14:22:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 20,
  "pages": 3
}
```

### 3.2 Get Student Detailed Profile
* **Endpoint:** `GET /api/v1/students/{student_id}`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`, `STUDENT`
* **Authorization Enforcement:**
  - `STUDENT`: Permitted *only* if `student_id == current_user.student_profile.id`.
  - `FACULTY`: Permitted if student is assigned to faculty.
  - `ADMIN`: Unrestricted.
* **Success Response (200 OK):** Comprehensive profile with coursework, attendance summary, and term GPA progression.
* **Error Responses:** `403 Forbidden` ("Access to student record denied"), `404 Not Found`.

---

## 4. Academic Records Endpoints (`/api/v1/academic-records`)

### 4.1 Get Student Academic History
* **Endpoint:** `GET /api/v1/academic-records/student/{student_id}`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`, `STUDENT` (Student restricted to own record)
* **Success Response (200 OK):** Array of enrollments, semester SGPA history, attendance records, and internal assessment grades.

### 4.2 Record Continuous Assessment Score
* **Endpoint:** `POST /api/v1/academic-records/assessments`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`
* **Request:**
```json
{
  "enrollment_id": "8a7b6c5d-4e3f-2a1b-0c9d-8e7f6a5b4c3d",
  "assessment_name": "Midterm Exam",
  "assessment_type": "MIDTERM",
  "maximum_marks": 100.0,
  "obtained_marks": 74.5,
  "weightage_percentage": 30.0
}
```
* **Validation:** `obtained_marks <= maximum_marks`, `maximum_marks > 0`.
* **Success Response (201 Created):** Created assessment object.

---

## 5. Machine Learning & Prediction Endpoints (`/api/v1/predictions`)

### 5.0 Direct AI CGPA Prediction (Phase 3 Core)
* **Endpoint:** `POST /api/v1/predictions/cgpa`
* **Auth Required:** No (Open for ad-hoc what-if & institutional inference)
* **Allowed Roles:** Public / Authenticated
* **Description:** Executes active champion ML model (`LinearRegression`, `RandomForest`, or `XGBoost`) using Phase 2 preprocessor artifact to return bounded predicted CGPA and dynamic metadata.
* **Request:**
```json
{
  "attendance_percentage": 82.0,
  "previous_cgpa": 7.40,
  "mid_1": 72.0,
  "mid_2": 76.0,
  "internal_marks": 78.0,
  "backlogs": 0,
  "department_code": "CS",
  "semester": 4,
  "gender": "MALE",
  "age": 20
}
```
* **Success Response (200 OK):**
```json
{
  "predicted_cgpa": 7.82,
  "model_name": "LinearRegression",
  "model_version": "cgpa_v1.0.0",
  "feature_summary": {
    "academic_average": 75.33,
    "attendance_risk_score": 0.0,
    "attendance_risk_category": "NORMAL",
    "internal_average": 0.78,
    "mid_term_average": 74.0,
    "previous_cgpa_trend": 0.0,
    "backlog_severity_score": 0.0,
    "backlog_severity_category": "NONE",
    "academic_stability": 0.0
  },
  "top_feature_contributions": {
    "academic_average": 0.045,
    "previous_cgpa": 0.612
  },
  "status": "success"
}
```
* **Validation Errors (422 Unprocessable Entity):**
  - Attendance $> 100\%$ or $< 0\%$
  - Marks $< 0$ or $> 100$
  - Backlogs $< 0$
  - CGPA $< 0$ or $> 10$

### 5.1 Generate Student Prediction
* **Endpoint:** `POST /api/v1/predictions/generate/{student_id}`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`
* **Description:** Pulls fresh verified academic records, builds feature vector, executes active ML pipeline, calculates SHAP attributions and calibrated confidence.
* **Request Body:** Empty or optional override params for real-time recalculation.
* **Success Response (201 Created):**
```json
{
  "id": "9b1c2d3e-4f5a-6b7c-8d9e-0f1a2b3c4d5e",
  "student_id": "e3b0c442-98fc-1c14-9af0-2a3b4c5d6e7f",
  "model_version": "1.0.0",
  "predicted_cgpa": 6.85,
  "predicted_cgpa_range": { "lower": 6.50, "upper": 7.20 },
  "risk_level": "MODERATE",
  "risk_probabilities": {
    "LOW": 0.15,
    "MODERATE": 0.72,
    "HIGH": 0.11,
    "CRITICAL": 0.02
  },
  "confidence_score": 0.72,
  "confidence_category": "MODERATE",
  "top_influencing_factors": [
    {
      "feature": "attendance_percentage",
      "impact": "NEGATIVE",
      "shap_value": -0.42,
      "human_explanation": "Current attendance (68%) reduces predicted performance."
    },
    {
      "feature": "assignment_completion_rate",
      "impact": "POSITIVE",
      "shap_value": 0.28,
      "human_explanation": "High assignment completion (92%) positively bolsters score."
    }
  ],
  "created_at": "2026-09-13T10:30:00Z"
}
```
* **Error Responses:** `400 Bad Request` ("Insufficient student records for inference"), `404 Not Found`.

### 5.2 Get Student Prediction History
* **Endpoint:** `GET /api/v1/predictions/student/{student_id}`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`, `STUDENT` (Student restricted to own history)
* **Success Response (200 OK):** Paginated chronological list of past predictions.

---

## 6. Counterfactual What-If Simulation Endpoints (`/api/v1/simulations`)

### 6.1 Execute What-If Scenario
* **Endpoint:** `POST /api/v1/simulations/run`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`, `STUDENT`
* **Authorization:** Student can run simulations only for their own profile.
* **Request:**
```json
{
  "student_id": "e3b0c442-98fc-1c14-9af0-2a3b4c5d6e7f",
  "hypothetical_overrides": {
    "attendance_percentage": 88.0,
    "midterm_score": 82.0,
    "assignment_completion_rate": 95.0
  }
}
```
* **Validation:** All override features must fall within physiological/academic boundaries (0–100%).
* **Safety Constraint:** Does **not** modify or overwrite production student records.
* **Success Response (200 OK):**
```json
{
  "simulation_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "baseline": {
    "predicted_cgpa": 6.85,
    "risk_level": "MODERATE"
  },
  "simulated": {
    "predicted_cgpa": 7.40,
    "risk_level": "LOW"
  },
  "delta": {
    "cgpa_improvement": 0.55,
    "risk_reduction": "MODERATE -> LOW"
  },
  "key_drivers": [
    "Improving attendance from 68% to 88% is estimated to contribute +0.38 to CGPA."
  ]
}
```

---

## 7. Generative AI Academic Assistant (`/api/v1/ai`)

### 7.1 Send Grounded Conversation Message
* **Endpoint:** `POST /api/v1/ai/chat`
* **Auth Required:** Yes
* **Allowed Roles:** `STUDENT`
* **Request:**
```json
{
  "conversation_id": "Optional UUID (starts new session if null)",
  "message": "How can I improve my CGPA before the end of this semester?"
}
```
* **Internal Guardrails:**
  - Extracts verified student records & latest ML predictions on backend.
  - Injects factual context into grounded system prompt.
  - Strips PII.
* **Success Response (200 OK):**
```json
{
  "conversation_id": "4b5c6d7e-8f9a-0b1c-2d3e-4f5a6b7c8d9e",
  "reply": "Based on your current academic profile, your strongest area for growth is your Data Structures coursework, where attendance currently stands at 68%. If you attend the remaining 6 lab sessions and complete the pending practice problems, our predictive models project you could move from a Moderate Risk to a Low Risk category.",
  "grounded_sources": ["Attendance Record: Data Structures", "Prediction: Model v1.0.0"],
  "suggested_actions": [
    "Schedule review session for Data Structures Lab",
    "Run What-If simulation with 85% attendance"
  ]
}
```

### 7.2 Synthesize Personalized Recommendations
* **Endpoint:** `POST /api/v1/ai/recommendations/generate/{student_id}`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`
* **Success Response (201 Created):** Synthesized structured action plan saved to `recommendations` table.

---

## 8. Intervention Workflow Endpoints (`/api/v1/interventions`)

### 8.1 Create Intervention Plan
* **Endpoint:** `POST /api/v1/interventions`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`
* **Request:**
```json
{
  "student_id": "e3b0c442-98fc-1c14-9af0-2a3b4c5d6e7f",
  "prediction_id": "9b1c2d3e-4f5a-6b7c-8d9e-0f1a2b3c4d5e",
  "title": "Mandatory Peer Tutoring & Weekly Check-ins",
  "description": "Student assigned to 2 weekly sessions with senior TA for Algorithms.",
  "intervention_type": "TUTORING",
  "due_date": "2026-11-15"
}
```
* **Success Response (201 Created):** Created intervention object with status `ASSIGNED`.

### 8.2 Update Intervention Status & Outcome
* **Endpoint:** `PATCH /api/v1/interventions/{intervention_id}`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`
* **Request:**
```json
{
  "status": "COMPLETED",
  "outcome_notes": "Student attended 8 of 8 sessions. Midterm score rose from 52 to 74."
}
```
* **Success Response (200 OK):** Updated intervention entity.

---

## 9. Model & Dataset Governance (`/api/v1/models` & `/api/v1/datasets`)

### 9.1 Upload & Validate Dataset
* **Endpoint:** `POST /api/v1/datasets/upload`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`
* **Request:** `multipart/form-data` (CSV or Parquet file + metadata JSON).
* **Validation:** Mandatory columns present, zero duplicate rows, valid data types, schema validation.
* **Success Response (201 Created):** Dataset registered with SHA256 checksum and record count.

### 9.2 List Registered Models & Evaluation Metrics
* **Endpoint:** `GET /api/v1/models`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`
* **Success Response (200 OK):** Returns all registered models, their active status, training datasets, and verified test metrics (Accuracy, ROC-AUC, RMSE, F1).

### 9.3 Activate Model for Production Inference
* **Endpoint:** `POST /api/v1/models/{model_id}/activate`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`
* **Success Response (200 OK):** Sets target model `is_active = TRUE` and deactivates former production pipeline. Logs to `audit_logs`.

---

## 10. Institutional Analytics Endpoints (`/api/v1/analytics`)

### 10.1 Get Institutional Risk Distribution
* **Endpoint:** `GET /api/v1/analytics/risk-distribution`
* **Auth Required:** Yes
* **Allowed Roles:** `ADMIN`, `FACULTY`
* **Query Parameters:** `department_id`, `semester`
* **Success Response (200 OK):**
```json
{
  "total_students_assessed": 1240,
  "distribution": {
    "LOW": 820,
    "MODERATE": 280,
    "HIGH": 110,
    "CRITICAL": 30
  },
  "department_breakdown": [
    {
      "department_name": "Computer Science",
      "critical_count": 8,
      "high_count": 25
    }
  ]
}
```
