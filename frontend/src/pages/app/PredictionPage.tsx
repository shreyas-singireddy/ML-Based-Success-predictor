import React, { useEffect, useMemo, useState } from 'react';
import { Calculator, RotateCcw } from 'lucide-react';
import { AppPageHeader } from '../../components/layout/AppPageHeader';
import { Alert } from '../../components/ui/Alert';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { MetricDisplay } from '../../components/dashboard/MetricDisplay';
import { LoadingPanel } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { useStudentData } from '../../contexts/StudentDataContext';
import { getLatestRecord } from '../../lib/prediction';
import { predictionApi } from '../../services/predictionApi';
import { useAsync } from '../../hooks/useAsync';
import type { CGPAPredictionRequest } from '../../types';

type NumFieldKeys =
  | 'attendance_percentage'
  | 'previous_cgpa'
  | 'mid_1'
  | 'mid_2'
  | 'internal_marks'
  | 'backlogs';

const FIELD_LIMITS: Record<NumFieldKeys, { min: number; max: number; label: string }> = {
  attendance_percentage: { min: 0, max: 100, label: 'Attendance %' },
  previous_cgpa: { min: 0, max: 10, label: 'Previous CGPA / 10' },
  mid_1: { min: 0, max: 100, label: 'Mid 1 Marks / 100' },
  mid_2: { min: 0, max: 100, label: 'Mid 2 Marks / 100' },
  internal_marks: { min: 0, max: 100, label: 'Internal Marks / 100' },
  backlogs: { min: 0, max: 50, label: 'Open Backlogs' },
};

