import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  Activity,
  Layers,
  BookOpen,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  Info,
} from 'lucide-react';
import { facultyApi } from '../../services/facultyApi';
import { FacultyAnalyticsResponse } from '../../types/faculty';

export const FacultyAnalyticsPage: React.FC = () => {
  const [data, setData] = useState<FacultyAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await facultyApi.getAnalytics();
      setData(res);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load class analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '3rem', color: '#71717A', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <RefreshCw size={18} className="animate-spin" color="#6366F1" />
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.85rem' }}>
          COMPUTING CLASS-LEVEL AGGREGATE RISK DISTRIBUTIONS…
        </span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '2.5rem' }}>
        <div style={{ padding: '1.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#FCA5A5' }}>
          <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>ANALYTICS UNAVAILABLE</div>
          <div style={{ fontSize: '0.85rem' }}>{error}</div>
        </div>
      </div>
    );
  }

  const total = data.total_students || 1;

  return (
    <div style={{ padding: '2rem 2.5rem', maxWidth: '1400px', width: '100%', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '2rem' }}>
        <div>
          <div style={{ fontSize: '0.7rem', fontFamily: "'JetBrains Mono', monospace", color: '#6366F1', fontWeight: 600, letterSpacing: '0.08em', marginBottom: '0.35rem' }}>
            CLASS-LEVEL INTELLIGENCE
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#FFFFFF', margin: 0, letterSpacing: '-0.02em' }}>
            Academic Performance & Risk Analytics
          </h1>
          <div style={{ fontSize: '0.8rem', color: '#71717A', marginTop: '0.25rem' }}>
            Aggregate statistical distributions, academic bands, and semester risk hotspots for {data.department_scope || 'monitored cohort'}.
          </div>
        </div>

        <button
          onClick={fetchAnalytics}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.45rem 0.85rem',
            backgroundColor: '#18181B',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '6px',
            color: '#E4E4E7',
            cursor: 'pointer',
            fontSize: '0.75rem',
            fontWeight: 600,
          }}
        >
          <RefreshCw size={13} />
          <span>REFRESH</span>
        </button>
      </div>

      {/* Distribution Grids */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* CGPA Distribution */}
        <div
          style={{
            backgroundColor: '#0A0A0C',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              CGPA Tier Distribution
            </h2>
            <span style={{ fontSize: '0.7rem', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
              ACADEMIC BANDS
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {Object.entries(data.cgpa_distribution).map(([band, count]) => {
              const pct = ((count / total) * 100).toFixed(0);
              return (
                <div key={band}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '0.25rem' }}>
                    <span style={{ color: '#E4E4E7', fontWeight: 600 }}>{band} CGPA</span>
                    <span style={{ color: '#A1A1AA', fontFamily: "'JetBrains Mono', monospace" }}>
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: '#18181B', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${pct}%`,
                        backgroundColor: band.includes('<6.0') ? '#EF4444' : band.includes('6.0') ? '#F59E0B' : '#6366F1',
                        borderRadius: '4px',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Attendance Distribution */}
        <div
          style={{
            backgroundColor: '#0A0A0C',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              Attendance Rate Distribution
            </h2>
            <span style={{ fontSize: '0.7rem', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
              COMPLIANCE BANDS
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {Object.entries(data.attendance_distribution).map(([band, count]) => {
              const pct = ((count / total) * 100).toFixed(0);
              return (
                <div key={band}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '0.25rem' }}>
                    <span style={{ color: '#E4E4E7', fontWeight: 600 }}>{band} Attendance</span>
                    <span style={{ color: '#A1A1AA', fontFamily: "'JetBrains Mono', monospace" }}>
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: '#18181B', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${pct}%`,
                        backgroundColor: band.includes('<65') ? '#EF4444' : band.includes('65%-75') ? '#F59E0B' : '#10B981',
                        borderRadius: '4px',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Semester Risk Hotspots Table */}
      <div
        style={{
          backgroundColor: '#0A0A0C',
          border: '1px solid rgba(255, 255, 255, 0.07)',
          borderRadius: '8px',
          overflow: 'hidden',
          marginBottom: '1.5rem',
        }}
      >
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
            Semester Academic Risk Hotspots
          </h2>
          <div style={{ fontSize: '0.75rem', color: '#71717A' }}>
            Comparison of risk concentration and average standing across academic terms
          </div>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
          <thead>
            <tr style={{ backgroundColor: '#0F0F12', borderBottom: '1px solid rgba(255, 255, 255, 0.06)', color: '#71717A' }}>
              <th style={{ padding: '0.85rem 1.25rem', fontWeight: 600 }}>SEMESTER</th>
              <th style={{ padding: '0.85rem 1.25rem', fontWeight: 600 }}>ENROLLED</th>
              <th style={{ padding: '0.85rem 1.25rem', fontWeight: 600 }}>AT-RISK (HIGH/CRITICAL)</th>
              <th style={{ padding: '0.85rem 1.25rem', fontWeight: 600 }}>AT-RISK RATIO</th>
              <th style={{ padding: '0.85rem 1.25rem', fontWeight: 600 }}>AVG CGPA</th>
              <th style={{ padding: '0.85rem 1.25rem', fontWeight: 600 }}>AVG ATTENDANCE</th>
            </tr>
          </thead>
          <tbody>
            {data.semester_risk_hotspots.map((spot) => (
              <tr key={spot.semester} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700, color: '#FFFFFF' }}>
                  Semester {spot.semester}
                </td>
                <td style={{ padding: '0.85rem 1.25rem', color: '#E4E4E7' }}>
                  {spot.student_count} students
                </td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  <span style={{ fontWeight: 700, color: spot.high_critical_count > 0 ? '#EF4444' : '#10B981' }}>
                    {spot.high_critical_count}
                  </span>
                </td>
                <td style={{ padding: '0.85rem 1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: '60px', height: '6px', backgroundColor: '#18181B', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${spot.high_critical_pct}%`, height: '100%', backgroundColor: spot.high_critical_pct > 25 ? '#EF4444' : '#6366F1' }} />
                    </div>
                    <span style={{ fontSize: '0.75rem', color: '#A1A1AA', fontFamily: "'JetBrains Mono', monospace" }}>
                      {spot.high_critical_pct}%
                    </span>
                  </div>
                </td>
                <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: '#FFFFFF' }}>
                  {spot.average_cgpa !== null ? spot.average_cgpa.toFixed(2) : '—'}
                </td>
                <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: '#FFFFFF' }}>
                  {spot.average_attendance !== null ? `${spot.average_attendance.toFixed(1)}%` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
