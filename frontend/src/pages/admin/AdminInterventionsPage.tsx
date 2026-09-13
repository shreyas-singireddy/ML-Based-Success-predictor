import React, { useEffect, useState } from 'react';
import {
  ClipboardList,
  RefreshCw,
  Loader2,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle2,
  Clock,
  Info,
} from 'lucide-react';
import { adminAnalyticsApi } from '../../services/adminAnalyticsApi';
import { AdminInterventionsAnalytics } from '../../types/adminAnalytics';

export const AdminInterventionsPage: React.FC = () => {
  const [data, setData] = useState<AdminInterventionsAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInterventionsAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminAnalyticsApi.getInterventions();
      setData(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load intervention analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInterventionsAnalytics();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
        <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#EF4444' }} />
        AGGREGATING INSTITUTIONAL INTERVENTIONS & OUTCOMES...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: '2rem' }}>
        <div style={{ padding: '1.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#FCA5A5' }}>
          {error || 'Failed to load intervention analytics.'}
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
              PHASE 13 INTERVENTION ANALYTICS
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>
            System-Wide Academic Interventions & Measured Outcomes
          </h1>
          <p style={{ color: '#A1A1AA', fontSize: '0.875rem', margin: '0.35rem 0 0 0' }}>
            Aggregated institutional intervention volume, completion metrics, and observational indicator trajectories.
          </p>
        </div>

        <button
          onClick={fetchInterventionsAnalytics}
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

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: '#0F0F11', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: '#71717A', textTransform: 'uppercase' }}>Total Interventions</div>
          <div style={{ fontSize: '1.85rem', fontWeight: 700, marginTop: '0.4rem', color: '#FFFFFF' }}>
            {data.total_interventions}
          </div>
        </div>

        <div style={{ backgroundColor: '#0F0F11', border: '1px solid rgba(34, 197, 94, 0.2)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: '#86EFAC', textTransform: 'uppercase' }}>Completion Rate</div>
          <div style={{ fontSize: '1.85rem', fontWeight: 700, marginTop: '0.4rem', color: '#86EFAC' }}>
            {data.completion_rate}%
          </div>
          <div style={{ fontSize: '0.75rem', color: '#71717A', marginTop: '0.2rem' }}>
            {data.follow_ups_due_count} follow-ups due
          </div>
        </div>

        <div style={{ backgroundColor: '#0F0F11', border: '1px solid rgba(99, 102, 241, 0.2)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: '#A5B4FC', textTransform: 'uppercase' }}>Measured Evaluations</div>
          <div style={{ fontSize: '1.85rem', fontWeight: 700, marginTop: '0.4rem', color: '#A5B4FC' }}>
            {data.measured_students_count}
          </div>
        </div>

        <div style={{ backgroundColor: '#0F0F11', border: '1px solid rgba(34, 197, 94, 0.2)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.75rem', color: '#86EFAC', textTransform: 'uppercase' }}>Improved Indicators %</div>
          <div style={{ fontSize: '1.85rem', fontWeight: 700, marginTop: '0.4rem', color: '#86EFAC' }}>
            {data.improved_percentage_of_measured}%
          </div>
          <div style={{ fontSize: '0.75rem', color: '#71717A', marginTop: '0.2rem' }}>
            Of measured evaluations
          </div>
        </div>
      </div>

      {/* Two Columns: Outcome Trajectories & Category Distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Outcome Trajectory */}
        <div style={{ backgroundColor: '#0F0F11', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: '0 0 1rem 0', color: '#FFFFFF' }}>
            Observed Academic Indicator Trajectories
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {[
              { label: 'IMPROVED INDICATORS', count: data.outcome_distribution.IMPROVED || 0, color: '#22C55E' },
              { label: 'STABLE INDICATORS', count: data.outcome_distribution.STABLE || 0, color: '#3B82F6' },
              { label: 'DECLINED INDICATORS', count: data.outcome_distribution.DECLINED || 0, color: '#EF4444' },
              { label: 'INSUFFICIENT DATA / PENDING', count: data.outcome_distribution.INSUFFICIENT_DATA || 0, color: '#71717A' },
            ].map((item) => {
              const total = data.total_interventions || 1;
              const pct = ((item.count / total) * 100).toFixed(1);

              return (
                <div key={item.label}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
                    <span style={{ fontWeight: 600, color: item.color }}>{item.label}</span>
                    <span style={{ color: '#A1A1AA', fontFamily: "'JetBrains Mono', monospace" }}>
                      {item.count} ({pct}%)
                    </span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: '#18181B', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${pct}%`, backgroundColor: item.color, borderRadius: '4px' }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Category Breakdown */}
        <div style={{ backgroundColor: '#0F0F11', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: '0 0 1rem 0', color: '#FFFFFF' }}>
            Interventions by Category
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {Object.entries(data.by_category).map(([cat, count]) => (
              <div
                key={cat}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.55rem 0.75rem',
                  backgroundColor: '#141418',
                  borderRadius: '6px',
                  fontSize: '0.82rem',
                }}
              >
                <span style={{ color: '#E4E4E7' }}>{cat.replace(/_/g, ' ')}</span>
                <span style={{ fontWeight: 600, color: '#A5B4FC', fontFamily: "'JetBrains Mono', monospace" }}>
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Non-causal Observational Disclaimer Banner */}
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
          <strong>Non-Causal Observational Methodology:</strong> {data.observational_statement}
        </div>
      </div>
    </div>
  );
};
