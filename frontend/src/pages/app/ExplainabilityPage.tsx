import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Info } from 'lucide-react';
import { AppPageHeader } from '../../components/layout/AppPageHeader';
import { Tabs } from '../../components/ui/Tabs';
import { Alert } from '../../components/ui/Alert';
import { Button } from '../../components/ui/Button';
import { LoadingPanel } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { useStudentData } from '../../contexts/StudentDataContext';
import { buildPredictionPayload } from '../../lib/prediction';
import { predictionApi } from '../../services/predictionApi';
import { useAsync } from '../../hooks/useAsync';
import type { ExplanationData } from '../../types';

type ExplainTab = 'cgpa' | 'risk';

export const ExplainabilityPage: React.FC = () => {
  const { student, loading, error, refresh } = useStudentData();
  const payload = useMemo(() => buildPredictionPayload(student), [student]);
  const [tab, setTab] = useState<ExplainTab>('cgpa');

  const explainCgpa = useAsync(
    () => (payload?.cgpa ? predictionApi.explainCgpa(payload.cgpa) : Promise.reject(new Error('NO_DATA'))),
    [payload]
  );
  const explainRisk = useAsync(
    () => (payload?.risk ? predictionApi.explainRisk(payload.risk) : Promise.reject(new Error('NO_DATA'))),
    [payload]
  );

  useEffect(() => {
    if (payload) {
      explainCgpa.run();
      explainRisk.run();
    }
  }, [payload]);

  const active = tab === 'cgpa' ? explainCgpa : explainRisk;
  const explanation: ExplanationData | null =
    (tab === 'cgpa' ? explainCgpa.data?.explanation : explainRisk.data?.explanation) ?? null;
  const modelName =
    (tab === 'cgpa' ? explainCgpa.data?.model_name : explainRisk.data?.model_name) ?? '—';
  const modelVer =
    (tab === 'cgpa' ? explainCgpa.data?.model_version : explainRisk.data?.model_version) ?? '—';

  if (loading) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="EXPLAINABILITY · PHASE 5" title="Loading…" />
        <LoadingPanel />
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="EXPLAINABILITY · PHASE 5" title="Profile unavailable" />
        <Alert variant="error">{error}</Alert>
        <Button onClick={refresh} style={{ marginTop: '0.8rem' }}>Retry</Button>
      </div>
    );
  }

  const globalImportance = explanation?.top_global_features
    ? Object.entries(explanation.top_global_features)
        .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
        .slice(0, 8)
    : [];

  return (
    <div className="app-page">
      <AppPageHeader
        eyebrow="EXPLAINABILITY · PHASE 5"
        title="WHY THE NUMBER?"
        description="SHAP-based attribution, explained in plain language against your actual values."
      />

      <Tabs
        tabs={[
          { id: 'cgpa', label: 'CGPA EXPLANATION' },
          { id: 'risk', label: 'RISK EXPLANATION' },
        ]}
        activeTab={tab}
        onChange={(id) => setTab(id as ExplainTab)}
      />

      <div className="xai-page-layout">
        {/* Model header */}
        <section className="panel xai-model">
          <span className="mono-label">MODEL // {explanation?.task_type ?? ''}</span>
          <span className="mono-label dim">{modelName} v{modelVer} · {explanation?.explainer_type ?? ''}</span>
          {explanation && (
            <div className="xai-base">
              <MetricInline label="BASE PREDICTION" value={explanation.base_value.toFixed(3)} />
              <MetricInline label="SHAP SUM ATTAINED" value={explanation.shap_sum.toFixed(3)} />
              <MetricInline label="FACTORS" value={String(explanation.top_factors.length)} />
            </div>
          )}
        </section>

        {!payload && (
          <EmptyState title="NO COMPLETE RECORD" body="A complete verified semester record is required to explain a prediction." />
        )}

        {!payload && !explanation && (
          <Alert variant="info">
            <span>Run a prediction first — or add missing academic fields — to unlock explanations.</span>
          </Alert>
        )}

        {!active.loading && !active.error && !explanation && (
          <EmptyState title="NO EXPLANATION YET" body="Generate the related prediction to see attributed reasons." />
        )}

        {active.loading && <LoadingPanel message="Computing SHAP attributions…" />}

        {active.error && !active.data && <Alert variant="error">{active.error}</Alert>}

        {explanation?.explanation_available === false && (
          <Alert variant="info"><span>Explanation is unavailable for this model configuration.</span></Alert>
        )}

        {explanation?.explanation_available && (
          <>
            {/* Directional factors */}
            <div className="shap-grid">
              <section className="panel shap-column">
                <div className="panel-head">
                  <span className="mono-label" style={{ color: 'var(--color-primary)' }}>POSITIVE ATTRIBUTION — BOOSTS</span>
                  <span className="mono-label dim">OFFSET UPWARD</span>
                </div>
                {explanation.positive_factors.length === 0 && <EmptyState title="NONE" />}
                {explanation.positive_factors.map((f) => (
                  <FactorCard key={f.feature_name} explain={f} direction="positive" />
                ))}
              </section>

              <section className="panel shap-column">
                <div className="panel-head">
                  <span className="mono-label" style={{ color: 'var(--risk-high)' }}>NEGATIVE ATTRIBUTION — DRAGS</span>
                  <span className="mono-label dim">OFFSET DOWNWARD</span>
                </div>
                {explanation.negative_factors.length === 0 && <EmptyState title="NONE" />}
                {explanation.negative_factors.map((f) => (
                  <FactorCard key={f.feature_name} explain={f} direction="negative" />
                ))}
              </section>
            </div>

            {/* Global importance */}
            {globalImportance.length > 0 && (
              <section className="panel dash-panel">
                <div className="panel-head"><span className="mono-label">GLOBAL FEATURE IMPORTANCE</span></div>
                {globalImportance.map(([name, val]) => (
                  <div key={name} className="factor-row global">
                    <div className="factor-name">{name.replace(/_/g, ' ').toUpperCase()}</div>
                    <div className="factor-track">
                      <span style={{ width: `${Math.min(Math.abs(val) * 12, 100)}%`, background: 'var(--color-primary)' }} />
                    </div>
                    <span className="mono-label">{val.toFixed(3)}</span>
                  </div>
                ))}
              </section>
            )}

            {/* Fairness + honest boundary */}
            <section className="xai-fairness">
              <div className="xai-fairness-head">
                <Info size={16} />
                <span className="mono-label">FAIRNESS AUDIT — {explanation.contains_demographic_factors ? 'DEMOGRAPHIC FACTORS PRESENT' : 'DEMOGRAPHIC FACTORS ABSENT'}</span>
              </div>
              <p>{explanation.fairness_note}</p>
            </section>
          </>
        )}

        <section className="panel dash-panel what-if-cta">
          <div className="panel-head">
            <span className="mono-label">WHAT-IF SIMULATOR</span>
            <span className="node-status-chip ready">AVAILABLE · PHASE 7</span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Adjust attendance, clear a backlog, shift mid-term marks — and preview the changed
            CGPA, risk level, and impact vs baseline. Powered by the same production models.
          </p>
          <Link to="/app/what-if" className="btn btn-primary btn-sm">
            OPEN SIMULATOR <ArrowRight size={14} />
          </Link>
        </section>
      </div>
    </div>
  );
};

const MetricInline: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
    <span className="mono-label dim">{label}</span>
    <span style={{ fontSize: '1.05rem', fontVariantNumeric: 'tabular-nums' }}>{value}</span>
  </div>
);

const FactorCard: React.FC<{ explain: ExplanationData['top_factors'][number]; direction: 'positive' | 'negative' }> = ({ explain, direction }) => {
  const color = direction === 'positive' ? 'var(--color-primary)' : 'var(--risk-high)';
  const sign = direction === 'positive' ? '+' : '−';
  return (
    <div className="factor-card" style={{ borderLeft: `2px solid ${color}` }}>
      <div className="factor-card-head">
        <span className="mono-label">{explain.display_name} · {explain.impact_level}</span>
        <span className="mono-label" style={{ color }}>{sign}{Math.abs(explain.shap_value).toFixed(3)}</span>
      </div>
      <p className="factor-card-explanation">“{explain.student_explanation}”</p>
      <span className="factor-card-value">
        YOUR VALUE: {explain.original_value}{explain.unit}{explain.is_demographic ? ' · demographic surface' : ''}
      </span>
    </div>
  );
};