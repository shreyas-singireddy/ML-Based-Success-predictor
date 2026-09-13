import React, { useEffect, useState } from 'react';
import {
  Building2,
  RefreshCw,
  Loader2,
  Users,
  GraduationCap,
  ClipboardList,
} from 'lucide-react';
import { adminAnalyticsApi } from '../../services/adminAnalyticsApi';
import { DepartmentPerformanceItem } from '../../types/adminAnalytics';

export const AdminDepartmentsPage: React.FC = () => {
  const [departments, setDepartments] = useState<DepartmentPerformanceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDepts = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminAnalyticsApi.getDepartments();
      setDepartments(res.departments);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load department analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDepts();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
        <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#EF4444' }} />
        AGGREGATING DEPARTMENT METRICS...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem' }}>
        <div style={{ padding: '1.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#FCA5A5' }}>
          {error}
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto', color: '#FFFFFF' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem' }}>
            <span
              style={{
                fontSize: '0.7rem',
                fontFamily: "'JetBrains Mono', monospace",
                color: '#EF4444',
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
              }}
            >
              PHASE 13 DEPARTMENT COMPARISON
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>
            Academic Department Comparative Intelligence
          </h1>
          <p style={{ color: '#A1A1AA', fontSize: '0.875rem', margin: '0.35rem 0 0 0' }}>
            Cross-faculty benchmark metrics across GPA averages, attendance rates, backlogs, and recorded interventions.
          </p>
        </div>

        <button
          onClick={fetchDepts}
          style={{
            padding: '0.6rem 0.9rem',
            backgroundColor: '#18181B',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '6px',
            color: '#E4E4E7',
            fontSize: '0.85rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
          }}
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {departments.length === 0 ? (
        <div style={{ padding: '4rem', textAlign: 'center', backgroundColor: '#0F0F11', borderRadius: '8px' }}>
          <Building2 size={40} color="#52525B" style={{ margin: '0 auto 1rem auto' }} />
          <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>NO DEPARTMENT DATA AVAILABLE</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {departments.map((dept) => (
            <div
              key={dept.department_id}
              style={{
                backgroundColor: '#0F0F11',
                border: '1px solid rgba(255, 255, 255, 0.07)',
                borderRadius: '8px',
                padding: '1.5rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0, color: '#FFFFFF' }}>
                    {dept.department_name}
                  </h3>
                  <div style={{ fontSize: '0.75rem', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
                    CODE: {dept.department_code}
                  </div>
                </div>
                <span
                  style={{
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    backgroundColor: 'rgba(99, 102, 241, 0.15)',
                    color: '#A5B4FC',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    fontFamily: "'JetBrains Mono', monospace",
                  }}
                >
                  {dept.student_count} Students
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.8rem' }}>
                <div style={{ padding: '0.75rem', backgroundColor: '#141418', borderRadius: '6px' }}>
                  <div style={{ color: '#71717A', fontSize: '0.7rem' }}>Avg Current CGPA</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#10B981', marginTop: '0.2rem' }}>
                    {dept.average_current_cgpa?.toFixed(2) || 'N/A'}
                  </div>
                </div>

                <div style={{ padding: '0.75rem', backgroundColor: '#141418', borderRadius: '6px' }}>
                  <div style={{ color: '#71717A', fontSize: '0.7rem' }}>Avg Predicted CGPA</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#6366F1', marginTop: '0.2rem' }}>
                    {dept.average_predicted_cgpa?.toFixed(2) || 'N/A'}
                  </div>
                </div>

                <div style={{ padding: '0.75rem', backgroundColor: '#141418', borderRadius: '6px' }}>
                  <div style={{ color: '#71717A', fontSize: '0.7rem' }}>Attendance Rate</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#FFFFFF', marginTop: '0.2rem' }}>
                    {dept.average_attendance?.toFixed(1) || 'N/A'}%
                  </div>
                </div>

                <div style={{ padding: '0.75rem', backgroundColor: '#141418', borderRadius: '6px' }}>
                  <div style={{ color: '#71717A', fontSize: '0.7rem' }}>Backlog Count</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: dept.total_backlogs > 0 ? '#FCA5A5' : '#86EFAC', marginTop: '0.2rem' }}>
                    {dept.total_backlogs}
                  </div>
                </div>
              </div>

              <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(255, 255, 255, 0.05)', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#A1A1AA' }}>
                <span>Interventions Performed:</span>
                <strong style={{ color: '#FFFFFF' }}>{dept.intervention_count}</strong>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
