export type UserRole = 'ADMIN' | 'FACULTY' | 'STUDENT';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  profile_id?: string;
}

export interface Department {
  id: string;
  code: string;
  name: string;
  created_at: string;
}

export type Gender = 'MALE' | 'FEMALE' | 'OTHER' | 'NON_BINARY';

export interface SemesterAcademicRecord {
  id: string;
  student_id: string;
  academic_year: string;
  semester: number;
  attendance_percentage: number;
  previous_cgpa?: number;
  mid_1?: number;
  mid_2?: number;
  internal_marks?: number;
  backlogs: number;
  semester_cgpa?: number;
  grade?: string;
  historical_risk_level?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Student {
  id: string;
  user_id?: string;
  student_number: string;
  name: string;
  gender: Gender;
  age: number;
  department_id: string;
  department_code?: string;
  department_name?: string;
  enrollment_year: number;
  current_semester: number;
  cumulative_gpa?: number;
  total_credits_earned: number;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  academic_records?: SemesterAcademicRecord[];
}

export interface StudentListResponse {
  items: Student[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface CSVPreviewItem {
  row_number: number;
  is_valid: boolean;
  is_duplicate_in_file: boolean;
  is_existing_in_db: boolean;
  student_id: string;
  name: string;
  gender: string;
  age?: number;
  department_code: string;
  semester?: number;
  academic_year: string;
  attendance?: number;
  previous_cgpa?: number;
  mid_1?: number;
  mid_2?: number;
  internal_marks?: number;
  backlogs?: number;
  semester_cgpa?: number;
  grade?: string;
  historical_risk_level?: string;
  errors: string[];
}

export interface CSVValidationPreview {
  import_batch_token: string;
  total_rows: number;
  valid_rows_count: number;
  invalid_rows_count: number;
  duplicate_in_file_count: number;
  existing_in_db_count: number;
  preview_items: CSVPreviewItem[];
  errors: Array<{
    row_number: number;
    student_id?: string;
    field: string;
    error_message: string;
    raw_value?: string;
  }>;
  is_ready_for_import: boolean;
}

export interface CSVImportResult {
  total_processed: number;
  created_students: number;
  updated_students: number;
  created_academic_records: number;
  updated_academic_records: number;
  skipped_records: number;
  failed_records: number;
  duplicate_policy_applied: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Phase 5 — Explainable AI Types
// ---------------------------------------------------------------------------

export type ImpactLevel = 'HIGH' | 'MEDIUM' | 'LOW';
export type ContributionDirection = 'positive' | 'negative';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface FeatureContribution {
  feature_name: string;
  display_name: string;
  original_value: number | null;
  unit: string;
  shap_value: number;
  contribution_direction: ContributionDirection;
  impact_level: ImpactLevel;
  is_demographic: boolean;
  student_explanation: string;
}

export interface ExplanationData {
  model_name: string;
  model_version: string;
  model_type: string;
  explainer_type: string;
  explanation_available: boolean;
  task_type: string;
  explained_class: string | null;
  top_factors: FeatureContribution[];
  positive_factors: FeatureContribution[];
  negative_factors: FeatureContribution[];
  base_value: number;
  shap_sum: number;
  top_global_features: Record<string, number>;
  fairness_note: string;
  contains_demographic_factors: boolean;
}

export interface CGPAExplainedResponse {
  predicted_cgpa: number;
  model_name: string;
  model_version: string;
  prediction_context: string;
  feature_summary: Record<string, number | string>;
  top_feature_contributions: Record<string, number> | null;
  status: string;
  explanation: ExplanationData;
}

export interface RiskExplainedResponse {
  predicted_cgpa: number;
  grade: string;
  performance_category: string;
  risk_level: RiskLevel;
  risk_score: number;
  risk_probabilities: Record<RiskLevel, number>;
  risk_factors: Array<{
    factor_name: string;
    display_name: string;
    value: number | string;
    score: number;
    severity: string;
    description: string;
  }>;
  model_name: string;
  model_version: string;
  prediction_context: string;
  status: string;
  explanation: ExplanationData;
}

export interface GlobalImportanceResponse {
  model_name: string;
  model_version: string;
  task_type: string;
  explainer_type: string;
  global_feature_importance: Record<string, number>;
  top_features: Record<string, number>;
  fairness_note: string;
}

// ---------------------------------------------------------------------------
// Phase 3 — CGPA Prediction API Types
// ---------------------------------------------------------------------------

export interface CGPAPredictionRequest {
  attendance_percentage: number;
  previous_cgpa: number;
  mid_1: number;
  mid_2: number;
  internal_marks: number;
  backlogs: number;
  department_code?: string;
  semester?: number;
  gender?: string;
  age?: number;
  student_number?: string;
}

export interface FeatureSummary {
  academic_average: number;
  attendance_risk_score: number;
  attendance_risk_category: string;
  internal_average: number;
  mid_term_average: number;
  previous_cgpa_trend: number;
  backlog_severity_score: number;
  backlog_severity_category: string;
  academic_stability: number;
}

export interface CGPAPredictionResponse {
  predicted_cgpa: number;
  model_name: string;
  model_version: string;
  prediction_context: string;
  feature_summary: FeatureSummary;
  top_feature_contributions: Record<string, number> | null;
  status: string;
}

// ---------------------------------------------------------------------------
// Phase 4 — Academic Risk API Types
// ---------------------------------------------------------------------------

export interface RiskPredictionRequest {
  student_number?: string;
  gender?: string;
  age?: number;
  department_code?: string;
  semester?: number;
  attendance_percentage: number;
  previous_cgpa: number;
  mid_1: number;
  mid_2: number;
  internal_marks: number;
  backlogs: number;
}

export interface RiskFactorDetail {
  factor: string;
  level: string;
  value: number | string;
  detail: string;
}

export interface RiskPredictionResponse {
  predicted_cgpa: number;
  grade: string;
  performance_category: string;
  risk_level: RiskLevel;
  risk_score: number;
  risk_probabilities: Record<RiskLevel, number>;
  risk_factors: RiskFactorDetail[];
  model_name: string;
  model_version: string;
  prediction_context: string;
  status: string;
}

export interface ApiErrorBody {
  error?: {
    code?: string;
    message?: string;
  };
  detail?: string;
}

// ---------------------------------------------------------------------------
// Phase 7 — What-If Academic Simulator Types
// ---------------------------------------------------------------------------

export interface WhatIfHypotheticalInputs {
  attendance_percentage?: number;
  mid_1?: number;
  mid_2?: number;
  internal_marks?: number;
  backlogs?: number;
  previous_cgpa?: number;
}

export interface WhatIfSimulationRequest {
  student_number?: string;
  semester?: number;
  baseline_inputs?: CGPAPredictionRequest;
  hypothetical_inputs: WhatIfHypotheticalInputs;
}

export interface AcademicState {
  attendance_percentage: number;
  mid_1: number;
  mid_2: number;
  internal_marks: number;
  backlogs: number;
  previous_cgpa: number;
  semester: number;
  department_code: string;
}

export interface SimulationOutcome {
  predicted_cgpa: number;
  grade: string;
  performance_category: string;
  risk_level: RiskLevel;
  risk_score: number;
  risk_probabilities: Record<RiskLevel, number>;
  academic_state: AcademicState;
}

export interface FactorDelta {
  factor: string;
  display_name: string;
  baseline_value: number;
  simulated_value: number;
  delta: number;
  unit: string;
}

export interface SimulationDelta {
  cgpa_delta: number;
  cgpa_trend: 'IMPROVED' | 'UNCHANGED' | 'WORSENED';
  risk_score_delta: number;
  risk_transition: string;
  risk_trend: 'IMPROVED' | 'UNCHANGED' | 'WORSENED';
  performance_category_transition: string;
  modified_factors: FactorDelta[];
  overall_impact: 'IMPROVED' | 'UNCHANGED' | 'WORSENED';
}

export interface WhatIfSimulationResponse {
  baseline: SimulationOutcome;
  simulation: SimulationOutcome;
  delta: SimulationDelta;
  model_name: string;
  model_version: string;
  risk_model_name: string;
  risk_model_version: string;
  status: string;
  disclaimer: string;
}

// ---------------------------------------------------------------------------
// Phase 8 — AI Personalized Recommendation Engine Types
// ---------------------------------------------------------------------------

export type RecommendationCategory =
  | 'ATTENDANCE'
  | 'BACKLOG_RECOVERY'
  | 'EXAM_PREPARATION'
  | 'INTERNAL_ASSESSMENT'
  | 'STUDY_IMPROVEMENT'
  | 'CGPA_IMPROVEMENT'
  | 'ACADEMIC_HABITS'
  | 'MAINTAIN_STRENGTH';

export type RecommendationPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type RecommendationSource = 'ACADEMIC_DATA' | 'RISK_POLICY' | 'XAI' | 'WHAT_IF_SIMULATION' | 'COMBINED';
export type ExpectedImpactLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';
export type TimeHorizon = 'THIS_WEEK' | 'NEXT_30_DAYS' | 'LONGER_TERM';

export interface RecommendationEvidence {
  factor: string;
  display_name: string;
  current_value?: number | string | null;
  target_or_threshold?: number | string | null;
  unit: string;
  source: RecommendationSource;
  simulated_value?: number | string | null;
  shap_contribution?: number | null;
  impact_detail?: string | null;
}

export interface RecommendationItem {
  id: string;
  title: string;
  priority: RecommendationPriority;
  category: RecommendationCategory;
  evidence: RecommendationEvidence[];
  action: string;
  expected_impact: ExpectedImpactLevel;
  source: RecommendationSource;
  time_horizon: TimeHorizon;
  risk_factor?: string | null;
  technical_details?: Record<string, any>;
}

export interface ActionPlan {
  this_week: RecommendationItem[];
  next_30_days: RecommendationItem[];
  longer_term: RecommendationItem[];
  simulation_summary?: {
    baseline_predicted_cgpa: number;
    simulated_predicted_cgpa: number;
    cgpa_delta: number;
    baseline_risk_level: string;
    simulated_risk_level: string;
    risk_score_delta: number;
    risk_transition: string;
    overall_impact: string;
    overrides_evaluated?: Record<string, any>;
  } | null;
}

export interface RecommendationRequest {
  student_number?: string;
  semester?: number;
  gender?: string;
  age?: number;
  department_code?: string;
  attendance_percentage?: number;
  previous_cgpa?: number;
  mid_1?: number;
  mid_2?: number;
  internal_marks?: number;
  backlogs?: number;
}

export interface RecommendationResponse {
  student_number?: string;
  student_name?: string;
  predicted_cgpa: number;
  grade: string;
  performance_category: string;
  risk_level: RiskLevel;
  risk_score: number;
  recommendations: RecommendationItem[];
  action_plan: ActionPlan;
  evidence_summary: {
    factors_analyzed: number;
    rules_evaluated: number;
    candidates_generated: number;
    recommendations_returned: number;
    simulation_levers_tested: number;
    shap_evidence_attached: boolean;
  };
  model_version_info: Record<string, string>;
  policy_version: string;
  generated_at: string;
  disclaimer: string;
  status: string;
}

// ---------------------------------------------------------------------------
// Phase 9 — GenAI Academic Assistant Types
// ---------------------------------------------------------------------------

export type AssistantIntent =
  | 'PERFORMANCE'
  | 'PREDICTION'
  | 'RISK'
  | 'EXPLAINABILITY'
  | 'RECOMMENDATION'
  | 'WHAT_IF'
  | 'ATTENDANCE'
  | 'BACKLOG'
  | 'CGPA'
  | 'TREND'
  | 'GENERAL_ACADEMIC_GUIDANCE'
  | 'UNKNOWN';

export type ChatRole = 'user' | 'assistant' | 'system';

export type ChatResponseStatus = 'success' | 'refuted' | 'unavailable' | 'error';

export interface ChatMessageInput {
  role: ChatRole;
  content: string;
  timestamp?: string;
}

export interface EvidenceSourceRef {
  phase: number;
  title: string;
  description: string;
}

export interface ChatResponse {
  message: string;
  intent: AssistantIntent;
  sources_used: string[];
  evidence_references: EvidenceSourceRef[];
  suggested_prompts: string[];
  disclaimer: string;
  generated_at: string;
  status: ChatResponseStatus;
}

export interface AssistantSuggestion {
  prompt: string;
  intent: AssistantIntent;
  label: string;
}

export interface SuggestionsResponse {
  items: AssistantSuggestion[];
  generated_at: string;
}

/** UI model for a single rendered chat turn (superset of backend ChatResponse). */
export interface ChatTurn {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  intent?: AssistantIntent;
  sourcesUsed?: string[];
  evidenceReferences?: EvidenceSourceRef[];
  suggestedPrompts?: string[];
  disclaimer?: string;
  status?: ChatResponseStatus;
  isError?: boolean;
  isTyping?: boolean;
}

