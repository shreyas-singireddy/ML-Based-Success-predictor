import React, { useState, useEffect, useMemo } from 'react';
import {
  Lightbulb,
  Calendar,
  Layers,
  Filter,
  RefreshCw,
  Sparkles,
  ShieldCheck,
  SlidersHorizontal,
  Info,
} from 'lucide-react';
import { AppPageHeader } from '../../components/layout/AppPageHeader';
import { MetricDisplay } from '../../components/dashboard/MetricDisplay';
import { RecommendationCard } from '../../components/recommendations/RecommendationCard';
import { ActionPlanTimeline } from '../../components/recommendations/ActionPlanTimeline';
import { LoadingPanel } from '../../components/ui/Skeleton';
import { ErrorState } from '../../components/ui/ErrorState';
import { EmptyState } from '../../components/ui/EmptyState';
import { useStudentData } from '../../contexts/StudentDataContext';
import { recommendationApi } from '../../services/recommendationApi';
import { useAsync } from '../../hooks/useAsync';
import { buildPredictionPayload } from '../../lib/prediction';
import type {
  RecommendationResponse,
  RecommendationPriority,
  RecommendationCategory,
} from '../../types';

export const RecommendationsPage: React.FC = () => {
  const { student, loading: studentLoading, error: studentError, refresh: refreshStudent } = useStudentData();
  const [activeTab, setActiveTab] = useState<'ranked' | 'timeline' | 'evidence'>('ranked');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');

  const payload = useMemo(() => buildPredictionPayload(student), [student]);

  const recAsync = useAsync<RecommendationResponse>(
    () => {
      if (payload?.cgpa) {
        return recommendationApi.generate(payload.cgpa);
      }
      return Promise.reject(new Error('NO_DATA'));
    },
    [payload]
  );

  useEffect(() => {
    if (payload?.cgpa) {
      recAsync.run();
    }
  }, [payload]);

  const recData = recAsync.data;

  const filteredRecommendations = useMemo(() => {
    if (!recData?.recommendations) return [];
    return recData.recommendations.filter((rec) => {
      const matchPriority = priorityFilter === 'ALL' || rec.priority === priorityFilter;
      const matchCategory = categoryFilter === 'ALL' || rec.category === categoryFilter;
      return matchPriority && matchCategory;
    });
  }, [recData, priorityFilter, categoryFilter]);

  const categoriesAvailable = useMemo(() => {
    if (!recData?.recommendations) return [];
    return Array.from(new Set(recData.recommendations.map((r) => r.category)));
  }, [recData]);

  if (studentLoading) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="ACADEMIC GUIDANCE" title="Loading personalized recommendations…" />
        <LoadingPanel message="Synthesizing predictions, risk factors, and What-If evidence…" />
      </div>
    );
  }

  if (studentError) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="ACADEMIC GUIDANCE" title="Profile unavailable" />
        <ErrorState title="COULD NOT LOAD STUDENT PROFILE" message={studentError} onRetry={refreshStudent} />
      </div>
    );
  }

  if (!student) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="ACADEMIC GUIDANCE" title="No profile linked" />
        <EmptyState
          title="NO STUDENT PROFILE"
          body="Your user account is not linked to an active student record. Please contact administration."
        />
      </div>
    );
  }

  return (
    <div className="app-page">
      <AppPageHeader
        eyebrow={`AI RECOMMENDATION ENGINE // ${student.student_number}`}
        title="PERSONALIZED ACADEMIC ACTION PLAN"
        description="Evidence-backed, prioritized academic recommendations grounded in your actual course indicators, risk models, SHAP explanations, and What-If simulations."
        actions={
          <button
            className="btn btn-outline btn-sm"
            onClick={() => {
              refreshStudent();
              recAsync.run();
            }}
            disabled={recAsync.loading}
          >
            <RefreshCw size={14} className={recAsync.loading ? 'animate-spin' : ''} /> REFRESH
          </button>
        }
      />

      {/* Top Metric Strip */}
      {recData && (
        <div className="metric-grid">
          <MetricDisplay
            label="PROJECTED CGPA"
            value={recData.predicted_cgpa.toFixed(2)}
            sub={`Grade: ${recData.grade} · ${recData.performance_category}`}
          />
          <MetricDisplay
            label="ACADEMIC RISK"
            value={recData.risk_level}
            sub={`Score: ${recData.risk_score.toFixed(1)} / 100`}
            accent={
              recData.risk_level === 'CRITICAL'
                ? 'var(--risk-critical)'
                : recData.risk_level === 'HIGH'
                ? 'var(--risk-high)'
                : recData.risk_level === 'MEDIUM'
                ? 'var(--risk-medium)'
                : 'var(--risk-minimum)'
            }
          />
          <MetricDisplay
            label="ACTIONABLE ITEMS"
            value={recData.recommendations.length}
            sub={`${recData.action_plan.this_week.length} immediate priority`}
          />
          <MetricDisplay
            label="EVIDENCE SOURCES"
            value={recData.evidence_summary.simulation_levers_tested ? 'ML + WHAT-IF' : 'ML + POLICY'}
            sub={`Policy v${recData.policy_version}`}
          />
        </div>
      )}

      {/* View Switcher Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          borderBottom: '1px solid var(--hairline-subtle)',
          paddingBottom: '0.75rem',
          marginBottom: '1.25rem',
          flexWrap: 'wrap',
        }}
      >
        <button
          className={`btn btn-sm ${activeTab === 'ranked' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('ranked')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <Lightbulb size={15} /> RANKED ACTIONS ({recData?.recommendations.length ?? 0})
        </button>

        <button
          className={`btn btn-sm ${activeTab === 'timeline' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('timeline')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <Calendar size={15} /> ACTION TIMELINE (
          {(recData?.action_plan.this_week.length ?? 0) + (recData?.action_plan.next_30_days.length ?? 0)}
          )
        </button>

        <button
          className={`btn btn-sm ${activeTab === 'evidence' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('evidence')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <Layers size={15} /> EVIDENCE & MODEL METRICS
        </button>
      </div>

      {/* Loading state */}
      {recAsync.loading && (
        <LoadingPanel message="Evaluating multi-phase academic evidence and computing What-If simulation deltas…" />
      )}

      {/* Error state */}
      {recAsync.error && !recData && (
        <ErrorState
          title="RECOMMENDATIONS UNAVAILABLE"
          message={recAsync.error}
          onRetry={() => recAsync.run()}
        />
      )}

      {/* Main Content */}
      {recData && !recAsync.loading && (
        <>
          {/* TAB 1: RANKED RECOMMENDATIONS */}
          {activeTab === 'ranked' && (
            <div>
              {/* Filter controls */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                  marginBottom: '1.2rem',
                }}
              >
                {/* Priority Pills */}
                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
                  <span className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    PRIORITY:
                  </span>
                  {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((p) => (
                    <button
                      key={p}
                      className={`btn btn-sm ${priorityFilter === p ? 'btn-secondary' : 'btn-ghost'}`}
                      style={{
                        padding: '0.2rem 0.55rem',
                        fontSize: '0.72rem',
                        fontFamily: 'var(--font-mono)',
                      }}
                      onClick={() => setPriorityFilter(p)}
                    >
                      {p}
                    </button>
                  ))}
                </div>

                {/* Category Dropdown Filter */}
                {categoriesAvailable.length > 1 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      CATEGORY:
                    </span>
                    <select
                      className="input-select"
                      style={{
                        padding: '0.25rem 0.5rem',
                        fontSize: '0.75rem',
                        fontFamily: 'var(--font-mono)',
                        background: 'var(--bg-panel)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--hairline)',
                        borderRadius: 'var(--radius-sm)',
                      }}
                      value={categoryFilter}
                      onChange={(e) => setCategoryFilter(e.target.value)}
                    >
                      <option value="ALL">ALL CATEGORIES</option>
                      {categoriesAvailable.map((c) => (
                        <option key={c} value={c}>
                          {c.replace(/_/g, ' ')}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* List */}
              {filteredRecommendations.length === 0 ? (
                <EmptyState
                  title="NO MATCHING ACTIONS"
                  body={
                    priorityFilter !== 'ALL' || categoryFilter !== 'ALL'
                      ? 'No recommendations match the current filter criteria.'
                      : "You're currently on track! No critical academic interventions were identified."
                  }
                />
              ) : (
                filteredRecommendations.map((rec, index) => (
                  <RecommendationCard key={rec.id} recommendation={rec} rank={index + 1} />
                ))
              )}
            </div>
          )}

          {/* TAB 2: ACTION PLAN TIMELINE */}
          {activeTab === 'timeline' && <ActionPlanTimeline actionPlan={recData.action_plan} />}

          {/* TAB 3: EVIDENCE & MODEL METRICS */}
          {activeTab === 'evidence' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div className="panel" style={{ padding: '1.25rem' }}>
                <div
                  className="mono-label"
                  style={{
                    color: 'var(--color-primary-hover)',
                    marginBottom: '0.8rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                  }}
                >
                  <Sparkles size={16} /> EVIDENCE PIPELINE & VERIFICATION TELEMETRY
                </div>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                    gap: '1rem',
                  }}
                >
                  <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                    <div className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      INDICATORS ANALYZED
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {recData.evidence_summary.factors_analyzed} Factors
                    </div>
                  </div>

                  <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                    <div className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      DETERMINISTIC RULES
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {recData.evidence_summary.rules_evaluated} Rules Evaluated
                    </div>
                  </div>

                  <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                    <div className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      WHAT-IF SIMULATION LEVERS
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--color-info)' }}>
                      {recData.evidence_summary.simulation_levers_tested} Scenarios Simulated
                    </div>
                  </div>

                  <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                    <div className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      SHAP EXPLAINABILITY
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--color-success)' }}>
                      {recData.evidence_summary.shap_evidence_attached ? 'Attributed & Aligned' : 'Unavailable'}
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    marginTop: '1.25rem',
                    padding: '0.85rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--hairline-subtle)',
                  }}
                >
                  <div className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                    UNDERLYING MODEL ARTIFACTS
                  </div>
                  <div style={{ fontSize: '0.82rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                    <div>CGPA Regression: {recData.model_version_info.cgpa_model}</div>
                    <div>Risk Classification: {recData.model_version_info.risk_model}</div>
                    <div>Recommendation Policy: v{recData.policy_version}</div>
                    <div>Evaluation Timestamp: {new Date(recData.generated_at).toLocaleString()}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Disclaimer Footer */}
          <div
            style={{
              marginTop: '1.5rem',
              padding: '0.85rem 1rem',
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--hairline-subtle)',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.6rem',
              color: 'var(--text-muted)',
              fontSize: '0.78rem',
            }}
          >
            <Info size={16} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--color-primary)' }} />
            <div>
              <strong>ACADEMIC DECISION SUPPORT DISCLAIMER:</strong> {recData.disclaimer}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
