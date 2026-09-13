export type InterventionStatus =
  | 'PLANNED'
  | 'SCHEDULED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'FOLLOW_UP_REQUIRED';

export type InterventionCategory =
  | 'ATTENDANCE_SUPPORT'
  | 'BACKLOG_SUPPORT'
  | 'EXAM_PREPARATION'
  | 'SUBJECT_SUPPORT'
  | 'STUDY_PLAN'
  | 'ACADEMIC_COUNSELLING'
  | 'FACULTY_MEETING'
  | 'PERFORMANCE_REVIEW'
  | 'OTHER';

export type InterventionPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type OutcomeStatus = 'IMPROVED' | 'STABLE' | 'DECLINED' | 'INSUFFICIENT_DATA';

export interface InterventionOutcome {
  id: string;
  intervention_id: string;
  measured_at: string;
  previous_risk: string | null;
  current_risk: string | null;
  previous_predicted_cgpa: number | null;
  current_predicted_cgpa: number | null;
  previous_attendance: number | null;
  current_attendance: number | null;
  previous_backlogs: number | null;
  current_backlogs: number | null;
  outcome_status: OutcomeStatus;
  notes: string | null;
  measured_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface IndicatorDelta {
  indicator: string;
  before: string | number | null;
  after: string | number | null;
  delta: string | null;
  status: 'IMPROVED' | 'STABLE' | 'DECLINED' | 'INSUFFICIENT_DATA';
}

export interface BeforeAfterComparison {
  intervention_id: string;
  student_id: string;
  student_name: string;
  student_number: string;
  measured_at: string | null;
  outcome_status: OutcomeStatus;
  observational_statement: string;
  indicators: IndicatorDelta[];
  has_sufficient_data: boolean;
  disclaimer: string;
}

export interface Intervention {
  id: string;
  student_id: string;
  student_name?: string;
  student_number?: string;
  department_name?: string;
  faculty_id?: string | null;
  faculty_name?: string | null;
  category: InterventionCategory;
  title: string;
  description: string;
  reason?: string | null;
  priority: InterventionPriority;
  status: InterventionStatus;
  notes?: string | null;
  source: string;
  related_alert_id?: string | null;
  related_recommendation_id?: string | null;
  scheduled_at?: string | null;
  completed_at?: string | null;
  follow_up_date?: string | null;
  follow_up_notes?: string | null;

  baseline_risk_level?: string | null;
  baseline_predicted_cgpa?: number | null;
  baseline_attendance?: number | null;
  baseline_backlogs?: number | null;

  created_by?: string | null;
  created_at: string;
  updated_at: string;

  outcome?: InterventionOutcome | null;
}

export interface InterventionDetail extends Intervention {
  comparison?: BeforeAfterComparison | null;
}

export interface InterventionListResponse {
  items: Intervention[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface InterventionDashboardStats {
  total_interventions: number;
  active_interventions: number;
  follow_ups_due: number;
  completed_interventions: number;
  improved_count: number;
  stable_count: number;
  declined_count: number;
  insufficient_data_count: number;
}

export interface InterventionCreatePayload {
  student_id: string;
  category: InterventionCategory;
  title: string;
  description: string;
  reason?: string;
  priority?: InterventionPriority;
  status?: InterventionStatus;
  notes?: string;
  source?: string;
  related_alert_id?: string;
  related_recommendation_id?: string;
  scheduled_at?: string;
  follow_up_date?: string;
}

export interface InterventionUpdatePayload {
  category?: InterventionCategory;
  title?: string;
  description?: string;
  reason?: string;
  priority?: InterventionPriority;
  status?: InterventionStatus;
  notes?: string;
  scheduled_at?: string;
  completed_at?: string;
  follow_up_date?: string;
  follow_up_notes?: string;
}

export interface InterventionCompletePayload {
  completion_notes?: string;
  follow_up_date?: string;
  completed_at?: string;
}

export interface InterventionFollowUpPayload {
  follow_up_notes: string;
  status?: InterventionStatus;
  new_follow_up_date?: string;
}

export interface InterventionOutcomePayload {
  current_risk?: string;
  current_predicted_cgpa?: number;
  current_attendance?: number;
  current_backlogs?: number;
  outcome_status?: OutcomeStatus;
  notes?: string;
}
