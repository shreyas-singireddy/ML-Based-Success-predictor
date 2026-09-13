import React, { useEffect, useMemo, useState } from 'react';
import { ShieldAlert, RotateCcw } from 'lucide-react';
import { AppPageHeader } from '../../components/layout/AppPageHeader';
import { Alert } from '../../components/ui/Alert';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { RiskGauge } from '../../components/dashboard/RiskGauge';
import { LoadingPanel } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { useStudentData } from '../../contexts/StudentDataContext';
import { getLatestRecord } from '../../lib/prediction';
import { predictionApi } from '../../services/predictionApi';
import { useAsync } from '../../hooks/useAsync';
import { riskColor } from '../../lib/risk';
import type { RiskPredictionRequest } from '../../types';

export const RiskPage: React.FC = () => {
  const { student, loading, error: studentError, refresh } = useStudentData();
  const latest = useMemo(() => (student ? getLatestRecord(student) : null), [student]);

  const [form, setForm] = useState<RiskPredictionRequest | null>(null);

  useEffect(() => {
    if (latest && !form) {
      setForm({
        gender: student?.gender,
        age: student?.age,
        department_code: student?.department_code ?? undefined,
        semester: latest.semester,
        attendance_percentage: latest.attendance_percentage,
        previous_cgpa: latest.previous_cgpa ?? student?.cumulative_gpa ?? 0,
        mid_1: latest.mid_1 ?? 0,
        mid_2: latest.mid_2 ?? 0,
        internal_marks: latest.internal_marks ?? 0,
        backlogs: latest.backlogs ?? 0,
      });
    }
  }, [latest, student, form]);

  const risk = useAsync(
    () => (form ? predictionApi.predictRisk(form) : Promise.reject(new Error('FORM_INCOMPLETE'))),
    [form]
  );

  const setNum = (key: keyof RiskPredictionRequest, value: string) => {
    setForm((prev) => {
      if (!prev) return prev;
      const num = parseFloat(value);
      if (Number.isNaN(num)) return prev;
      return { ...prev, [key]: num };
    });
  };

  if (loading) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="ACADEMIC RISK · PHASE 4" title="Loading…" />
        <LoadingPanel />
      </div>
    );
  }

  if (studentError) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="ACADEMIC RISK · PHASE 4" title="Profile unavailable" />
        <Alert variant="error">{studentError}</Alert>
        <Button onClick={refresh} style={{ marginTop: '0.8rem' }}>Retry</Button>
      </div>
    );
  }

  const riskCount = risk.data
    ? Object.entries(risk.data.risk_probabilities).sort((a, b) => b[1] - a[1])
    : [];

  return (
    <div className="app-page">
      <AppPageHeader
        eyebrow="ACADEMIC RISK · PHASE 4"
        title="RISK CLASSIFICATION"
        description="The risk engine scores academic standing from 0–100 across MINIMUM → CRITICAL, with attributed drivers."
      />

      <div className="predict-layout">
        <section className="panel dash-panel">
          <div className="panel-head"><span className="mono-label">RISK INPUTS</span></div>
          {!latest ? (
            <EmptyState title="NO VERIFIED SEMESTER" body="A complete record is required to run risk classification." />
          ) : (
            <form
              className="form-grid"
              onSubmit={(e) => { e.preventDefault(); risk.run(); }}
            >
              <Select
                label="Gender"
                value={form?.gender ?? ''}
                options={[
                  { value: 'MALE', label: 'MALE' },
                  { value: 'FEMALE', label: 'FEMALE' },
                  { value: 'OTHER', label: 'OTHER' },
                ]}
                onChange={(e) => setForm((prev) => prev ? { ...prev, gender: e.target.value } : prev)}
              />
              <Input label="Age" type="number" value={String(form?.age ?? '')} onChange={(e) => setNum('age', e.target.value)} />
              <Input label="Attendance %" type="number" min={0} max={100} step="any" value={String(form?.attendance_percentage ?? '')} onChange={(e) => setNum('attendance_percentage', e.target.value)} />
              <Input label="Previous CGPA" type="number" min={0} max={10} step="any" value={String(form?.previous_cgpa ?? '')} onChange={(e) => setNum('previous_cgpa', e.target.value)} />
              <Input label="Mid 1 Marks" type="number" min={0} max={100} step="any" value={String(form?.mid_1 ?? '')} onChange={(e) => setNum('mid_1', e.target.value)} />
              <Input label="Mid 2 Marks" type="number" min={0} max={100} step="any" value={String(form?.mid_2 ?? '')} onChange={(e) => setNum('mid_2', e.target.value)} />
              <Input label="Internal Marks" type="number" min={0} max={100} step="any" value={String(form?.internal_marks ?? '')} onChange={(e) => setNum('internal_marks', e.target.value)} />
              <Input label="Open Backlogs" type="number" min={0} max={50} step="1" value={String(form?.backlogs ?? '')} onChange={(e) => setNum('backlogs', e.target.value)} />

              {risk.error && !risk.data && <Alert variant="error">{risk.error}</Alert>}

              <div className="form-actions">
                <Button type="submit" loading={risk.loading}>
                  {risk.loading ? 'CLASSIFYING…' : 'EVALUATE RISK'} <ShieldAlert size={15} />
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    risk.reset();
                    setForm(null);
                    if (latest) {
                      setForm({
                        gender: student?.gender,
                        age: student?.age,
                        department_code: student?.department_code ?? undefined,
                        semester: latest.semester,
                        attendance_percentage: latest.attendance_percentage,
                        previous_cgpa: latest.previous_cgpa ?? student?.cumulative_gpa ?? 0,
                        mid_1: latest.mid_1 ?? 0,
                        mid_2: latest.mid_2 ?? 0,
                        internal_marks: latest.internal_marks ?? 0,
                        backlogs: latest.backlogs ?? 0,
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

        <section className="panel dash-panel">
          <div className="panel-head">
            <span className="mono-label">RISK OUTPUT</span>
            {risk.data && (
              <span className="mono-label dim">{risk.data.model_name} v{risk.data.model_version}</span>
            )}
          </div>

          {risk.loading && <LoadingPanel message="Evaluating risk profile…" />}
          {risk.error && !risk.data && <Alert variant="error">{risk.error}</Alert>}
          {!risk.data && !risk.loading && (
            <EmptyState title="AWAITING EVALUATION" body="Run the risk engine to see your classification." />
          )}

          {risk.data && (
            <div className="risk-output">
              <RiskGauge
                score={risk.data.risk_score}
                level={risk.data.risk_level}
                caption={`${risk.data.performance_category} · PREDICTED GPA ${risk.data.predicted_cgpa.toFixed(2)} · GRADE ${risk.data.grade}`}
              />

              <div className="prob-chips" role="group" aria-label="Risk probabilities by level">
                {riskCount.map(([level, prob]) => (
                  <div key={level} className="prob-chip" style={{ borderColor: riskColor(level) }}>
                    <span className="mono-label">{level}</span>
                    <span className={`dot`} style={{ background: riskColor(level) }} />
                    <span className="mono-label">{(prob * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>

              <div className="factor-list">
                <span className="mono-label" style={{ display: 'block', marginBottom: '0.4rem' }}>ATTRIBUTED DRIVERS</span>
                {risk.data.risk_factors.map((f) => (
                  <div key={f.factor} className="risk-factor-item">
                    <div className="risk-factor-head">
                      <span style={{ color: riskColor(f.level) }}>{f.factor.replace(/_/g, ' ').toUpperCase()}</span>
                      <span className="mono-label">{f.value}</span>
                      <span className={`node-status-chip ${f.level.toLowerCase()}`}>{f.level}</span>
                    </div>
                    <p className="risk-factor-detail">{f.detail}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};