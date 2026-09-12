import React, { useState } from 'react';
import { Student, SemesterAcademicRecord } from '../types';
import { Modal } from './ui/Modal';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Alert } from './ui/Alert';
import { studentApi } from '../services/api';
import { Plus, BookOpen, Calendar, Award, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface StudentProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  student: Student | null;
  onRecordAdded?: () => void;
}

export const StudentProfileModal: React.FC<StudentProfileModalProps> = ({
  isOpen,
  onClose,
  student,
  onRecordAdded
}) => {
  const [showAddRecord, setShowAddRecord] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // New semester record state
  const [academicYear, setAcademicYear] = useState('2024-2025');
  const [semester, setSemester] = useState((student?.current_semester || 1) + 1);
  const [attendance, setAttendance] = useState('85.0');
  const [prevCgpa, setPrevCgpa] = useState(student?.cumulative_gpa?.toString() || '');
  const [mid1, setMid1] = useState('75.0');
  const [mid2, setMid2] = useState('80.0');
  const [internalMarks, setInternalMarks] = useState('78.0');
  const [backlogs, setBacklogs] = useState('0');
  const [semesterCgpa, setSemesterCgpa] = useState('8.0');
  const [grade, setGrade] = useState('A');

  if (!student) return null;

  const handleAddRecordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await studentApi.addAcademicRecord(student.id, {
        academic_year: academicYear,
        semester: Number(semester),
        attendance_percentage: parseFloat(attendance),
        previous_cgpa: prevCgpa ? parseFloat(prevCgpa) : null,
        mid_1: mid1 ? parseFloat(mid1) : null,
        mid_2: mid2 ? parseFloat(mid2) : null,
        internal_marks: internalMarks ? parseFloat(internalMarks) : null,
        backlogs: parseInt(backlogs, 10),
        semester_cgpa: semesterCgpa ? parseFloat(semesterCgpa) : null,
        grade: grade || null,
        historical_risk_level: parseFloat(attendance) < 65 || parseInt(backlogs, 10) > 1 ? 'HIGH' : 'LOW'
      });

      setSuccess(`Successfully added Academic Record for Semester ${semester}!`);
      setShowAddRecord(false);
      if (onRecordAdded) onRecordAdded();
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to add academic record';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Student Profile — ${student.name} (${student.student_number})`}
      maxWidth="850px"
    >
      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      {/* Basic Student Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="glass-card" style={{ padding: '1rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Department</span>
          <p style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--color-primary)', marginTop: '0.2rem' }}>
            {student.department_code || student.department_name || 'N/A'}
          </p>
        </div>
        <div className="glass-card" style={{ padding: '1rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Current Semester</span>
          <p style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '0.2rem' }}>
            Semester {student.current_semester}
          </p>
        </div>
        <div className="glass-card" style={{ padding: '1rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Actual CGPA</span>
          <p style={{ fontSize: '1.1rem', fontWeight: 800, color: (student.cumulative_gpa || 0) >= 7.5 ? 'var(--color-success)' : 'var(--color-warning)', marginTop: '0.2rem' }}>
            {student.cumulative_gpa !== undefined && student.cumulative_gpa !== null ? Number(student.cumulative_gpa).toFixed(2) : 'N/A'}
          </p>
        </div>
        <div className="glass-card" style={{ padding: '1rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Status</span>
          <div style={{ marginTop: '0.3rem' }}>
            {student.is_archived ? <Badge variant="neutral">Archived</Badge> : <Badge variant="success">Active</Badge>}
          </div>
        </div>
      </div>

      {/* Historical Semesters Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', marginTop: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Longitudinal Academic History</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Preserved historical term records over time</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          icon={<Plus size={16} />}
          onClick={() => setShowAddRecord(!showAddRecord)}
        >
          {showAddRecord ? 'Cancel' : 'Add Term Record'}
        </Button>
      </div>

      {/* Add Record Inline Form */}
      {showAddRecord && (
        <form onSubmit={handleAddRecordSubmit} className="glass-card" style={{ marginBottom: '1.5rem', borderColor: 'var(--color-primary)' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--color-primary)' }}>
            New Semester Academic Record
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem' }}>
            <Input label="Academic Year" value={academicYear} onChange={(e) => setAcademicYear(e.target.value)} required placeholder="2024-2025" />
            <Input label="Semester (1-12)" type="number" min="1" max="12" value={semester} onChange={(e) => setSemester(Number(e.target.value))} required />
            <Input label="Attendance %" type="number" step="0.1" min="0" max="100" value={attendance} onChange={(e) => setAttendance(e.target.value)} required />
            <Input label="Prev CGPA" type="number" step="0.01" min="0" max="10" value={prevCgpa} onChange={(e) => setPrevCgpa(e.target.value)} />
            <Input label="Mid-1 Marks" type="number" step="0.1" min="0" max="100" value={mid1} onChange={(e) => setMid1(e.target.value)} />
            <Input label="Mid-2 Marks" type="number" step="0.1" min="0" max="100" value={mid2} onChange={(e) => setMid2(e.target.value)} />
            <Input label="Internals" type="number" step="0.1" min="0" max="100" value={internalMarks} onChange={(e) => setInternalMarks(e.target.value)} />
            <Input label="Backlogs" type="number" min="0" value={backlogs} onChange={(e) => setBacklogs(e.target.value)} required />
            <Input label="Term SGPA" type="number" step="0.01" min="0" max="10" value={semesterCgpa} onChange={(e) => setSemesterCgpa(e.target.value)} />
            <Input label="Grade" value={grade} onChange={(e) => setGrade(e.target.value)} placeholder="A+, A, B" />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
            <Button type="submit" size="sm" loading={loading}>Save Semester Record</Button>
          </div>
        </form>
      )}

      {/* Historical Record Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        {(!student.academic_records || student.academic_records.length === 0) ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            No historical academic records found for this student.
          </div>
        ) : (
          student.academic_records.map((rec) => (
            <div
              key={rec.id}
              className="glass-card"
              style={{
                padding: '1.1rem 1.4rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '1rem'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <span style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                    Semester {rec.semester}
                  </span>
                  <Badge variant="neutral">{rec.academic_year}</Badge>
                  {rec.historical_risk_level && (
                    <Badge variant={rec.historical_risk_level === 'LOW' ? 'success' : rec.historical_risk_level === 'MODERATE' ? 'warning' : 'danger'}>
                      {rec.historical_risk_level} Risk (Historical)
                    </Badge>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '1.25rem', marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  <span>Attendance: <strong style={{ color: 'var(--text-primary)' }}>{rec.attendance_percentage}%</strong></span>
                  <span>Mid-1: <strong style={{ color: 'var(--text-primary)' }}>{rec.mid_1 ?? '-'}</strong></span>
                  <span>Mid-2: <strong style={{ color: 'var(--text-primary)' }}>{rec.mid_2 ?? '-'}</strong></span>
                  <span>Internals: <strong style={{ color: 'var(--text-primary)' }}>{rec.internal_marks ?? '-'}</strong></span>
                  <span>Backlogs: <strong style={{ color: rec.backlogs > 0 ? 'var(--color-danger)' : 'var(--text-primary)' }}>{rec.backlogs}</strong></span>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Term SGPA</span>
                <p style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--color-primary)' }}>
                  {rec.semester_cgpa !== undefined && rec.semester_cgpa !== null ? Number(rec.semester_cgpa).toFixed(2) : '-'}
                  {rec.grade && <span style={{ fontSize: '0.85rem', marginLeft: '0.4rem', color: 'var(--text-secondary)' }}>({rec.grade})</span>}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </Modal>
  );
};
