import { describe, expect, it } from 'vitest';
import { buildPredictionPayload, getLatestRecord } from '../lib/prediction';
import type { Student } from '../types';

const baseStudent: Student = {
  id: 'st-1',
  user_id: 'u-1',
  student_number: 'CS2022001',
  name: 'Alice Johnson',
  gender: 'FEMALE',
  age: 20,
  department_id: 'd-1',
  department_code: 'CS',
  enrollment_year: 2022,
  current_semester: 4,
  cumulative_gpa: 7.4,
  total_credits_earned: 72,
  is_archived: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const fullRecord = {
  id: 'rec-4',
  student_id: 'st-1',
  academic_year: '2024-2025',
  semester: 4,
  attendance_percentage: 84.5,
  previous_cgpa: 7.2,
  mid_1: 78,
  mid_2: 71,
  internal_marks: 80,
  backlogs: 1,
  semester_cgpa: 7.6,
  grade: 'A',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

describe('getLatestRecord', () => {
  it('returns null for an absent or empty history', () => {
    expect(getLatestRecord(null)).toBeNull();
    expect(getLatestRecord({ ...baseStudent, academic_records: [] })).toBeNull();
  });

  it('sorts records by semester and returns the newest', () => {
    const student = {
      ...baseStudent,
      academic_records: [
        { ...fullRecord, id: 'r3', semester: 3 },
        { ...fullRecord, id: 'r4', semester: 4 },
        { ...fullRecord, id: 'r2', semester: 2 },
      ],
    };
    expect(getLatestRecord(student)?.semester).toBe(4);
  });
});

describe('buildPredictionPayload', () => {
  it('returns null payloads when there is no student', () => {
    const { cgpa, risk } = buildPredictionPayload(null);
    expect(cgpa).toBeNull();
    expect(risk).toBeNull();
  });

  it('returns null payloads when a required field is missing', () => {
    const student = {
      ...baseStudent,
      academic_records: [{ ...fullRecord, mid_2: undefined }],
    };
    const { cgpa } = buildPredictionPayload(student);
    expect(cgpa).toBeNull();
  });

  it('maps the latest record into backend-ready payloads', () => {
    const student = { ...baseStudent, academic_records: [fullRecord] };
    const { cgpa, risk } = buildPredictionPayload(student);
    expect(cgpa).toEqual({
      student_number: 'CS2022001',
      gender: 'FEMALE',
      age: 20,
      department_code: 'CS',
      semester: 4,
      attendance_percentage: 84.5,
      previous_cgpa: 7.2,
      mid_1: 78,
      mid_2: 71,
      internal_marks: 80,
      backlogs: 1,
    });
    expect(risk).toEqual(cgpa);
  });

  it('falls back to cumulative_gpa when previous_cgpa is absent', () => {
    const student = {
      ...baseStudent,
      academic_records: [{ ...fullRecord, previous_cgpa: undefined }],
    };
    const { cgpa } = buildPredictionPayload(student);
    expect(cgpa?.previous_cgpa).toBe(7.4);
  });
});