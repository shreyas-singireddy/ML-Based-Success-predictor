import type {
  CGPAPredictionRequest,
  RiskPredictionRequest,
  SemesterAcademicRecord,
  Student,
} from '../types';

export interface PredictionPayload {
  cgpa: CGPAPredictionRequest | null;
  risk: RiskPredictionRequest | null;
}

/** Returns the most recent semester record, or null. */
export function getLatestRecord(student: Student | null): SemesterAcademicRecord | null {
  if (!student || !student.academic_records || student.academic_records.length === 0) {
    return null;
  }
  return [...student.academic_records].sort((a, b) => b.semester - a.semester)[0];
}

/**
 * Builds the CGPA/Risk request payloads from the student's LATEST verified record.
 *
 * Returns null for a payload when a required backend field is missing so the UI
 * shows an intentional empty state instead of silently substituting fake values.
 */
export function buildPredictionPayload(
  student: Student | null
): PredictionPayload {
  const record = getLatestRecord(student);
  const empty: PredictionPayload = { cgpa: null, risk: null };

  if (!student || !record) return empty;

  const attendance = record.attendance_percentage;
  const previousCgpa = record.previous_cgpa ?? student.cumulative_gpa;
  const mid1 = record.mid_1;
  const mid2 = record.mid_2;
  const internal = record.internal_marks;
  const backlogs = record.backlogs;

  if (
    attendance === null || attendance === undefined ||
    previousCgpa === null || previousCgpa === undefined ||
    mid1 === null || mid1 === undefined ||
    mid2 === null || mid2 === undefined ||
    internal === null || internal === undefined ||
    backlogs === null || backlogs === undefined
  ) {
    return empty;
  }

  const common = {
    student_number: student.student_number,
    gender: student.gender,
    age: student.age,
    department_code: student.department_code ?? undefined,
    semester: record.semester,
  };

  const cgpa: CGPAPredictionRequest = {
    ...common,
    attendance_percentage: Number(attendance),
    previous_cgpa: Number(previousCgpa),
    mid_1: Number(mid1),
    mid_2: Number(mid2),
    internal_marks: Number(internal),
    backlogs: Number(backlogs),
  };

  const risk: RiskPredictionRequest = { ...cgpa };

  return { cgpa, risk };
}