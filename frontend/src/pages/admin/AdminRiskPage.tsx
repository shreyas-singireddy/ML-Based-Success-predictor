import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  Loader2,
  Building2,
  Layers,
  Activity,
  Info,
} from 'lucide-react';
import { adminAnalyticsApi } from '../../services/adminAnalyticsApi';
import { AdminRiskAnalytics } from '../../types/adminAnalytics';

export const AdminRiskPage: React.FC = () => {
  const [data, setData] = useState<AdminRiskAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRisk = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminAnalyticsApi.getRisk();
      setData(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load risk intelligence analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRisk();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
        <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#EF4444' }} />
        COMPUTING INSTITUTIONAL RISK PROFILES & CORRELATIONS...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '2rem' }}>
        <div style={{ padding: '1.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#FCA5A5' }}>
          {error || 'Failed to load risk analytics.'}
        </div>
      </div>
    );
  }

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
              PHASE 13 RISK INTELLIGENCE
            </span>
            <span style={{ fontSize: '0.75rem', color: '#71717A' }}>Institutional Risk Stratification</span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>
            System-Wide Risk Distribution & Factor Intelligence
          </h1>
          <p style={{ color: '#A1A1AA', fontSize: '0.875rem', margin: '0.35rem 0 0 0' }}>
            Departmental risk concentration, progression bottlenecks, and empirical attendance correlation.
          </p>
        </div>

        <button
          onClick={fetchRisk}
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

      {/* High / Critical Risk Callout */}
      <div
        style={{
          padding: '1.25rem 1.5rem',
          borderRadius: '8px',
          backgroundColor: '#141014',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          marginBottom: '2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <AlertTriangle size={24} color="#EF4444" />
          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#FFFFFF' }}>
              {data.total_high_critical_count} Students in Elevated / Critical Risk Category ({data.high_critical_percentage}%)
            </div>
            <div style={{ fontSize: '0.8rem', color: '#A1A1AA' }}>
              Identified through calibrated gradient-boosted decision trees and ensemble classifiers.
            </div>
          </div>
        </div>
      </div>

      {/* Department Risk Stratification */}
      <div
        style={{
          backgroundColor: '#0F0F11',
          border: '1px solid rgba(255, 255, 255, 0.07)',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '2rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Building2 size={18} color="#6366F1" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: 0 }}>
            Department Risk Breakdown
          </h2>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#71717A', textAlign: 'left' }}>
                <th style={{ padding: '0.75rem 0.5rem' }}>Department</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Enrolled</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Low Risk</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Medium Risk</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>High Risk</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>Critical</th>
                <th style={{ padding: '0.75rem 0.5rem' }}>High+Critical %</th>
              </tr>
            </thead>
            <tbody>
              {data.department_risk_breakdown.map((dept) => (
                <tr key={dept.department_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <td style={{ padding: '0.75rem 0.5rem', fontWeight: 600, color: '#FFFFFF' }}>
                    {dept.department_name} ({dept.department_code})
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: '#A1A1AA', fontFamily: "'JetBrains Mono', monospace" }}>
                    {dept.student_count}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: '#86EFAC', fontFamily: "'JetBrains Mono', monospace" }}>
                    {dept.risk_distribution.LOW || 0}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: '#FDE047', fontFamily: "'JetBrains Mono', monospace" }}>
                    {dept.risk_distribution.MEDIUM || 0}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: '#FDBA74', fontFamily: "'JetBrains Mono', monospace" }}>
                    {dept.risk_distribution.HIGH || 0}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', color: '#FCA5A5', fontFamily: "'JetBrains Mono', monospace" }}>
                    {dept.risk_distribution.CRITICAL || 0}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem' }}>
                    <span
                      style={{
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        fontFamily: "'JetBrains Mono', monospace",
                        backgroundColor: dept.high_or_critical_pct > 25 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(113, 113, 122, 0.2)',
                        color: dept.high_or_critical_pct > 25 ? '#FCA5A5' : '#D4D4D8',
                      }}
                    >
                      {dept.high_or_critical_pct}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Attendance vs Risk Correlation Grid */}
      <div
        style={{
          backgroundColor: '#0F0F11',
          border: '1px solid rgba(255, 255, 255, 0.07)',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '2rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Activity size={18} color="#10B981" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: 0 }}>
            Attendance Rate vs. Risk Category Correlation
          </h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
          {data.attendance_vs_risk.map((bucket) => {
            const tot = bucket.student_count;
            const hc = (bucket.risk_distribution.HIGH || 0) + (bucket.risk_distribution.CRITICAL || 0);
            const hcPct = tot > 0 ? ((hc / tot) * 100).toFixed(0) : '0';

            return (
              <div
                key={bucket.attendance_bracket}
                style={{
                  backgroundColor: '#141418',
                  borderRadius: '6px',
                  padding: '1.25rem',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF' }}>
                    {bucket.attendance_bracket}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
                    {bucket.student_count} students
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.8rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#86EFAC' }}>Low Risk:</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>{bucket.risk_distribution.LOW || 0}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#FDE047' }}>Medium Risk:</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>{bucket.risk_distribution.MEDIUM || 0}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#FDBA74' }}>High Risk:</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>{bucket.risk_distribution.HIGH || 0}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#FCA5A5' }}>Critical:</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>{bucket.risk_distribution.CRITICAL || 0}</span>
                  </div>
                </div>

                <div style={{ marginTop: '0.75rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(255, 255, 255, 0.05)', fontSize: '0.75rem', color: '#A1A1AA' }}>
                  Elevated Risk: <strong style={{ color: Number(hcPct) > 50 ? '#FCA5A5' : '#FFFFFF' }}>{hcPct}%</strong>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
