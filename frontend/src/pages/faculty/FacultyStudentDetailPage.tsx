import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  GraduationCap,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Activity,
  BookOpen,
  Sparkles,
  CheckCircle2,
  Clock,
  Sliders,
  ShieldCheck,
  Info,
  Calendar,
  Layers,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';
import { facultyApi } from '../../services/facultyApi';
import { interventionApi } from '../../services/interventionApi';
import { FacultyStudentDossier } from '../../types/faculty';
import { RecommendationItem } from '../../types';

export const FacultyStudentDetailPage: React.FC = () => {
  const { studentId } = useParams<{ studentId: string }>();
  const navigate = useNavigate();

  const [dossier, setDossier] = useState<FacultyStudentDossier | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Intervention review checklist state
  const [reviewStatus, setReviewStatus] = useState<'PENDING' | 'CONTACTED' | 'RECOMMENDED_SUPPORT' | 'FOLLOWUP_SCHEDULED'>('PENDING');
  const [facultyNote, setFacultyNote] = useState('');
  const [noteSaved, setNoteSaved] = useState(false);
  const [savingIntervention, setSavingIntervention] = useState(false);


  const fetchDossier = async () => {
    if (!studentId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await facultyApi.getStudentDossier(studentId);
      setDossier(res);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load student dossier.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDossier();
  }, [studentId]);

  if (loading) {
    return (
      <div style={{ padding: '3rem', color: '#71717A', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <RefreshCw size={18} className="animate-spin" color="#6366F1" />
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.85rem' }}>
          ASSEMBLING COMPREHENSIVE STUDENT INTELLIGENCE DOSSIER…
        </span>
      </div>
    );
  }

  if (error || !dossier) {
    return (
      <div style={{ padding: '2.5rem' }}>
        <button
          onClick={() => navigate('/faculty/students')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            background: 'none',
            border: 'none',
            color: '#71717A',
            cursor: 'pointer',
            fontSize: '0.8rem',
            marginBottom: '1rem',
          }}
        >
          <ArrowLeft size={16} />
          <span>Back to Priority Queue</span>
        </button>
        <div style={{ padding: '1.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#FCA5A5' }}>
          <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>STUDENT DOSSIER UNAVAILABLE</div>
          <div style={{ fontSize: '0.85rem' }}>{error}</div>
        </div>
      </div>
    );
  }

  const s = dossier.student;
  const trend = dossier.trend_analysis;

  return (
    <div style={{ padding: '2rem 2.5rem', maxWidth: '1400px', width: '100%', margin: '0 auto' }}>
      {/* Top Breadcrumb & Navigation */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <button
          onClick={() => navigate('/faculty/students')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            background: 'none',
            border: 'none',
            color: '#A1A1AA',
            cursor: 'pointer',
            fontSize: '0.8rem',
            fontWeight: 600,
            padding: 0,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#FFFFFF')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#A1A1AA')}
        >
          <ArrowLeft size={16} />
          <span>Back to Priority Queue</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span
            style={{
              fontSize: '0.7rem',
              fontFamily: "'JetBrains Mono', monospace",
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              backgroundColor: '#18181B',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#A1A1AA',
            }}
          >
            MODEL: {dossier.model_version}
          </span>
          <span
            style={{
              fontSize: '0.7rem',
              fontFamily: "'JetBrains Mono', monospace",
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              backgroundColor: '#18181B',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#A1A1AA',
            }}
          >
            RISK CLASSIFIER: {dossier.risk_model_version}
          </span>
        </div>
      </div>

      {/* Student Profile Header Card */}
      <div
        style={{
          backgroundColor: '#0A0A0C',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '8px',
          padding: '1.5rem 1.75rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              backgroundColor: '#18181B',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#6366F1',
              fontWeight: 700,
              fontSize: '1.1rem',
            }}
          >
            {s.name.charAt(0)}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFFFFF', margin: 0 }}>{s.name}</h1>
              <span
                style={{
                  fontSize: '0.68rem',
                  fontFamily: "'JetBrains Mono', monospace",
                  padding: '0.15rem 0.45rem',
                  borderRadius: '4px',
                  backgroundColor: '#18181B',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#A1A1AA',
                }}
              >
                {s.student_number}
              </span>
            </div>
            <div style={{ fontSize: '0.78rem', color: '#71717A', marginTop: '0.2rem' }}>
              {s.department_name || s.department_code || 'Department of Computer Science'} · Semester {s.current_semester} · Age {s.gender}
            </div>
          </div>
        </div>

        {/* Status Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              padding: '0.45rem 0.85rem',
              borderRadius: '6px',
              backgroundColor:
                s.priority_tier === 'CRITICAL'
                  ? 'rgba(147, 51, 234, 0.15)'
                  : s.priority_tier === 'HIGH'
                  ? 'rgba(255, 45, 32, 0.15)'
                  : s.priority_tier === 'MEDIUM'
                  ? 'rgba(255, 183, 3, 0.15)'
                  : 'rgba(85, 166, 48, 0.15)',
              border: `1px solid ${
                s.priority_tier === 'CRITICAL'
                  ? 'rgba(147, 51, 234, 0.4)'
                  : s.priority_tier === 'HIGH'
                  ? 'rgba(255, 45, 32, 0.4)'
                  : s.priority_tier === 'MEDIUM'
                  ? 'rgba(255, 183, 3, 0.4)'
                  : 'rgba(85, 166, 48, 0.4)'
              }`,
              textAlign: 'right',
            }}
          >
            <div style={{ fontSize: '0.65rem', fontWeight: 600, color: '#A1A1AA', textTransform: 'uppercase' }}>
              Intervention Urgency
            </div>
            <div
              style={{
                fontSize: '0.95rem',
                fontWeight: 800,
                color:
                  s.priority_tier === 'CRITICAL'
                    ? '#D8B4FE'
                    : s.priority_tier === 'HIGH'
                    ? '#FF2D20'
                    : s.priority_tier === 'MEDIUM'
                    ? '#FFB703'
                    : '#55A630',
              }}
            >
              {s.priority_tier} PRIORITY ({s.priority_score.toFixed(0)})
            </div>
          </div>
        </div>
      </div>

      {/* 4-KPI Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        {/* Metric 1: Current CGPA */}
        <div style={{ backgroundColor: '#0F0F12', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.72rem', color: '#71717A', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            Current Standing CGPA
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FFFFFF', lineHeight: 1 }}>
            {s.current_cgpa !== null ? s.current_cgpa.toFixed(2) : 'N/A'}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#52525B', marginTop: '0.4rem' }}>Recorded academic baseline</div>
        </div>

        {/* Metric 2: Predicted CGPA */}
        <div style={{ backgroundColor: '#0F0F12', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.72rem', color: '#71717A', fontWeight: 600, textTransform: 'uppercase' }}>
              Predicted CGPA (Phase 3)
            </span>
            <Sparkles size={14} color="#6366F1" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#6366F1', lineHeight: 1 }}>
            {dossier.predicted_cgpa !== null ? dossier.predicted_cgpa.toFixed(2) : 'N/A'}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#71717A', marginTop: '0.4rem' }}>
            Confidence: {dossier.prediction_confidence !== null ? `${(dossier.prediction_confidence * 100).toFixed(0)}%` : 'Standard'}
          </div>
        </div>

        {/* Metric 3: Academic Risk */}
        <div style={{ backgroundColor: '#0F0F12', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.72rem', color: '#71717A', fontWeight: 600, textTransform: 'uppercase' }}>
              Risk Classification
            </span>
            <AlertTriangle size={14} color={dossier.risk_level === 'CRITICAL' || dossier.risk_level === 'HIGH' ? '#EF4444' : '#10B981'} />
          </div>
          <div
            style={{
              fontSize: '2rem',
              fontWeight: 800,
              color:
                dossier.risk_level === 'CRITICAL'
                  ? '#D8B4FE'
                  : dossier.risk_level === 'HIGH'
                  ? '#FF2D20'
                  : dossier.risk_level === 'MEDIUM'
                  ? '#FFB703'
                  : '#55A630',
              lineHeight: 1,
            }}
          >
            {dossier.risk_level}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#71717A', marginTop: '0.4rem' }}>
            Risk Score: {dossier.risk_score.toFixed(1)} / 100.0
          </div>
        </div>

        {/* Metric 4: Attendance & Backlogs */}
        <div style={{ backgroundColor: '#0F0F12', border: '1px solid rgba(255, 255, 255, 0.07)', borderRadius: '8px', padding: '1.25rem' }}>
          <div style={{ fontSize: '0.72rem', color: '#71717A', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            Attendance & Backlogs
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FFFFFF', lineHeight: 1 }}>
            {s.attendance_percentage !== null ? `${s.attendance_percentage.toFixed(0)}%` : 'N/A'}
          </div>
          <div style={{ fontSize: '0.72rem', color: s.backlogs > 0 ? '#F59E0B' : '#52525B', marginTop: '0.4rem' }}>
            {s.backlogs} pending backlog course(s)
          </div>
        </div>
      </div>

      {/* Academic Trend Progression Timeline */}
      <div
        style={{
          backgroundColor: '#0A0A0C',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              Academic Performance Trajectory
            </h2>
            <div style={{ fontSize: '0.75rem', color: '#71717A' }}>
              Historical recorded semester terms → Current CGPA → Predicted CGPA projection
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.35rem 0.75rem',
              borderRadius: '6px',
              backgroundColor:
                trend.trend_direction === 'IMPROVING'
                  ? 'rgba(16, 185, 129, 0.15)'
                  : trend.trend_direction === 'DECLINING'
                  ? 'rgba(239, 68, 68, 0.15)'
                  : 'rgba(113, 113, 122, 0.15)',
              color:
                trend.trend_direction === 'IMPROVING'
                  ? '#10B981'
                  : trend.trend_direction === 'DECLINING'
                  ? '#EF4444'
                  : '#A1A1AA',
              fontWeight: 700,
              fontSize: '0.75rem',
            }}
          >
            {trend.trend_direction === 'IMPROVING' && <TrendingUp size={14} />}
            {trend.trend_direction === 'DECLINING' && <TrendingDown size={14} />}
            {trend.trend_direction === 'STABLE' && <Minus size={14} />}
            <span>TRAJECTORY: {trend.trend_direction}</span>
          </div>
        </div>

        {/* Timeline Sequence */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            overflowX: 'auto',
            padding: '1rem 0',
          }}
        >
          {trend.semester_history.map((rec) => (
            <div
              key={rec.semester}
              style={{
                minWidth: '130px',
                padding: '0.85rem',
                backgroundColor: '#121216',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                borderRadius: '6px',
                position: 'relative',
              }}
            >
              <div style={{ fontSize: '0.68rem', color: '#71717A', fontFamily: "'JetBrains Mono', monospace" }}>
                SEM 0{rec.semester} · HISTORICAL
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#FFFFFF', marginTop: '0.25rem' }}>
                {rec.semester_cgpa !== null ? rec.semester_cgpa.toFixed(2) : '—'}
              </div>
              <div style={{ fontSize: '0.68rem', color: '#A1A1AA', marginTop: '0.2rem' }}>
                Att: {rec.attendance.toFixed(0)}% · BL: {rec.backlogs}
              </div>
            </div>
          ))}

          {/* Current Standing Card */}
          <div
            style={{
              minWidth: '140px',
              padding: '0.85rem',
              backgroundColor: 'rgba(99, 102, 241, 0.08)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '6px',
            }}
          >
            <div style={{ fontSize: '0.68rem', color: '#A5B4FC', fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}>
              CURRENT STANDING
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#FFFFFF', marginTop: '0.25rem' }}>
              {trend.current_cgpa !== null ? trend.current_cgpa.toFixed(2) : '—'}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#A5B4FC', marginTop: '0.2rem' }}>
              Recorded baseline
            </div>
          </div>

          {/* Predicted Card */}
          <div
            style={{
              minWidth: '150px',
              padding: '0.85rem',
              backgroundColor: 'rgba(99, 102, 241, 0.18)',
              border: '1px solid #6366F1',
              borderRadius: '6px',
            }}
          >
            <div style={{ fontSize: '0.68rem', color: '#C7D2FE', fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}>
              PROJECTED (PHASE 3)
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#6366F1', marginTop: '0.25rem' }}>
              {trend.predicted_cgpa !== null ? trend.predicted_cgpa.toFixed(2) : '—'}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#C7D2FE', marginTop: '0.2rem' }}>
              Delta: {trend.delta_cgpa !== null ? `${trend.delta_cgpa > 0 ? '+' : ''}${trend.delta_cgpa.toFixed(2)}` : '0.00'}
            </div>
          </div>
        </div>

        <div style={{ fontSize: '0.78rem', color: '#A1A1AA', marginTop: '0.5rem', lineHeight: 1.5 }}>
          {trend.trend_description}
        </div>
      </div>

      {/* Two-Column Section: XAI Explainability + Phase 8 Recommendations */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Phase 5 Explainable AI Factors */}
        <div
          style={{
            backgroundColor: '#0A0A0C',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '8px',
            padding: '1.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
                Explainable AI Factor Analysis (Phase 5 SHAP)
              </h2>
              <div style={{ fontSize: '0.72rem', color: '#71717A' }}>
                Model attribution breakdown identifying primary features influencing risk
              </div>
            </div>
          </div>

          <div
            style={{
              padding: '0.85rem',
              backgroundColor: '#121216',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              borderRadius: '6px',
              fontSize: '0.78rem',
              color: '#E4E4E7',
              marginBottom: '1rem',
              lineHeight: 1.5,
            }}
          >
            {dossier.faculty_explanation_summary}
          </div>

          {/* Top Contributing Factors List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {dossier.explanation?.top_factors && dossier.explanation.top_factors.length > 0 ? (
              dossier.explanation.top_factors.slice(0, 4).map((factor, idx) => (
                <div
                  key={factor.feature_name}
                  style={{
                    padding: '0.75rem',
                    backgroundColor: '#121216',
                    border: '1px solid rgba(255, 255, 255, 0.04)',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.8rem', color: '#FFFFFF' }}>
                      {factor.display_name}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: '#71717A' }}>
                      Observed: {factor.original_value !== null ? factor.original_value : '—'} {factor.unit}
                    </div>
                  </div>

                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      padding: '0.2rem 0.45rem',
                      borderRadius: '4px',
                      backgroundColor:
                        factor.impact_level === 'HIGH'
                          ? 'rgba(239, 68, 68, 0.15)'
                          : factor.impact_level === 'MEDIUM'
                          ? 'rgba(245, 158, 11, 0.15)'
                          : 'rgba(113, 113, 122, 0.15)',
                      color:
                        factor.impact_level === 'HIGH'
                          ? '#EF4444'
                          : factor.impact_level === 'MEDIUM'
                          ? '#F59E0B'
                          : '#A1A1AA',
                    }}
                  >
                    {factor.impact_level} IMPACT
                  </span>
                </div>
              ))
            ) : (
              <div style={{ fontSize: '0.78rem', color: '#71717A', padding: '0.5rem' }}>
                Standard factor distributions across evaluated baseline features.
              </div>
            )}
          </div>
        </div>

        {/* Phase 8 Grouped Faculty Action Recommendations */}
        <div
          style={{
            backgroundColor: '#0A0A0C',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '8px',
            padding: '1.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
                Faculty Action Priorities (Phase 8)
              </h2>
              <div style={{ fontSize: '0.72rem', color: '#71717A' }}>
                Evidence-backed intervention pathways organized by urgency
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {/* Immediate Attention Group */}
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#EF4444', textTransform: 'uppercase', marginBottom: '0.4rem', letterSpacing: '0.04em' }}>
                Immediate Attention
              </div>
              {dossier.grouped_recommendations.immediate_attention.length === 0 ? (
                <div style={{ fontSize: '0.75rem', color: '#52525B', padding: '0.2rem 0' }}>No critical immediate flags.</div>
              ) : (
                dossier.grouped_recommendations.immediate_attention.map((rec) => (
                  <div
                    key={rec.id}
                    style={{
                      padding: '0.75rem',
                      backgroundColor: 'rgba(239, 68, 68, 0.06)',
                      border: '1px solid rgba(239, 68, 68, 0.2)',
                      borderRadius: '6px',
                      marginBottom: '0.4rem',
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.8rem', color: '#FFFFFF' }}>{rec.title}</div>
                    <div style={{ fontSize: '0.72rem', color: '#D4D4D8', marginTop: '0.2rem' }}>{rec.action}</div>
                  </div>
                ))
              )}
            </div>

            {/* Short-Term Support Group */}
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#F59E0B', textTransform: 'uppercase', marginBottom: '0.4rem', letterSpacing: '0.04em' }}>
                Short-Term Support (Next 30 Days)
              </div>
              {dossier.grouped_recommendations.short_term.length === 0 ? (
                <div style={{ fontSize: '0.75rem', color: '#52525B', padding: '0.2rem 0' }}>No short-term milestones needed.</div>
              ) : (
                dossier.grouped_recommendations.short_term.map((rec) => (
                  <div
                    key={rec.id}
                    style={{
                      padding: '0.75rem',
                      backgroundColor: 'rgba(245, 158, 11, 0.06)',
                      border: '1px solid rgba(245, 158, 11, 0.2)',
                      borderRadius: '6px',
                      marginBottom: '0.4rem',
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.8rem', color: '#FFFFFF' }}>{rec.title}</div>
                    <div style={{ fontSize: '0.72rem', color: '#D4D4D8', marginTop: '0.2rem' }}>{rec.action}</div>
                  </div>
                ))
              )}
            </div>

            {/* Monitor Group */}
            {dossier.grouped_recommendations.monitor.length > 0 && (
              <div>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#38BDF8', textTransform: 'uppercase', marginBottom: '0.4rem', letterSpacing: '0.04em' }}>
                  Monitor & Maintain
                </div>
                {dossier.grouped_recommendations.monitor.slice(0, 2).map((rec) => (
                  <div
                    key={rec.id}
                    style={{
                      padding: '0.75rem',
                      backgroundColor: 'rgba(56, 189, 248, 0.06)',
                      border: '1px solid rgba(56, 189, 248, 0.2)',
                      borderRadius: '6px',
                      marginBottom: '0.4rem',
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.8rem', color: '#FFFFFF' }}>{rec.title}</div>
                    <div style={{ fontSize: '0.72rem', color: '#D4D4D8', marginTop: '0.2rem' }}>{rec.action}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Intervention Decision Support Workflow Card */}
      <div
        style={{
          backgroundColor: '#0A0A0C',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <ShieldCheck size={18} color="#6366F1" />
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#FFFFFF', margin: 0 }}>
              Faculty Intervention Decision Support
            </h2>
          </div>
          <span style={{ fontSize: '0.72rem', color: '#A5B4FC', fontFamily: "'JetBrains Mono', monospace" }}>
            HUMAN DECISION WORKFLOW
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '1.5rem', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '0.78rem', color: '#A1A1AA', marginBottom: '0.75rem' }}>
              Select intervention action taken for this student:
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              {[
                { id: 'PENDING', label: 'Review Pending' },
                { id: 'CONTACTED', label: 'Student Contacted' },
                { id: 'RECOMMENDED_SUPPORT', label: 'Recommended Tutoring / Remedial' },
                { id: 'FOLLOWUP_SCHEDULED', label: 'Scheduled Follow-Up' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setReviewStatus(opt.id as any)}
                  style={{
                    padding: '0.45rem 0.8rem',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    backgroundColor: reviewStatus === opt.id ? 'rgba(99, 102, 241, 0.2)' : '#121216',
                    border: reviewStatus === opt.id ? '1px solid #6366F1' : '1px solid rgba(255, 255, 255, 0.08)',
                    color: reviewStatus === opt.id ? '#FFFFFF' : '#A1A1AA',
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <textarea
              placeholder="Record confidential faculty notes regarding advising session or intervention plan..."
              value={facultyNote}
              onChange={(e) => {
                setFacultyNote(e.target.value);
                setNoteSaved(false);
              }}
              rows={3}
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: '#121216',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '6px',
                color: '#FFFFFF',
                fontSize: '0.8rem',
                outline: 'none',
                marginBottom: '0.75rem',
              }}
            />

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
              <button
                disabled={savingIntervention}
                onClick={async () => {
                  if (!facultyNote && reviewStatus === 'PENDING') {
                    alert('Please enter advising notes or select an intervention action.');
                    return;
                  }
                  setSavingIntervention(true);
                  try {
                    await interventionApi.createIntervention({
                      student_id: s.id,
                      category:
                        reviewStatus === 'RECOMMENDED_SUPPORT'
                          ? 'SUBJECT_SUPPORT'
                          : reviewStatus === 'FOLLOWUP_SCHEDULED'
                          ? 'STUDY_PLAN'
                          : 'ACADEMIC_COUNSELLING',
                      title: `Faculty Advising: ${reviewStatus.replace(/_/g, ' ')}`,
                      description: facultyNote || `Faculty logged action: ${reviewStatus.replace(/_/g, ' ')}`,
                      priority: s.risk_level === 'HIGH' || s.risk_level === 'CRITICAL' ? 'HIGH' : 'MEDIUM',
                      status: reviewStatus === 'FOLLOWUP_SCHEDULED' ? 'FOLLOW_UP_REQUIRED' : 'IN_PROGRESS',
                      notes: facultyNote,
                    });
                    setNoteSaved(true);
                    setFacultyNote('');
                  } catch (err: any) {
                    alert(err?.response?.data?.detail || 'Failed to save intervention.');
                  } finally {
                    setSavingIntervention(false);
                  }
                }}
                style={{
                  padding: '0.45rem 1rem',
                  backgroundColor: '#6366F1',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                }}
              >
                {savingIntervention ? 'Saving Intervention...' : 'Log Intervention Record'}
              </button>
              <button
                onClick={() => navigate(`/faculty/interventions?student_id=${s.id}`)}
                style={{
                  padding: '0.45rem 0.85rem',
                  backgroundColor: '#18181B',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  color: '#A1A1AA',
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                }}
              >
                View Interventions & Outcomes →
              </button>
              {noteSaved && (
                <span style={{ fontSize: '0.75rem', color: '#10B981', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  <CheckCircle2 size={14} />
                  <span>Intervention logged for review</span>
                </span>
              )}
            </div>

          </div>

          <div
            style={{
              padding: '1rem',
              backgroundColor: '#121216',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}
          >
            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#6366F1', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
              Ask Faculty AI Advisor
            </div>
            <div style={{ fontSize: '0.75rem', color: '#A1A1AA', marginBottom: '0.75rem' }}>
              Get conversational grounded insights about {s.name}'s risk factors and tailored advising strategies.
            </div>
            <button
              onClick={() => navigate(`/faculty/assistant?student_id=${s.id}`)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.4rem',
                padding: '0.55rem',
                backgroundColor: '#18181B',
                border: '1px solid rgba(99, 102, 241, 0.4)',
                borderRadius: '6px',
                color: '#A5B4FC',
                fontWeight: 600,
                fontSize: '0.78rem',
                cursor: 'pointer',
              }}
            >
              <Sparkles size={14} color="#6366F1" />
              <span>Ask AI About This Student</span>
            </button>
          </div>
        </div>
      </div>

      {/* Decision Support Disclaimer */}
      <div
        style={{
          padding: '1rem 1.25rem',
          backgroundColor: '#08080A',
          borderRadius: '6px',
          border: '1px solid rgba(255, 255, 255, 0.04)',
          display: 'flex',
          gap: '0.6rem',
          alignItems: 'flex-start',
        }}
      >
        <Info size={16} color="#71717A" style={{ marginTop: '0.1rem', flexShrink: 0 }} />
        <div style={{ fontSize: '0.72rem', color: '#71717A', lineHeight: 1.5 }}>
          {dossier.disclaimer}
        </div>
      </div>
    </div>
  );
};