export const PredictionPage: React.FC = () => {
  const { student, loading, error: studentError, refresh } = useStudentData();
  const latest = useMemo(() => (student ? getLatestRecord(student) : null), [student]);

  const [form, setForm] = useState<CGPAPredictionRequest | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (latest && !form) {
      setForm({
        attendance_percentage: latest.attendance_percentage,
        previous_cgpa: latest.previous_cgpa ?? student?.cumulative_gpa ?? 0,
        mid_1: latest.mid_1 ?? 0,
        mid_2: latest.mid_2 ?? 0,
        internal_marks: latest.internal_marks ?? 0,
        backlogs: latest.backlogs ?? 0,
        department_code: student?.department_code ?? undefined,
        semester: latest.semester,
      });
    }
  }, [latest, student, form]);

  const predict = useAsync(
    () => (form ? predictionApi.predictCgpa(form) : Promise.reject(new Error('FORM_INCOMPLETE'))),
    [form]
  );

  const setField = (key: keyof CGPAPredictionRequest, value: string) => {
    setFormError(null);
    setForm((prev) => {
      if (!prev) return prev;
      const num = parseFloat(value);
      const isConstrainable = key in FIELD_LIMITS;
      const limits = isConstrainable ? FIELD_LIMITS[key as NumFieldKeys] : null;
      if (Number.isNaN(num)) return prev;
      if (limits && value !== '' && (num < limits.min || num > limits.max)) {
        setFormError(`${limits.label} must be between ${limits.min} and ${limits.max}.`);
        return prev;
      }
      return { ...prev, [key]: num };
    });
  };

  if (loading) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="PREDICT CGPA · PHASE 3" title="Loading…" />
        <LoadingPanel />
      </div>
    );
  }

  if (studentError) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="PREDICT CGPA · PHASE 3" title="Profile unavailable" />
        <Alert variant="error">{studentError}</Alert>
        <Button onClick={refresh} style={{ marginTop: '0.8rem' }}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="app-page">
      <AppPageHeader
        eyebrow="PREDICT CGPA · PHASE 3"
        title="SEMESTER CGPA PREDICTION"
        description="Inputs are computed server-side by the trained regressor. Adjust any field to run a what-if — results are always real model output."
        actions={latest && (
          <span className="mono-label">BASELINE: SEMESTER {latest.semester}</span>
        )}
      />

      <div className="predict-layout">
        {/* Inputs */}
        <section className="panel dash-panel">
          <div className="panel-head">
            <span className="mono-label">ACADEMIC INPUTS</span>
          </div>
          {!latest ? (
            <EmptyState title="NO VERIFIED SEMESTER" body="A complete record is required to seed the prediction." />
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!form) return;
                const outOfRange = (Object.keys(FIELD_LIMITS) as Array<keyof typeof FIELD_LIMITS>).some((k) => {
                  const limits = FIELD_LIMITS[k];
                  const v = form[k];
                  return typeof v === 'number' && (v < limits.min || v > limits.max);
                });
                if (outOfRange) {
                  setFormError('One or more inputs are out of range.');
                  return;
                }
                setFormError(null);
                predict.run();
              }}
              className="form-grid"
            >
              {Object.entries(FIELD_LIMITS).map(([key, limits]) => {
                const k = key as keyof CGPAPredictionRequest;
                const num = form?.[k];
                const value = typeof num === 'number' ? String(num) : '0';
                return (
                  <Input
                    key={key}
                    label={limits.label}
                    type="number"
                    step={key === 'backlogs' ? '1' : 'any'}
                    value={value}
                    onChange={(e) => setField(k, e.target.value)}
                    required
                  />
                );
              })}

              {formError && <Alert variant="error">{formError}</Alert>}

              <div className="form-actions">
                <Button type="submit" loading={predict.loading}>
                  {predict.loading ? 'COMPUTING…' : 'COMPUTE CGPA'} <Calculator size={15} />
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setForm(null);
                    setFormError(null);
                    predict.reset();
                    if (latest) {
                      setForm({
                        attendance_percentage: latest.attendance_percentage,
                        previous_cgpa: latest.previous_cgpa ?? student?.cumulative_gpa ?? 0,
                        mid_1: latest.mid_1 ?? 0,
                        mid_2: latest.mid_2 ?? 0,
                        internal_marks: latest.internal_marks ?? 0,
                        backlogs: latest.backlogs ?? 0,
                        department_code: student?.department_code ?? undefined,
                        semester: latest.semester,
                      });
                    }
                  }}
                >
                  <RotateCcw size={14} /> RESET
                </Button>
              </div>
            </form>
          )}
        </section>

        {/* Result */}
        <section className="panel dash-panel">
          <div className="panel-head">
            <span className="mono-label">MODEL OUTPUT</span>
            {predict.data && (
              <span className="mono-label dim">
                {predict.data.model_name} v{predict.data.model_version}
              </span>
            )}
          </div>

          {predict.loading && <LoadingPanel message="Running the regressor…" />}
          {predict.error && !predict.data && <Alert variant="error">{predict.error}</Alert>}
          {!predict.data && !predict.loading && (
            <EmptyState
              title="AWAITING INPUT"
              body="Set your inputs and run the prediction. Results are generated by the backend only."
            />
          )}

          {predict.data && (
            <div className="result-area">
              <div className="result-hero">
                <span className="mono-label">PREDICTED SEMESTER CGPA</span>
                <span className="result-number">{predict.data.predicted_cgpa.toFixed(2)}</span>
                <span className="mono-label dim">{predict.data.prediction_context}</span>
              </div>

              <div className="metric-grid metric-grid--2">
                <MetricDisplay label="ACADEMIC AVERAGE" value={predict.data.feature_summary.academic_average.toFixed(1)} sub="/ 100" />
                <MetricDisplay label="ATTENDANCE RISK" value={predict.data.feature_summary.attendance_risk_category} sub={`score ${predict.data.feature_summary.attendance_risk_score.toFixed(0)}`} accent={predict.data.feature_summary.attendance_risk_category !== 'LOW' ? 'var(--risk-medium)' : undefined} />
                <MetricDisplay label="MID + INTERNAL AVG" value={predict.data.feature_summary.mid_term_average.toFixed(0)} sub={`internal ${predict.data.feature_summary.internal_average.toFixed(0)}`} />
                <MetricDisplay label="STABILITY" value={predict.data.feature_summary.academic_stability.toFixed(1)} sub="consistency index" />
              </div>

              {predict.data.top_feature_contributions && (
                <details className="top-contrib" aria-label="Top feature contributions">
                  <summary style={{ fontSize: '0.72rem', color: 'var(--text-muted)', cursor: 'pointer', fontFamily: 'var(--font-mono)' }}>
                    VIEW TOP FEATURE CONTRIBUTIONS
                  </summary>
                  <div className="xai-cards" style={{ marginTop: '0.6rem' }}>
                    {Object.entries(predict.data.top_feature_contributions)
                      .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                      .slice(0, 6)
                      .map(([name, shap]) => (
                        <div key={name} className="xai-card">
                          <span className="mono-label">{name.replace(/_/g, ' ').toUpperCase()}</span>
                          <span className="mono-label" style={{ color: shap >= 0 ? 'var(--color-primary)' : 'var(--risk-high)' }}>
                            {shap >= 0 ? '+' : ''}{shap.toFixed(3)}
                          </span>
                        </div>
                      ))}
                  </div>
                </details>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};