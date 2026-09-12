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
