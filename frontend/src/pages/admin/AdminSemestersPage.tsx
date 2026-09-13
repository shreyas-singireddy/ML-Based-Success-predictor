import React, { useEffect, useState } from 'react';
import {
  Layers,
  RefreshCw,
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import { adminAnalyticsApi } from '../../services/adminAnalyticsApi';
import { SemesterRiskItem } from '../../types/adminAnalytics';

export const AdminSemestersPage: React.FC = () => {
  const [semesters, setSemesters] = useState<SemesterRiskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSemesters = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminAnalyticsApi.getSemesters();
      setSemesters(res.semesters);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load semester analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSemesters();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
        <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#EF4444' }} />
        AGGREGATING SEMESTER PROGRESSION METRICS...
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
              PHASE 13 SEMESTER PROGRESSION
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>
            Semester Progression & Longitudinal Risk Trends
          </h1>
          <p style={{ color: '#A1A1AA', fontSize: '0.875rem', margin: '0.35rem 0 0 0' }}>
            Academic risk distribution, grade averages, and attendance rates analyzed across cohorts from Semester 1 to Semester 8.
          </p>
        </div>

        <button
          onClick={fetchSemesters}
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

      {semesters.length === 0 ? (
        <div style={{ padding: '4rem', textAlign: 'center', backgroundColor: '#0F0F11', borderRadius: '8px' }}>
          <Layers size={40} color="#52525B" style={{ margin: '0 auto 1rem auto' }} />
          <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>INSUFFICIENT HISTORICAL DATA</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
          {semesters.map((sem) => (
            <div
              key={sem.semester}
              style={{
                backgroundColor: '#0F0F11',
                border: '1px solid rgba(255, 255, 255, 0.07)',
                borderRadius: '8px',
                padding: '1.5rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0, color: '#FFFFFF' }}>
                  Semester {sem.semester}
                </h3>
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
                  {sem.student_count} Students
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem', fontSize: '0.8rem' }}>
                <div style={{ padding: '0.65rem', backgroundColor: '#141418', borderRadius: '6px' }}>
                  <div style={{ color: '#71717A', fontSize: '0.7rem' }}>Avg CGPA</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#10B981', marginTop: '0.15rem' }}>
                    {sem.average_cgpa?.toFixed(2) || 'N/A'}
                  </div>
                </div>

                <div style={{ padding: '0.65rem', backgroundColor: '#141418', borderRadius: '6px' }}>
                  <div style={{ color: '#71717A', fontSize: '0.7rem' }}>Avg Attendance</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#FFFFFF', marginTop: '0.15rem' }}>
                    {sem.average_attendance?.toFixed(1) || 'N/A'}%
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.75rem', color: '#A1A1AA', marginBottom: '0.5rem' }}>Risk Breakdown</div>
              <div style={{ display: 'flex', gap: '0.35rem', fontSize: '0.75rem' }}>
                <span style={{ padding: '0.2rem 0.4rem', backgroundColor: 'rgba(34, 197, 94, 0.15)', color: '#86EFAC', borderRadius: '4px' }}>
                  Low: {sem.risk_distribution.LOW || 0}
                </span>
                <span style={{ padding: '0.2rem 0.4rem', backgroundColor: 'rgba(234, 179, 8, 0.15)', color: '#FDE047', borderRadius: '4px' }}>
                  Med: {sem.risk_distribution.MEDIUM || 0}
                </span>
                <span style={{ padding: '0.2rem 0.4rem', backgroundColor: 'rgba(249, 115, 22, 0.15)', color: '#FDBA74', borderRadius: '4px' }}>
                  High: {sem.risk_distribution.HIGH || 0}
                </span>
                <span style={{ padding: '0.2rem 0.4rem', backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#FCA5A5', borderRadius: '4px' }}>
                  Crit: {sem.risk_distribution.CRITICAL || 0}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
