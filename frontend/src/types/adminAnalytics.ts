export interface AdminOverviewAnalytics {
  total_students: number;
  active_students: number;
  students_monitored: number;
  average_current_cgpa: number | null;
  average_predicted_cgpa: number | null;
  risk_distribution: Record<string, number>;
  risk_percentages: Record<string, number>;
  students_requiring_attention: number;
  total_departments: number;
  total_faculty: number;
  total_interventions: number;
  completed_interventions: number;
  follow_ups_due: number;
  total_alerts: number;
}

export interface DepartmentRiskItem {
  department_id: string;
  department_name: string;
  department_code: string;
  student_count: number;
  risk_distribution: Record<string, number>;
  high_or_critical_pct: number;
}

export interface SemesterRiskItem {
  semester: number;
  student_count: number;
  risk_distribution: Record<string, number>;
  average_cgpa: number | null;
  average_attendance: number | null;
}

export interface AttendanceVsRiskBucket {
  attendance_bracket: string;
  student_count: number;
  risk_distribution: Record<string, number>;
}

export interface AdminRiskAnalytics {
  risk_distribution: Record<string, number>;
  risk_percentages: Record<string, number>;
  total_high_critical_count: number;
  high_critical_percentage: number;
  department_risk_breakdown: DepartmentRiskItem[];
  semester_risk_breakdown: SemesterRiskItem[];
  attendance_vs_risk: AttendanceVsRiskBucket[];
}

export interface DepartmentPerformanceItem {
  department_id: string;
  department_name: string;
  department_code: string;
  student_count: number;
  average_current_cgpa: number | null;
  average_predicted_cgpa: number | null;
  average_attendance: number | null;
  total_backlogs: number;
  students_with_backlogs: number;
  intervention_count: number;
}

export interface AdminAcademicPerformanceAnalytics {
  overall_cgpa_distribution: Record<string, number>;
  average_current_cgpa: number | null;
  average_predicted_cgpa: number | null;
  average_attendance: number | null;
  attendance_below_75_count: number;
  attendance_below_65_count: number;
  total_backlogs: number;
  students_with_backlogs_count: number;
  students_with_backlogs_pct: number;
  department_performances: DepartmentPerformanceItem[];
}

export interface AdminDepartmentAnalyticsResponse {
  departments: DepartmentPerformanceItem[];
  total_departments: number;
}

export interface AdminSemesterAnalyticsResponse {
  semesters: SemesterRiskItem[];
  total_semesters: number;
}

export interface AdminInterventionsAnalytics {
  total_interventions: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
  completion_rate: number;
  follow_ups_due_count: number;
  outcome_distribution: Record<string, number>;
  measured_students_count: number;
  improved_percentage_of_measured: number;
  observational_statement: string;
}
