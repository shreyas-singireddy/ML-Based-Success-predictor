/**
 * Type definitions for Phase 10: Faculty Intelligence & Academic Intervention Dashboard.
 */

import {
  RiskLevel,
  ExplanationData,
  RecommendationItem,
  ActionPlan,
  RiskFactorDetail,
  SemesterAcademicRecord,
} from './index';

export interface FacultyTopRiskFactor {
  factor_name: string;
  feature_code: string;
  affected_students_count: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
}

export interface FacultyAcademicAlert {
  id: string;
  alert_type: 'ATTENDANCE_CRITICAL' | 'HIGH_BACKLOGS' | 'RISK_ELEVATED' | 'CGPA_DROP' | 'MULTI_RISK';
  severity: 'INFO' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  description: string;
  affected_count: number;
  student_ids: string[];
  recommended_action: string;
}

export interface FacultyOverview {
  students_monitored: number;
  average_current_cgpa: number | null;
  average_predicted_cgpa: number | null;
  risk_distribution: Record<RiskLevel, number>;
  attendance_overview: {
    average_attendance: number | null;
    below_75_count: number;
    below_65_count: number;
  };
  backlog_overview: {
    total_backlogs: number;
    students_with_backlogs: number;
    students_with_backlogs_pct: number;
  };
  performance_categories: Record<string, number>;
  top_risk_factors: FacultyTopRiskFactor[];
  recent_alerts: FacultyAcademicAlert[];
  department_scope: string | null;
  department_name: string | null;
  last_analysis_timestamp: string;
}

export interface FacultyStudentSummary {
  id: string;
  student_number: string;
  name: string;
  department_id: string;
  department_code?: string;
  department_name?: string;
  current_semester: number;
  gender: string;
  current_cgpa: number | null;
  predicted_cgpa: number | null;
  risk_level: RiskLevel;
  risk_score: number;
  priority_score: number;
  priority_tier: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  attendance_percentage: number | null;
  backlogs: number;
  cgpa_trend: 'IMPROVING' | 'STABLE' | 'DECLINING' | 'INSUFFICIENT_DATA';
  top_risk_factors: string[];
  prediction_confidence: number | null;
  confidence_category: string;
  last_evaluated_at: string | null;
}

export interface FacultyStudentListResponse {
  items: FacultyStudentSummary[];
  total: number;
  page: number;
  limit: number;
  pages: number;
  risk_counts: Record<string, number>;
}

export interface GroupedFacultyRecommendations {
  immediate_attention: RecommendationItem[];
  short_term: RecommendationItem[];
  monitor: RecommendationItem[];
}

export interface HistoricalVsPredictedTrend {
  semester_history: Array<{
    semester: number;
    academic_year: string;
    semester_cgpa: number | null;
    attendance: number;
    backlogs: number;
  }>;
  current_cgpa: number | null;
  predicted_cgpa: number | null;
  trend_direction: 'IMPROVING' | 'STABLE' | 'DECLINING' | 'INSUFFICIENT_DATA';
  delta_cgpa: number | null;
  trend_description: string;
}

export interface FacultyStudentDossier {
  student: FacultyStudentSummary;
  academic_history: SemesterAcademicRecord[];
  trend_analysis: HistoricalVsPredictedTrend;
  predicted_cgpa: number | null;
  prediction_confidence: number | null;
  prediction_interval?: Record<string, number> | null;
  feature_summary?: Record<string, any> | null;
  risk_level: RiskLevel;
  risk_score: number;
  risk_factors_breakdown?: RiskFactorDetail[] | null;
  explanation?: ExplanationData | null;
  faculty_explanation_summary: string;
  grouped_recommendations: GroupedFacultyRecommendations;
  action_plan?: ActionPlan | null;
  model_version: string;
  risk_model_version: string;
  evaluated_at: string;
  disclaimer: string;
}

export interface FacultyAnalyticsResponse {
  department_scope: string | null;
  total_students: number;
  risk_distribution: Record<string, number>;
  performance_distribution: Record<string, number>;
  cgpa_distribution: Record<string, number>;
  attendance_distribution: Record<string, number>;
  backlog_distribution: Record<string, number>;
  top_model_risk_factors: FacultyTopRiskFactor[];
  semester_risk_hotspots: Array<{
    semester: number;
    student_count: number;
    high_critical_count: number;
    high_critical_pct: number;
    average_cgpa: number | null;
    average_attendance: number | null;
  }>;
  generated_at: string;
}

export interface FacultyAssistantChatResponse {
  reply: string;
  intent: string;
  scope: string;
  evidence_references: Array<{
    source: string;
    label: string;
    value: string;
  }>;
  data_summary?: Record<string, any> | null;
  disclaimer: string;
}
