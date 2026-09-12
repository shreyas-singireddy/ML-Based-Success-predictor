import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Student } from '../types';
import { studentApi } from '../services/api';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { GraduationCap, LogOut, BookOpen, Calendar, Award, CheckCircle, TrendingUp } from 'lucide-react';

export const StudentPortalPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMyProfile = async () => {
      if (!user?.profile_id) {
        setError('No associated student profile linked to your user account.');
        setLoading(false);
        return;
      }
      try {
        const data = await studentApi.getStudentById(user.profile_id);
        setStudent(data);
      } catch (err: any) {
        setError(err.response?.data?.error?.message || 'Failed to load your academic record.');
      } finally {
        setLoading(false);
      }
    };

    fetchMyProfile();
  }, [user]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <header
        className="glass-panel"
        style={{
          borderRadius: 0,
          borderLeft: 'none',
          borderRight: 'none',
          borderTop: 'none',
          padding: '0.85rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky',
          top: 0,
          zIndex: 40
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, var(--color-success), #059669)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <GraduationCap size={22} color="#ffffff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              Student Academic Portal
            </h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Self-Service Performance Center
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div style={{ textAlign: 'right' }}>
            <p style={{ fontSize: '0.9rem', fontWeight: 700 }}>{user?.full_name}</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2px' }}>
              <Badge variant="success">STUDENT</Badge>
            </div>
          </div>
          <Button variant="outline" size="sm" icon={<LogOut size={16} />} onClick={logout}>
            Sign Out
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: '1080px', width: '100%', margin: '0 auto', padding: '2rem 1.5rem', flex: 1 }}>
        {error && <Alert variant="error">{error}</Alert>}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
            Loading your academic history...
          </div>
        ) : student ? (
          <div>
            {/* Student Overview Header */}
            <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem' }}>
                <div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--color-primary)', fontWeight: 700 }}>
                    {student.student_number}
                  </span>
                  <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
                    {student.name}
                  </h1>
                  <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginTop: '0.3rem' }}>
                    Department of {student.department_code || student.department_name} • Semester {student.current_semester} • Class of {student.enrollment_year + 4}
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>Cumulative CGPA</span>
                    <p style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--color-success)', lineHeight: 1.1 }}>
                      {student.cumulative_gpa !== undefined && student.cumulative_gpa !== null ? Number(student.cumulative_gpa).toFixed(2) : '—'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Academic History Timeline */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '0.3rem' }}>
                My Longitudinal Performance History
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                Chronological semester progress verified by your academic department
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {(!student.academic_records || student.academic_records.length === 0) ? (
                  <div className="glass-card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    No semester records have been registered yet.
                  </div>
                ) : (
                  student.academic_records.map((rec) => (
                    <div key={rec.id} className="glass-card" style={{ padding: '1.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                            Semester {rec.semester}
                          </h3>
                          <Badge variant="neutral">{rec.academic_year}</Badge>
                          {rec.grade && <Badge variant="success">Grade: {rec.grade}</Badge>}
                        </div>

                        <div style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Semester SGPA</span>
                          <p style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--color-primary)' }}>
                            {rec.semester_cgpa !== undefined && rec.semester_cgpa !== null ? Number(rec.semester_cgpa).toFixed(2) : '—'}
                          </p>
                        </div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem', background: 'rgba(15, 23, 42, 0.4)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Attendance</span>
                          <p style={{ fontWeight: 700, fontSize: '1rem' }}>{rec.attendance_percentage}%</p>
                        </div>
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Mid-Term 1</span>
                          <p style={{ fontWeight: 700, fontSize: '1rem' }}>{rec.mid_1 ?? '—'}</p>
                        </div>
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Mid-Term 2</span>
                          <p style={{ fontWeight: 700, fontSize: '1rem' }}>{rec.mid_2 ?? '—'}</p>
                        </div>
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Internal Marks</span>
                          <p style={{ fontWeight: 700, fontSize: '1rem' }}>{rec.internal_marks ?? '—'}</p>
                        </div>
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Backlogs</span>
                          <p style={{ fontWeight: 700, fontSize: '1rem', color: rec.backlogs > 0 ? 'var(--color-danger)' : 'var(--text-primary)' }}>
                            {rec.backlogs}
                          </p>
                        </div>
                      </div>

                      {rec.notes && (
                        <div style={{ marginTop: '0.85rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                          <strong>Advisor Note:</strong> {rec.notes}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
};
