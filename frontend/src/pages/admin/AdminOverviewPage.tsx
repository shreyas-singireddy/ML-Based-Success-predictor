import React, { useEffect, useState } from 'react';
import {
  Users,
  ShieldAlert,
  BarChart3,
  Building2,
  ClipboardList,
  AlertTriangle,
  TrendingUp,
  RefreshCw,
  Loader2,
  Info,
  CheckCircle2,
  Clock,
} from 'lucide-react';
import { adminAnalyticsApi } from '../../services/adminAnalyticsApi';
import { AdminOverviewAnalytics } from '../../types/adminAnalytics';

export const AdminOverviewPage: React.FC = () => {
  const [data, setData] = useState<AdminOverviewAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminAnalyticsApi.getOverview();
      setData(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load system-wide overview analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
        <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#EF4444' }} />
        AGGREGATING INSTITUTION-WIDE ACADEMIC INTELLIGENCE...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '2rem' }}>
        <div
          style={{
            padding: '1.5rem',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            color: '#FCA5A5',
          }}
        >
          {error || 'Failed to load overview data.'}
        </div>
      </div>
    );
  }

  const riskTotal = (data.risk_distribution.LOW || 0) + (data.risk_distribution.MEDIUM || 0) + (data.risk_distribution.HIGH || 0) + (data.risk_distribution.CRITICAL || 0);

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
              PHASE 13 INSTITUTIONAL INTELLIGENCE
            </span>
            <span style={{ fontSize: '0.75rem', color: '#71717A' }}>System-Wide Executive KPI Dashboard</span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>
            Academic Intelligence & Institution Overview
          </h1>
          <p style={{ color: '#A1A1AA', fontSize: '0.875rem', margin: '0.35rem 0 0 0' }}>
            Aggregated institutional metrics across students, active departments, risk profiles, and academic interventions.
          </p>
        </div>

        <button
          onClick={fetchOverview}
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

      {/* KPI Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
          marginBottom: '2rem',
        }}
      >
        <div
          style={{
            backgroundColor: '#0F0F11',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: '#71717A', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Monitored Students
            </span>
            <Users size={16} color="#6366F1" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 700, marginTop: '0.4rem', color: '#FFFFFF' }}>
            {data.total_students}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#71717A', marginTop: '0.2rem' }}>
            Active across {data.total_departments} Departments
          </div>
        </div>

        <div
          style={{
            backgroundColor: '#0F0F11',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: '#71717A', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Average Current CGPA
            </span>
            <BarChart3 size={16} color="#10B981" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 700, marginTop: '0.4rem', color: '#10B981' }}>
            {data.average_current_cgpa?.toFixed(2) || 'N/A'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#71717A', marginTop: '0.2rem' }}>
            Predicted: {data.average_predicted_cgpa?.toFixed(2) || 'N/A'}
          </div>
        </div>

        <div
          style={{
            backgroundColor: '#0F0F11',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: '#FCA5A5', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Requires Attention
            </span>
            <AlertTriangle size={16} color="#EF4444" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 700, marginTop: '0.4rem', color: '#FCA5A5' }}>
            {data.students_requiring_attention}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#71717A', marginTop: '0.2rem' }}>
            High risk, low attendance, or backlogs
          </div>
        </div>

        <div
          style={{
            backgroundColor: '#0F0F11',
            border: '1px solid rgba(99, 102, 241, 0.2)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: '#A5B4FC', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Total Interventions
            </span>
            <ClipboardList size={16} color="#6366F1" />
          </div>
          <div style={{ fontSize: '1.85rem', fontWeight: 700, marginTop: '0.4rem', color: '#A5B4FC' }}>
            {data.total_interventions}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#71717A', marginTop: '0.2rem' }}>
            {data.completed_interventions} Completed • {data.follow_ups_due} Follow-ups
          </div>
        </div>
      </div>

      {/* Two Columns: Risk Distribution & Quick Intelligence Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Risk Distribution Card */}
        <div
          style={{
            backgroundColor: '#0F0F11',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.5rem',
          }}
        >
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: '0 0 1rem 0', color: '#FFFFFF' }}>
            Institutional Risk Distribution
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {[
              { level: 'LOW', count: data.risk_distribution.LOW || 0, pct: data.risk_percentages.LOW || 0, color: '#22C55E' },
              { level: 'MEDIUM', count: data.risk_distribution.MEDIUM || 0, pct: data.risk_percentages.MEDIUM || 0, color: '#EAB308' },
              { level: 'HIGH', count: data.risk_distribution.HIGH || 0, pct: data.risk_percentages.HIGH || 0, color: '#F97316' },
              { level: 'CRITICAL', count: data.risk_distribution.CRITICAL || 0, pct: data.risk_percentages.CRITICAL || 0, color: '#EF4444' },
            ].map((item) => (
              <div key={item.level}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
                  <span style={{ fontWeight: 600, color: item.color }}>{item.level} RISK</span>
                  <span style={{ color: '#A1A1AA', fontFamily: "'JetBrains Mono', monospace" }}>
                    {item.count} students ({item.pct}%)
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
                      width: `${item.pct}%`,
                      backgroundColor: item.color,
                      borderRadius: '4px',
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Operational Overview Card */}
        <div
          style={{
            backgroundColor: '#0F0F11',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.5rem',
          }}
        >
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: '0 0 1rem 0', color: '#FFFFFF' }}>
            Institutional Operational Footprint
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div style={{ padding: '1rem', backgroundColor: '#141418', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.75rem', color: '#71717A', textTransform: 'uppercase' }}>Academic Departments</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#FFFFFF', marginTop: '0.3rem' }}>
                {data.total_departments}
              </div>
            </div>

            <div style={{ padding: '1rem', backgroundColor: '#141418', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.75rem', color: '#71717A', textTransform: 'uppercase' }}>Faculty Advisors</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#FFFFFF', marginTop: '0.3rem' }}>
                {data.total_faculty}
              </div>
            </div>

            <div style={{ padding: '1rem', backgroundColor: '#141418', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.75rem', color: '#71717A', textTransform: 'uppercase' }}>Active Alerts</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#FCA5A5', marginTop: '0.3rem' }}>
                {data.total_alerts}
              </div>
            </div>

            <div style={{ padding: '1rem', backgroundColor: '#141418', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.75rem', color: '#71717A', textTransform: 'uppercase' }}>Intervention Actions</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#86EFAC', marginTop: '0.3rem' }}>
                {data.completed_interventions}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Non-causal Disclaimer */}
      <div
        style={{
          padding: '1rem 1.25rem',
          backgroundColor: '#0C0C0E',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          color: '#71717A',
          fontSize: '0.75rem',
          lineHeight: 1.5,
        }}
      >
        <Info size={16} color="#EF4444" style={{ flexShrink: 0 }} />
        <div>
          <strong>System Intelligence Disclaimer:</strong> Executive analytics are calculated dynamically from authentic student snapshots and trained machine learning pipelines. Correlations between risk markers and outcomes do not constitute deterministic causal conclusions.
        </div>
      </div>
    </div>
  );
};
