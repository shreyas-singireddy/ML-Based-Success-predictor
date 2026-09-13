import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  RefreshCw,
  Loader2,
  Building2,
  AlertCircle,
  GraduationCap,
  Percent,
} from 'lucide-react';
import { adminAnalyticsApi } from '../../services/adminAnalyticsApi';
import { AdminAcademicPerformanceAnalytics } from '../../types/adminAnalytics';

export const AdminPerformancePage: React.FC = () => {
  const [data, setData] = useState<AdminAcademicPerformanceAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPerformance = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminAnalyticsApi.getPerformance();
      setData(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load academic performance analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPerformance();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
        <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#EF4444' }} />
        AGGREGATING CGPA DISTRIBUTIONS & PERFORMANCE METRICS...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '2rem' }}>
        <div style={{ padding: '1.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#FCA5A5' }}>
          {error || 'Failed to load performance analytics.'}
        </div>
      </div>
    );
  }

  const totalStudentsInDist = Object.values(data.overall_cgpa_distribution).reduce((a, b) => a + b, 0);

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto', color: '#FFFFFF' }}>
      {/* Header */}
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
              PHASE 13 PERFORMANCE INTELLIGENCE
            </span>
            <span style={{ fontSize: '0.75rem', color: '#71717A' }}>Academic Trajectory & Backlogs</span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>
            Institutional Academic Performance
          </h1>
          <p style={{ color: '#A1A1AA', fontSize: '0.875rem', margin: '0.35rem 0 0 0' }}>
            Cumulative GPA distribution bands, attendance compliance, and backlog load across faculties.
          </p>
        </div>

        <button
          onClick={fetchPerformance}
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

      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: '#0F0F11', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: '#71717A', textTransform: 'uppercase' }}>Current Average CGPA</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.4rem', color: '#10B981' }}>
            {data.average_current_cgpa?.toFixed(2) || 'N/A'}
          </div>
        </div>

        <div style={{ backgroundColor: '#0F0F11', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: '#71717A', textTransform: 'uppercase' }}>Predicted Average CGPA</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.4rem', color: '#6366F1' }}>
            {data.average_predicted_cgpa?.toFixed(2) || 'N/A'}
          </div>
        </div>

        <div style={{ backgroundColor: '#0F0F11', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: '#71717A', textTransform: 'uppercase' }}>Average Attendance</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.4rem', color: '#FFFFFF' }}>
            {data.average_attendance?.toFixed(1) || 'N/A'}%
          </div>
          <div style={{ fontSize: '0.75rem', color: '#FCA5A5', marginTop: '0.2rem' }}>
            {data.attendance_below_75_count} students &lt; 75%
          </div>
        </div>

        <div style={{ backgroundColor: '#0F0F11', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: '#FCA5A5', textTransform: 'uppercase' }}>Backlog Load</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '0.4rem', color: '#FCA5A5' }}>
            {data.total_backlogs}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#71717A', marginTop: '0.2rem' }}>
            {data.students_with_backlogs_count} students ({data.students_with_backlogs_pct}%)
          </div>
        </div>
      </div>

      {/* CGPA Distribution Bar Section */}
      <div
        style={{
          backgroundColor: '#0F0F11',
          border: '1px solid rgba(255, 255, 255, 0.07)',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '2rem',
        }}
      >
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: '0 0 1.25rem 0', color: '#FFFFFF' }}>
          Cumulative GPA Distribution Bands
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {Object.entries(data.overall_cgpa_distribution).map(([bracket, count]) => {
            const pct = totalStudentsInDist > 0 ? ((count / totalStudentsInDist) * 100).toFixed(1) : '0';
            return (
              <div key={bracket}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
                  <span style={{ fontWeight: 600, color: '#E4E4E7' }}>{bracket} CGPA</span>
                  <span style={{ color: '#A1A1AA', fontFamily: "'JetBrains Mono', monospace" }}>
                    {count} students ({pct}%)
                  </span>
                </div>
                <div
                  style={{
                    height: '8px',
                    backgroundColor: '#18181B',
                    borderRadius: '4px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      width: `${pct}%`,
                      backgroundColor:
                        bracket === '< 6.0'
                          ? '#EF4444'
                          : bracket === '6.0 - 6.99'
                          ? '#F97316'
                          : bracket === '7.0 - 7.99'
                          ? '#EAB308'
                          : '#22C55E',
                      borderRadius: '4px',
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Department Performance Table */}
      <div
        style={{
          backgroundColor: '#0F0F11',
          border: '1px solid rgba(255, 255, 255, 0.07)',
          borderRadius: '8px',
          padding: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Building2 size={18} color="#6366F1" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: 0 }}>
            Department Academic Performance Comparison
          </h2>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#71717A', textAlign: 'left' }}>
                <th style={{ padding: '0.75rem 0.5rem' }}>Department</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Enrolled</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Avg CGPA</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Predicted CGPA</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Attendance</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Total Backlogs</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Interventions</th>
              </tr>
            </thead>
            <tbody>
              {data.department_performances.map((dept) => (
                <tr key={dept.department_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <td style={{ padding: '0.75rem 0.5rem', fontWeight: 600, color: '#FFFFFF' }}>
                    {dept.department_name} ({dept.department_code})
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: '#A1A1AA', fontFamily: "'JetBrains Mono', monospace" }}>
                    {dept.student_count}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: '#10B981', fontFamily: "'JetBrains Mono', monospace", fontWeight: 600 }}>
                    {dept.average_current_cgpa?.toFixed(2) || 'N/A'}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: '#6366F1', fontFamily: "'JetBrains Mono', monospace" }}>
                    {dept.average_predicted_cgpa?.toFixed(2) || 'N/A'}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: '#E4E4E7', fontFamily: "'JetBrains Mono', monospace" }}>
                    {dept.average_attendance?.toFixed(1) || 'N/A'}%
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: dept.total_backlogs > 0 ? '#FCA5A5' : '#86EFAC', fontFamily: "'JetBrains Mono', monospace" }}>
                    {dept.total_backlogs} ({dept.students_with_backlogs} st.)
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: '#A5B4FC', fontFamily: "'JetBrains Mono', monospace" }}>
                    {dept.intervention_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
