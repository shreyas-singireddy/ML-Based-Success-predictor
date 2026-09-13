import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  TrendingUp,
  AlertTriangle,
  Clock,
  ArrowUpRight,
  ShieldAlert,
  Sparkles,
  BookOpen,
  Activity,
  ChevronRight,
  RefreshCw,
  Info,
} from 'lucide-react';
import { facultyApi } from '../../services/facultyApi';
import { FacultyOverview } from '../../types/faculty';

export const FacultyOverviewPage: React.FC = () => {
  const [overview, setOverview] = useState<FacultyOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await facultyApi.getOverview();
      setOverview(data);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load faculty overview.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '2.5rem', color: '#71717A', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <RefreshCw size={18} className="animate-spin" color="#6366F1" />
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.85rem' }}>
          ASSEMBLING FACULTY INTELLIGENCE & ACADEMIC STANDING…
        </span>
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div style={{ padding: '2.5rem' }}>
        <div
          style={{
            padding: '1.5rem',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            color: '#FCA5A5',
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>FACULTY INTELLIGENCE UNAVAILABLE</div>
          <div style={{ fontSize: '0.875rem', marginBottom: '1rem' }}>{error}</div>
          <button
            onClick={fetchOverview}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#EF4444',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.8rem',
            }}
          >
            TRY AGAIN
          </button>
        </div>
      </div>
    );
  }

  const riskDist = overview.risk_distribution || { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
  const totalMonitored = overview.students_monitored || 1;
  const criticalCount = riskDist.CRITICAL || 0;
  const highCount = riskDist.HIGH || 0;
  const mediumCount = riskDist.MEDIUM || 0;
  const lowCount = riskDist.LOW || 0;

  return (
    <div style={{ padding: '2rem 2.5rem', maxWidth: '1400px', width: '100%', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '2rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
            <span
              style={{
                fontSize: '0.7rem',
                fontFamily: "'JetBrains Mono', monospace",
                color: '#6366F1',
                fontWeight: 600,
                letterSpacing: '0.08em',
              }}
            >
              PHASE 10 · DECISION SUPPORT
            </span>
            <span style={{ color: 'rgba(255, 255, 255, 0.2)' }}>/</span>
            <span style={{ fontSize: '0.75rem', color: '#A1A1AA' }}>
              {overview.department_name || overview.department_scope || 'Authorized Department'}
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#FFFFFF', margin: 0, letterSpacing: '-0.02em' }}>
            Faculty Intelligence Overview
          </h1>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontSize: '0.75rem',
              color: '#71717A',
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            <Clock size={13} />
            <span>LAST EVALUATION: {new Date(overview.last_analysis_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
          <button
            onClick={fetchOverview}
            title="Refresh Intelligence"
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
      </div>

      {/* KPI Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          marginBottom: '2rem',
        }}
      >
        {/* Metric 1: Students Monitored */}
        <div
          style={{
            backgroundColor: '#0F0F12',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
            <span style={{ fontSize: '0.72rem', color: '#71717A', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Students Monitored
            </span>
            <Users size={16} color="#6366F1" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FFFFFF', lineHeight: 1 }}>
            {overview.students_monitored}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#52525B', marginTop: '0.4rem' }}>
            Active department records
          </div>
        </div>

        {/* Metric 2: Avg Current CGPA */}
        <div
          style={{
            backgroundColor: '#0F0F12',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
            <span style={{ fontSize: '0.72rem', color: '#71717A', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Average Current CGPA
            </span>
            <TrendingUp size={16} color="#10B981" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FFFFFF', lineHeight: 1 }}>
            {overview.average_current_cgpa !== null ? overview.average_current_cgpa.toFixed(2) : 'N/A'}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#52525B', marginTop: '0.4rem' }}>
            Historical baseline
          </div>
        </div>

        {/* Metric 3: Avg Predicted CGPA */}
        <div
          style={{
            backgroundColor: '#0F0F12',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
            <span style={{ fontSize: '0.72rem', color: '#71717A', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Predicted CGPA (Phase 3)
            </span>
            <Sparkles size={16} color="#6366F1" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#6366F1', lineHeight: 1 }}>
            {overview.average_predicted_cgpa !== null ? overview.average_predicted_cgpa.toFixed(2) : 'N/A'}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#52525B', marginTop: '0.4rem' }}>
            AI champion projection
          </div>
        </div>

        {/* Metric 4: High / Critical Risk */}
        <div
          style={{
            backgroundColor: '#0F0F12',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
            <span style={{ fontSize: '0.72rem', color: '#71717A', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              At-Risk Population
            </span>
            <AlertTriangle size={16} color="#EF4444" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: criticalCount + highCount > 0 ? '#EF4444' : '#10B981', lineHeight: 1 }}>
            {criticalCount + highCount}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#71717A', marginTop: '0.4rem', display: 'flex', gap: '0.5rem' }}>
            <span>Crit: {criticalCount}</span>
            <span>·</span>
            <span>High: {highCount}</span>
          </div>
        </div>

        {/* Metric 5: Attendance Rate */}
        <div
          style={{
            backgroundColor: '#0F0F12',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
            <span style={{ fontSize: '0.72rem', color: '#71717A', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Avg Attendance Rate
            </span>
            <Activity size={16} color="#38BDF8" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FFFFFF', lineHeight: 1 }}>
            {overview.attendance_overview.average_attendance !== null
              ? `${overview.attendance_overview.average_attendance.toFixed(1)}%`
              : 'N/A'}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#EF4444', marginTop: '0.4rem' }}>
            {overview.attendance_overview.below_75_count} below 75% minimum
          </div>
        </div>

        {/* Metric 6: Backlog Overview */}
        <div
          style={{
            backgroundColor: '#0F0F12',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
            <span style={{ fontSize: '0.72rem', color: '#71717A', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Active Course Backlogs
            </span>
            <BookOpen size={16} color="#F59E0B" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FFFFFF', lineHeight: 1 }}>
            {overview.backlog_overview.total_backlogs}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#71717A', marginTop: '0.4rem' }}>
            {overview.backlog_overview.students_with_backlogs} students ({overview.backlog_overview.students_with_backlogs_pct}%)
          </div>
        </div>
      </div>

      {/* Main Section: Risk Distribution + Actionable Academic Alerts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Risk Distribution Card */}
        <div
          style={{
            backgroundColor: '#0A0A0C',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
                Academic Risk Distribution (Phase 4)
              </h2>
              <div style={{ fontSize: '0.75rem', color: '#71717A' }}>
                Multi-class classification breakdown across monitored students
              </div>
            </div>
            <button
              onClick={() => navigate('/faculty/students')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.3rem',
                fontSize: '0.75rem',
                color: '#6366F1',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              <span>EXPLORE QUEUE</span>
              <ArrowUpRight size={14} />
            </button>
          </div>

          {/* Stacked Risk Proportion Bar */}
          <div
            style={{
              height: '14px',
              borderRadius: '7px',
              overflow: 'hidden',
              display: 'flex',
              backgroundColor: '#18181B',
              marginBottom: '1.5rem',
            }}
          >
            <div style={{ width: `${(criticalCount / totalMonitored) * 100}%`, backgroundColor: '#9333EA' }} title={`CRITICAL: ${criticalCount}`} />
            <div style={{ width: `${(highCount / totalMonitored) * 100}%`, backgroundColor: '#FF2D20' }} title={`HIGH: ${highCount}`} />
            <div style={{ width: `${(mediumCount / totalMonitored) * 100}%`, backgroundColor: '#FFB703' }} title={`MEDIUM: ${mediumCount}`} />
            <div style={{ width: `${(lowCount / totalMonitored) * 100}%`, backgroundColor: '#55A630' }} title={`LOW: ${lowCount}`} />
          </div>

          {/* Risk Tier Badges Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}>
            <div
              onClick={() => navigate('/faculty/students?risk_level=CRITICAL')}
              style={{
                padding: '0.85rem',
                backgroundColor: 'rgba(147, 51, 234, 0.08)',
                border: '1px solid rgba(147, 51, 234, 0.3)',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#D8B4FE', letterSpacing: '0.04em' }}>
                CRITICAL
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#FFFFFF', marginTop: '0.2rem' }}>
                {criticalCount}
              </div>
              <div style={{ fontSize: '0.68rem', color: '#A1A1AA' }}>
                {((criticalCount / totalMonitored) * 100).toFixed(0)}% of class
              </div>
            </div>

            <div
              onClick={() => navigate('/faculty/students?risk_level=HIGH')}
              style={{
                padding: '0.85rem',
                backgroundColor: 'rgba(255, 45, 32, 0.08)',
                border: '1px solid rgba(255, 45, 32, 0.3)',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#FF2D20', letterSpacing: '0.04em' }}>
                HIGH
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#FFFFFF', marginTop: '0.2rem' }}>
                {highCount}
              </div>
              <div style={{ fontSize: '0.68rem', color: '#A1A1AA' }}>
                {((highCount / totalMonitored) * 100).toFixed(0)}% of class
              </div>
            </div>

            <div
              onClick={() => navigate('/faculty/students?risk_level=MEDIUM')}
              style={{
                padding: '0.85rem',
                backgroundColor: 'rgba(255, 183, 3, 0.08)',
                border: '1px solid rgba(255, 183, 3, 0.3)',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#FFB703', letterSpacing: '0.04em' }}>
                MEDIUM
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#FFFFFF', marginTop: '0.2rem' }}>
                {mediumCount}
              </div>
              <div style={{ fontSize: '0.68rem', color: '#A1A1AA' }}>
                {((mediumCount / totalMonitored) * 100).toFixed(0)}% of class
              </div>
            </div>

            <div
              onClick={() => navigate('/faculty/students?risk_level=LOW')}
              style={{
                padding: '0.85rem',
                backgroundColor: 'rgba(85, 166, 48, 0.08)',
                border: '1px solid rgba(85, 166, 48, 0.3)',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#55A630', letterSpacing: '0.04em' }}>
                LOW
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#FFFFFF', marginTop: '0.2rem' }}>
                {lowCount}
              </div>
              <div style={{ fontSize: '0.68rem', color: '#A1A1AA' }}>
                {((lowCount / totalMonitored) * 100).toFixed(0)}% of class
              </div>
            </div>
          </div>
        </div>

        {/* Academic Alerts Stream */}
        <div
          style={{
            backgroundColor: '#0A0A0C',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              Actionable Academic Alerts
            </h2>
            <span
              style={{
                fontSize: '0.68rem',
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                color: '#A5B4FC',
                fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 600,
              }}
            >
              {overview.recent_alerts.length} ALERTS
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', maxHeight: '220px' }}>
            {overview.recent_alerts.length === 0 ? (
              <div style={{ color: '#71717A', fontSize: '0.8rem', padding: '1rem', textAlign: 'center' }}>
                No active academic alert thresholds triggered.
              </div>
            ) : (
              overview.recent_alerts.map((alert) => (
                <div
                  key={alert.id}
                  style={{
                    padding: '0.85rem',
                    borderRadius: '6px',
                    backgroundColor: '#121216',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.82rem', color: alert.severity === 'CRITICAL' ? '#FCA5A5' : '#E4E4E7' }}>
                      {alert.title}
                    </div>
                    <span
                      style={{
                        fontSize: '0.62rem',
                        padding: '0.15rem 0.4rem',
                        borderRadius: '3px',
                        fontWeight: 700,
                        backgroundColor: alert.severity === 'CRITICAL' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: alert.severity === 'CRITICAL' ? '#EF4444' : '#F59E0B',
                      }}
                    >
                      {alert.severity}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#A1A1AA', marginBottom: '0.4rem' }}>
                    {alert.description}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#6366F1', fontWeight: 500 }}>
                    Action: {alert.recommended_action}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Top Model Risk Factors & Quick Actions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem' }}>
        {/* Top Risk Factors */}
        <div
          style={{
            backgroundColor: '#0A0A0C',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              Top Identified Model Factors (Phase 5 XAI)
            </h2>
            <span style={{ fontSize: '0.7rem', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
              CROSS-STUDENT SHAP
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {overview.top_risk_factors.map((factor) => (
              <div
                key={factor.feature_code}
                style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '6px',
                  backgroundColor: '#121216',
                  border: '1px solid rgba(255, 255, 255, 0.04)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.82rem', color: '#FFFFFF' }}>{factor.factor_name}</div>
                  <div style={{ fontSize: '0.72rem', color: '#71717A' }}>{factor.description}</div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: '1rem' }}>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF' }}>
                    {factor.affected_students_count}
                  </div>
                  <div style={{ fontSize: '0.65rem', color: '#71717A' }}>students</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Center */}
        <div
          style={{
            backgroundColor: '#0A0A0C',
            border: '1px solid rgba(255, 255, 255, 0.07)',
            borderRadius: '8px',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: '0 0 0.4rem 0' }}>
              Decision Support Actions
            </h2>
            <div style={{ fontSize: '0.75rem', color: '#71717A', marginBottom: '1.25rem' }}>
              Direct evidence-based workflows for student advisement
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <button
                onClick={() => navigate('/faculty/students')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 1rem',
                  backgroundColor: '#6366F1',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Users size={16} />
                  <span>Review Priority Student Queue</span>
                </div>
                <ChevronRight size={16} />
              </button>

              <button
                onClick={() => navigate('/faculty/assistant')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 1rem',
                  backgroundColor: '#121216',
                  color: '#E4E4E7',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Sparkles size={16} color="#6366F1" />
                  <span>Consult Faculty AI Advisor</span>
                </div>
                <ChevronRight size={16} />
              </button>

              <button
                onClick={() => navigate('/faculty/analytics')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 1rem',
                  backgroundColor: '#121216',
                  color: '#E4E4E7',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Activity size={16} color="#38BDF8" />
                  <span>Explore Class Analytics</span>
                </div>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          <div
            style={{
              marginTop: '1.25rem',
              padding: '0.75rem',
              backgroundColor: '#08080A',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.04)',
              display: 'flex',
              gap: '0.5rem',
              alignItems: 'flex-start',
            }}
          >
            <Info size={14} color="#71717A" style={{ marginTop: '0.15rem', flexShrink: 0 }} />
            <div style={{ fontSize: '0.68rem', color: '#71717A', lineHeight: 1.4 }}>
              Predictions and risk indicators are decision-support signals. Faculty judgment and personal student context remain essential.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
