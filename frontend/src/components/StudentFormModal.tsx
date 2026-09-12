import React, { useState, useEffect } from 'react';
import { Student, Department } from '../types';
import { Modal } from './ui/Modal';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Select } from './ui/Select';
import { Alert } from './ui/Alert';
import { studentApi } from '../services/api';

interface StudentFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  studentToEdit?: Student | null;
  departments: Department[];
  onSuccess: () => void;
}

export const StudentFormModal: React.FC<StudentFormModalProps> = ({
  isOpen,
  onClose,
  studentToEdit,
  departments,
  onSuccess
}) => {
  const isEdit = !!studentToEdit;

  const [studentNumber, setStudentNumber] = useState('');
  const [name, setName] = useState('');
  const [gender, setGender] = useState('OTHER');
  const [age, setAge] = useState('20');
  const [departmentId, setDepartmentId] = useState('');
  const [enrollmentYear, setEnrollmentYear] = useState('2024');
  const [currentSemester, setCurrentSemester] = useState('1');
  const [cumulativeGpa, setCumulativeGpa] = useState('');
  const [totalCredits, setTotalCredits] = useState('0');

  // Initial semester record fields (Add mode only)
  const [includeInitialRecord, setIncludeInitialRecord] = useState(true);
  const [academicYear, setAcademicYear] = useState('2024-2025');
  const [attendance, setAttendance] = useState('85.0');
  const [mid1, setMid1] = useState('75.0');
  const [mid2, setMid2] = useState('80.0');
  const [internalMarks, setInternalMarks] = useState('78.0');
  const [backlogs, setBacklogs] = useState('0');
  const [semesterCgpa, setSemesterCgpa] = useState('8.0');
  const [grade, setGrade] = useState('A');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (studentToEdit) {
      setStudentNumber(studentToEdit.student_number);
      setName(studentToEdit.name);
      setGender(studentToEdit.gender);
      setAge(studentToEdit.age.toString());
      setDepartmentId(studentToEdit.department_id);
      setEnrollmentYear(studentToEdit.enrollment_year.toString());
      setCurrentSemester(studentToEdit.current_semester.toString());
      setCumulativeGpa(studentToEdit.cumulative_gpa?.toString() || '');
      setTotalCredits(studentToEdit.total_credits_earned.toString());
      setIncludeInitialRecord(false);
    } else {
      setStudentNumber('');
      setName('');
      setGender('OTHER');
      setAge('20');
      setDepartmentId(departments[0]?.id || '');
      setEnrollmentYear('2024');
      setCurrentSemester('1');
      setCumulativeGpa('');
      setTotalCredits('0');
      setIncludeInitialRecord(true);
    }
    setError(null);
  }, [studentToEdit, departments, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isEdit && studentToEdit) {
        await studentApi.updateStudent(studentToEdit.id, {
          name,
          gender,
          age: parseInt(age, 10),
          department_id: departmentId,
          enrollment_year: parseInt(enrollmentYear, 10),
          current_semester: parseInt(currentSemester, 10),
          cumulative_gpa: cumulativeGpa ? parseFloat(cumulativeGpa) : null,
          total_credits_earned: parseInt(totalCredits, 10)
        });
      } else {
        const payload: any = {
          student_number: studentNumber.trim(),
          name: name.trim(),
          gender,
          age: parseInt(age, 10),
          department_id: departmentId,
          enrollment_year: parseInt(enrollmentYear, 10),
          current_semester: parseInt(currentSemester, 10),
          cumulative_gpa: cumulativeGpa ? parseFloat(cumulativeGpa) : (includeInitialRecord ? parseFloat(semesterCgpa) : null),
          total_credits_earned: parseInt(totalCredits, 10)
        };

        if (includeInitialRecord) {
          payload.initial_academic_record = {
            academic_year: academicYear,
            semester: parseInt(currentSemester, 10),
            attendance_percentage: parseFloat(attendance),
            previous_cgpa: null,
            mid_1: mid1 ? parseFloat(mid1) : null,
            mid_2: mid2 ? parseFloat(mid2) : null,
            internal_marks: internalMarks ? parseFloat(internalMarks) : null,
            backlogs: parseInt(backlogs, 10),
            semester_cgpa: semesterCgpa ? parseFloat(semesterCgpa) : null,
            grade: grade || null,
            historical_risk_level: parseFloat(attendance) < 65 || parseInt(backlogs, 10) > 1 ? 'HIGH' : 'LOW'
          };
        }

        await studentApi.createStudent(payload);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Operation failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const deptOptions = departments.map((d) => ({
    value: d.id,
    label: `${d.code} — ${d.name}`
  }));

  const genderOptions = [
    { value: 'MALE', label: 'Male' },
    { value: 'FEMALE', label: 'Female' },
    { value: 'NON_BINARY', label: 'Non-Binary' },
    { value: 'OTHER', label: 'Other' },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? `Edit Student — ${studentToEdit?.name}` : 'Add New Student Record'}
      maxWidth="720px"
    >
      {error && <Alert variant="error">{error}</Alert>}

      <form onSubmit={handleSubmit}>
        <h4 style={{ fontSize: '0.9rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-primary)', marginBottom: '0.8rem' }}>
          1. Student Identity & Program
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
          <Input
            label="Student ID / Roll No"
            value={studentNumber}
            onChange={(e) => setStudentNumber(e.target.value)}
            required
            disabled={isEdit}
            placeholder="STU-2024-001"
          />
          <Input
            label="Full Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="e.g. Jane Doe"
          />
          <Select
            label="Gender"
            options={genderOptions}
            value={gender}
            onChange={(e) => setGender(e.target.value)}
          />
          <Input
            label="Age"
            type="number"
            min="15"
            max="100"
            value={age}
            onChange={(e) => setAge(e.target.value)}
            required
          />
          <Select
            label="Department"
            options={deptOptions}
            value={departmentId}
            onChange={(e) => setDepartmentId(e.target.value)}
            required
          />
          <Input
            label="Enrollment Year"
            type="number"
            min="2000"
            max="2100"
            value={enrollmentYear}
            onChange={(e) => setEnrollmentYear(e.target.value)}
            required
          />
          <Input
            label="Current Semester (1-12)"
            type="number"
            min="1"
            max="12"
            value={currentSemester}
            onChange={(e) => setCurrentSemester(e.target.value)}
            required
          />
          <Input
            label="Actual Cumulative CGPA"
            type="number"
            step="0.01"
            min="0"
            max="10"
            value={cumulativeGpa}
            onChange={(e) => setCumulativeGpa(e.target.value)}
            placeholder="e.g. 8.45"
          />
        </div>

        {!isEdit && (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1.5rem', marginBottom: '1rem' }}>
              <input
                type="checkbox"
                id="initRecordCheck"
                checked={includeInitialRecord}
                onChange={(e) => setIncludeInitialRecord(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: 'var(--color-primary)' }}
              />
              <label htmlFor="initRecordCheck" style={{ fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer' }}>
                Include Initial Semester Academic Record (Semester {currentSemester})
              </label>
            </div>

            {includeInitialRecord && (
              <div className="glass-card" style={{ padding: '1rem', marginBottom: '1rem', borderColor: 'var(--border-glass)' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.65rem' }}>
                  <Input label="Academic Year" value={academicYear} onChange={(e) => setAcademicYear(e.target.value)} required />
                  <Input label="Attendance %" type="number" step="0.1" min="0" max="100" value={attendance} onChange={(e) => setAttendance(e.target.value)} required />
                  <Input label="Mid-1" type="number" step="0.1" min="0" max="100" value={mid1} onChange={(e) => setMid1(e.target.value)} />
                  <Input label="Mid-2" type="number" step="0.1" min="0" max="100" value={mid2} onChange={(e) => setMid2(e.target.value)} />
                  <Input label="Internals" type="number" step="0.1" min="0" max="100" value={internalMarks} onChange={(e) => setInternalMarks(e.target.value)} />
                  <Input label="Backlogs" type="number" min="0" value={backlogs} onChange={(e) => setBacklogs(e.target.value)} required />
                  <Input label="Term SGPA" type="number" step="0.01" min="0" max="10" value={semesterCgpa} onChange={(e) => setSemesterCgpa(e.target.value)} />
                  <Input label="Grade" value={grade} onChange={(e) => setGrade(e.target.value)} placeholder="A, A+" />
                </div>
              </div>
            )}
          </>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
          <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
          <Button type="submit" loading={loading}>{isEdit ? 'Save Changes' : 'Create Student'}</Button>
        </div>
      </form>
    </Modal>
  );
};
