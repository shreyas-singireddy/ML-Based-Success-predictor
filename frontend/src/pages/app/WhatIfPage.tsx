import React, { useEffect, useMemo, useState } from 'react';
import {
  SlidersHorizontal,
  RotateCcw,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  Minus,
  Plus,
  Loader2,
} from 'lucide-react';
import { AppPageHeader } from '../../components/layout/AppPageHeader';
import { Alert } from '../../components/ui/Alert';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { MetricDisplay } from '../../components/dashboard/MetricDisplay';
import { LoadingPanel } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { useStudentData } from '../../contexts/StudentDataContext';
import { getLatestRecord, buildPredictionPayload } from '../../lib/prediction';
import { whatIfApi } from '../../services/whatIfApi';
import { useAsync } from '../../hooks/useAsync';
import { riskColor } from '../../lib/risk';
import type {
  WhatIfSimulationRequest,
  WhatIfHypotheticalInputs,
  CGPAPredictionRequest,
  WhatIfSimulationResponse,
} from '../../types';

const SIMULATABLE_FIELDS: Array<{
  key: keyof WhatIfHypotheticalInputs;
  label: string;
  min: number;
  max: number;
  step: number | 'any';
  unit: string;
  displayName: string;
}> = [
  { key: 'attendance_percentage', label: 'Attendance %', min: 0, max: 100, step: 'any', unit: '%', displayName: 'Attendance' },
  { key: 'mid_1', label: 'Mid-Term 1', min: 0, max: 100, step: 'any', unit: 'marks', displayName: 'Mid-Term 1' },
  { key: 'mid_2', label: 'Mid-Term 2', min: 0, max: 100, step: 'any', unit: 'marks', displayName: 'Mid-Term 2' },
  { key: 'internal_marks', label: 'Internal Marks', min: 0, max: 100, step: 'any', unit: 'marks', displayName: 'Internal Marks' },
  { key: 'backlogs', label: 'Backlogs', min: 0, max: 50, step: 1, unit: 'count', displayName: 'Backlogs' },
  { key: 'previous_cgpa', label: 'Previous CGPA', min: 0, max: 10, step: 'any', unit: '/10', displayName: 'Previous CGPA' },
];

const PRESET_SCENARIOS: Array<{
  id: string;
  label: string;
  description: string;
  overrides: Partial<WhatIfHypotheticalInputs>;
}> = [
  {
    id: 'improve_attendance',
    label: 'Improve Attendance',
    description: 'Simulate 85% attendance',
    overrides: { attendance_percentage: 85 },
  },
  {
    id: 'improve_midterms',
    label: 'Improve Mid-Terms',
    description: 'Simulate 80+ on both mid-terms',
    overrides: { mid_1: 80, mid_2: 80 },
  },
  {
    id: 'improve_internals',
    label: 'Improve Internals',
    description: 'Simulate 85 internal marks',
    overrides: { internal_marks: 85 },
  },
  {
    id: 'clear_backlogs',
    label: 'Clear Backlogs',
    description: 'Simulate zero backlogs',
    overrides: { backlogs: 0 },
  },
  {
    id: 'comprehensive',
    label: 'Comprehensive Improvement',
    description: 'Attendance 85%, Mid-terms 80, Internals 85, No backlogs',
    overrides: { attendance_percentage: 85, mid_1: 80, mid_2: 80, internal_marks: 85, backlogs: 0 },
  },
];

export const WhatIfPage: React.FC = () => {
  const { student, loading, error: studentError, refresh } = useStudentData();
  const latest = useMemo(() => (student ? getLatestRecord(student) : null), [student]);
  const payload = useMemo(() => buildPredictionPayload(student), [student]);

  const [hypotheticalInputs, setHypotheticalInputs] = useState<WhatIfHypotheticalInputs>({});
  const [formError, setFormError] = useState<string | null>(null);

  const simulation = useAsync(
    () => {
      if (!payload?.cgpa) {
        return Promise.reject(new Error('NO_BASELINE_DATA'));
      }
      const request: WhatIfSimulationRequest = {
        student_number: payload.cgpa.student_number,
        semester: payload.cgpa.semester,
        hypothetical_inputs: hypotheticalInputs,
      };
      return whatIfApi.runSimulation(request);
    },
    [hypotheticalInputs, payload]
  );

  // Initialize hypothetical inputs from latest record when student loads
  useEffect(() => {
    if (latest && Object.keys(hypotheticalInputs).length === 0) {
      setHypotheticalInputs({
        attendance_percentage: latest.attendance_percentage,
        mid_1: latest.mid_1 ?? 0,
        mid_2: latest.mid_2 ?? 0,
        internal_marks: latest.internal_marks ?? 0,
        backlogs: latest.backlogs ?? 0,
        previous_cgpa: latest.previous_cgpa ?? student?.cumulative_gpa ?? 0,
      });
    }
  }, [latest, student, hypotheticalInputs]);

  const getBaselineValue = (key: keyof WhatIfHypotheticalInputs): number => {
    if (!latest) return 0;
    const fieldMap: Record<keyof WhatIfHypotheticalInputs, number | null> = {
      attendance_percentage: latest.attendance_percentage,
      mid_1: latest.mid_1 ?? 0,
      mid_2: latest.mid_2 ?? 0,
      internal_marks: latest.internal_marks ?? 0,
      backlogs: latest.backlogs ?? 0,
      previous_cgpa: latest.previous_cgpa ?? student?.cumulative_gpa ?? 0,
    };
    return fieldMap[key] ?? 0;
  };

  const handleInputChange = (key: keyof WhatIfHypotheticalInputs, value: string) => {
    setFormError(null);
    const num = parseFloat(value);
    if (Number.isNaN(num)) return;
    const limits = SIMULATABLE_FIELDS.find((f) => f.key === key);
    if (limits && (num < limits.min || num > limits.max)) {
      setFormError(`${limits.label} must be between ${limits.min} and ${limits.max}.`);
      return;
    }
    setHypotheticalInputs((prev) => ({ ...prev, [key]: num }));
  };

  const applyPreset = (preset: typeof PRESET_SCENARIOS[0]) => {
    setHypotheticalInputs((prev) => ({ ...prev, ...preset.overrides }));
  };

  const handleReset = () => {
    if (latest) {
      setHypotheticalInputs({
        attendance_percentage: latest.attendance_percentage,
        mid_1: latest.mid_1 ?? 0,
        mid_2: latest.mid_2 ?? 0,
        internal_marks: latest.internal_marks ?? 0,
        backlogs: latest.backlogs ?? 0,
        previous_cgpa: latest.previous_cgpa ?? student?.cumulative_gpa ?? 0,
      });
    }
    simulation.reset();
    setFormError(null);
  };

  const hasChanges = SIMULATABLE_FIELDS.some(
    (f) => hypotheticalInputs[f.key] !== getBaselineValue(f.key)
  );

  if (loading) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="WHAT-IF SIMULATOR · PHASE 7" title="Loading…" />
        <LoadingPanel />
      </div>
    );
  }

  if (studentError) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="WHAT-IF SIMULATOR · PHASE 7" title="Profile unavailable" />
        <Alert variant="error">{studentError}</Alert>
        <Button onClick={refresh} style={{ marginTop: '0.8rem' }}>Retry</Button>
      </div>
    );
  }

  if (!latest) {
    return (
      <div className="app-page">
        <AppPageHeader
          eyebrow="WHAT-IF SIMULATOR · PHASE 7"
          title="NO VERIFIED SEMESTER"
          description="A complete academic record is required to run simulations."
        />
        <EmptyState title="NO BASELINE DATA" body="Add a verified semester record to enable what-if analysis." />
      </div>
    );
  }

  const sim = simulation.data as WhatIfSimulationResponse | undefined;

  return (
    <div className="app-page">
      <AppPageHeader
        eyebrow="WHAT-IF SIMULATOR · PHASE 7"
        title="ACADEMIC SCENARIO SIMULATION"
        description="Adjust academic factors to explore hypothetical outcomes. Powered by production ML models — no fake data."
      />

      <div className="what-if-layout">
        {/* Left Column: Controls + Baseline */}
        <section className="panel dash-panel" style={{ flex: '1', minWidth: 320 }}>
          <div className="panel-head">
            <span className="mono-label">BASELINE ACADEMIC STATE</span>
          </div>

          <div className="baseline-grid" style={{ marginBottom: '1.5rem' }}>
            {SIMULATABLE_FIELDS.map((field) => {
              const baselineVal = getBaselineValue(field.key);
              const hypotheticalVal = hypotheticalInputs[field.key] ?? baselineVal;
              const hasChanged = hypotheticalVal !== baselineVal;
              return (
                <div key={field.key} className="baseline-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{field.label}</span>
                    {hasChanged && (
                      <span className="mono-label" style={{ fontSize: '0.65rem', color: 'var(--color-primary)', background: 'rgba(99,102,241,0.1)', padding: '1px 6px', borderRadius: 'var(--radius-sm)' }}>
                        MODIFIED
                      </span>
                    )}
                  </div>
                  <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.15rem' }}>
                    <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {typeof baselineVal === 'number' && baselineVal % 1 !== 0 ? baselineVal.toFixed(1) : baselineVal} {field.unit}
                    </span>
                    {hasChanged && (
                      <span className="mono-label" style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                        was {typeof baselineVal === 'number' && baselineVal % 1 !== 0 ? baselineVal.toFixed(1) : baselineVal}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="panel-head" style={{ marginTop: '1.5rem', marginBottom: '0.5rem' }}>
            <span className="mono-label">HYPOTHETICAL ADJUSTMENTS</span>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <span className="mono-label" style={{ fontSize: '0.7rem', display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>QUICK SCENARIOS</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {PRESET_SCENARIOS.map((preset) => (
                <Button
                  key={preset.id}
                  variant="ghost"
                  size="sm"
                  onClick={() => applyPreset(preset)}
                  disabled={simulation.loading}
                  title={preset.description}
                  style={{ fontSize: '0.65rem', padding: '0.4rem 0.75rem' }}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!hasChanges) return;
              simulation.run();
            }}
            className="form-grid"
            style={{ marginBottom: '1rem' }}
          >
            {SIMULATABLE_FIELDS.map((field) => {
              const baselineVal = getBaselineValue(field.key);
              const currentVal = hypotheticalInputs[field.key] ?? baselineVal;
              return (
                <div key={field.key} className="control-row" style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {field.label}
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Input
                      type="number"
                      min={field.min}
                      max={field.max}
                      step={field.step}
                      value={String(currentVal)}
                      onChange={(e) => handleInputChange(field.key, e.target.value)}
                      style={{ width: '80px', fontSize: '0.95rem', fontWeight: 700, textAlign: 'center' }}
                      aria-label={`${field.label} (baseline: ${baselineVal} ${field.unit})`}
                    />
                    <span className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', minWidth: '45px' }}>
                      {field.unit}
                    </span>
                    <input
                      type="range"
                      min={field.min}
                      max={field.max}
                      step={field.step === 'any' ? '0.1' : String(field.step)}
                      value={currentVal}
                      onChange={(e) => handleInputChange(field.key, e.target.value)}
                      style={{ flex: 1, accentColor: 'var(--color-primary)' }}
                      aria-label={`${field.label} slider`}
                    />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                    <span>{field.min}{field.unit}</span>
                    <span>{field.max}{field.unit}</span>
                  </div>
                </div>
              );
            })}

            {formError && <Alert variant="error" style={{ gridColumn: '1 / -1' }}>{formError}</Alert>}

            <div className="form-actions" style={{ gridColumn: '1 / -1', display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
              <Button
                type="submit"
                loading={simulation.loading}
                disabled={!hasChanges || simulation.loading}
                style={{ flex: 1 }}
              >
                {simulation.loading ? (
                  <>
                    <Loader2 size={15} className="animate-spin" /> RUNNING SIMULATION…
                  </>
                ) : (
                  <>
                    <SlidersHorizontal size={15} /> RUN SIMULATION
                  </>
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={handleReset}
                disabled={simulation.loading}
              >
                <RotateCcw size={14} /> RESET TO BASELINE
              </Button>
            </div>
          </form>

          {!hasChanges && !simulation.data && !simulation.loading && (
            <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', border: '1px dashed var(--border-subtle)' }}>
              <SlidersHorizontal size={28} style={{ marginBottom: '0.5rem', opacity: 0.5 }} />
              <p style={{ fontWeight: 600 }}>No changes from baseline</p>
              <p style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>Adjust sliders above to create a hypothetical scenario, then run the simulation.</p>
            </div>
          )}
        </section>

        {/* Right Column: Results + Comparison */}
        <section className="panel dash-panel" style={{ flex: '1', minWidth: 320 }}>
          <div className="panel-head">
            <span className="mono-label">SIMULATION OUTPUT</span>
            {sim && (
              <span className="mono-label dim">
                {sim.model_name} v{sim.model_version} · Risk: {sim.risk_model_name} v{sim.risk_model_version}
              </span>
            )}
          </div>

          {simulation.loading && <LoadingPanel message="Running regressor & risk engine…" />}
          {simulation.error && !simulation.data && <Alert variant="error">{simulation.error}</Alert>}
          {!simulation.data && !simulation.loading && !simulation.error && (
            <EmptyState title="AWAITING SIMULATION" body="Adjust inputs and run the simulator to see projected outcomes." />
          )}

          {sim && (
            <div className="simulation-results">
              {/* Main Result Hero */}
              <div className="result-hero" style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <span className="mono-label" style={{ alignSelf: 'flex-start' }}>PREDICTED CGPA</span>
                  <span className="result-number" style={{ fontSize: '3.5rem', fontWeight: 800, color: 'var(--color-primary)', lineHeight: 1 }}>
                    {sim.simulation.predicted_cgpa.toFixed(2)}
                  </span>
                  <span className="mono-label dim" style={{ alignSelf: 'flex-end', marginBottom: '0.5rem' }}>
                    {sim.delta.cgpa_delta >= 0 ? '+' : ''}{sim.delta.cgpa_delta.toFixed(2)} from baseline
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginTop: '0.75rem', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="node-status-chip" style={{ background: riskColor(sim.simulation.risk_level), color: 'var(--bg-primary)' }}>
                      {sim.simulation.risk_level}
                    </span>
                    <span className="mono-label">RISK LEVEL</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ color: riskColor(sim.simulation.performance_category) }}>
                      {sim.simulation.performance_category}
                    </span>
                    <span className="mono-label">PERFORMANCE</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="mono-label">GRADE</span>
                    <span style={{ fontWeight: 700, color: 'var(--color-success)' }}>{sim.simulation.grade}</span>
                  </div>
                </div>

                <div style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span className="mono-label">Risk Score: </span>
                  <span style={{ fontWeight: 600 }}>{sim.simulation.risk_score.toFixed(1)} / 100</span>
                  <span className="mono-label" style={{ marginLeft: '1rem' }}>Context: {sim.simulation.academic_state.semester} · {sim.baseline.academic_state.department_code}</span>
                </div>
              </div>

              {/* Comparison Table */}
              <div style={{ marginBottom: '1.5rem' }}>
                <span className="mono-label" style={{ display: 'block', marginBottom: '0.5rem' }}>COMPARISON: BASELINE vs SIMULATED</span>
                <div className="comparison-table" style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid var(--border-subtle)' }}>
                        <th style={{ textAlign: 'left', padding: '0.5rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.65rem' }}>METRIC</th>
                        <th style={{ textAlign: 'right', padding: '0.5rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.65rem' }}>CURRENT</th>
                        <th style={{ textAlign: 'right', padding: '0.5rem', color: 'var(--color-primary)', fontWeight: 600, fontSize: '0.65rem' }}>SIMULATED</th>
                        <th style={{ textAlign: 'right', padding: '0.5rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.65rem' }}>DELTA</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '0.5rem', fontWeight: 600 }}>Predicted CGPA</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem' }}>{sim.baseline.predicted_cgpa.toFixed(2)}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', fontWeight: 700, color: 'var(--color-primary)' }}>{sim.simulation.predicted_cgpa.toFixed(2)}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', fontWeight: 700, color: sim.delta.cgpa_delta >= 0 ? 'var(--color-success)' : 'var(--risk-high)' }}>
                          {sim.delta.cgpa_delta >= 0 ? '+' : ''}{sim.delta.cgpa_delta.toFixed(2)}
                          <span className="mono-label" style={{ fontSize: '0.6rem', marginLeft: '0.25rem', color: sim.delta.cgpa_delta >= 0 ? 'var(--color-success)' : 'var(--risk-high)' }}>
                            {sim.delta.cgpa_trend}
                          </span>
                        </td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '0.5rem', fontWeight: 600 }}>Risk Level</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem' }}>
                          <span className="node-status-chip" style={{ background: riskColor(sim.baseline.risk_level), color: 'var(--bg-primary)', fontSize: '0.7rem' }}>
                            {sim.baseline.risk_level}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right', padding: '0.5rem' }}>
                          <span className="node-status-chip" style={{ background: riskColor(sim.simulation.risk_level), color: 'var(--bg-primary)', fontSize: '0.7rem' }}>
                            {sim.simulation.risk_level}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', fontWeight: 700 }}>
                          {sim.delta.risk_transition}
                          <span className="mono-label" style={{ fontSize: '0.6rem', marginLeft: '0.25rem', color: riskColor(sim.simulation.risk_level) }}>
                            {sim.delta.risk_trend}
                          </span>
                        </td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '0.5rem', fontWeight: 600 }}>Risk Score</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem' }}>{sim.baseline.risk_score.toFixed(1)}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', fontWeight: 700, color: 'var(--color-primary)' }}>{sim.simulation.risk_score.toFixed(1)}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', fontWeight: 700, color: sim.delta.risk_score_delta <= 0 ? 'var(--color-success)' : 'var(--risk-high)' }}>
                          {sim.delta.risk_score_delta >= 0 ? '+' : ''}{sim.delta.risk_score_delta.toFixed(1)}
                        </td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '0.5rem', fontWeight: 600 }}>Performance Category</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem' }}>{sim.baseline.performance_category}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', fontWeight: 700, color: 'var(--color-primary)' }}>{sim.simulation.performance_category}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', fontWeight: 700 }}>
                          {sim.delta.performance_category_transition}
                        </td>
                      </tr>
                      {sim.delta.modified_factors.map((factor) => (
                        <tr key={factor.factor} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '0.5rem', fontWeight: 600, color: 'var(--color-primary)' }}>{factor.display_name}</td>
                          <td style={{ textAlign: 'right', padding: '0.5rem' }}>
                            {typeof factor.baseline_value === 'number' && factor.baseline_value % 1 !== 0
                              ? factor.baseline_value.toFixed(1)
                              : factor.baseline_value}
                            {factor.unit}
                          </td>
                          <td style={{ textAlign: 'right', padding: '0.5rem', fontWeight: 700, color: 'var(--color-primary)' }}>
                            {typeof factor.simulated_value === 'number' && factor.simulated_value % 1 !== 0
                              ? factor.simulated_value.toFixed(1)
                              : factor.simulated_value}
                            {factor.unit}
                          </td>
                          <td style={{ textAlign: 'right', padding: '0.5rem', fontWeight: 700, color: factor.delta >= 0 ? 'var(--color-success)' : 'var(--risk-high)' }}>
                            {factor.delta >= 0 ? '+' : ''}{factor.delta.toFixed(1)}{factor.unit}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Delta Summary */}
              <div className="delta-summary" style={{ padding: '1rem', background: 'rgba(15, 23, 42, 0.4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <span className="mono-label" style={{ display: 'block', marginBottom: '0.5rem' }}>OVERALL IMPACT ASSESSMENT</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{
                      fontSize: '1.5rem',
                      fontWeight: 800,
                      color: sim.delta.overall_impact === 'IMPROVED' ? 'var(--color-success)' :
                             sim.delta.overall_impact === 'WORSENED' ? 'var(--risk-high)' : 'var(--text-muted)'
                    }}>
                      {sim.delta.overall_impact === 'IMPROVED' && <TrendingUp size={20} />}
                      {sim.delta.overall_impact === 'WORSENED' && <AlertTriangle size={20} />}
                      {sim.delta.overall_impact === 'UNCHANGED' && <Minus size={20} />}
                    </span>
                    <span className="mono-label" style={{
                      color: sim.delta.overall_impact === 'IMPROVED' ? 'var(--color-success)' :
                             sim.delta.overall_impact === 'WORSENED' ? 'var(--risk-high)' : 'var(--text-muted)',
                      fontSize: '0.85rem',
                      textTransform: 'uppercase'
                    }}>
                      {sim.delta.overall_impact}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', maxWidth: '400px' }}>
                    {sim.delta.overall_impact === 'IMPROVED' && 'The simulated improvements are projected to enhance your academic standing.'}
                    {sim.delta.overall_impact === 'WORSENED' && 'The simulated changes are projected to negatively impact your academic standing.'}
                    {sim.delta.overall_impact === 'UNCHANGED' && 'The simulated changes do not meaningfully alter the projected outcome.'}
                  </div>
                </div>

                <details style={{ marginTop: '0.75rem' }}>
                  <summary style={{ fontSize: '0.7rem', color: 'var(--text-muted)', cursor: 'pointer', fontFamily: 'var(--font-mono)' }}>
                    VIEW DISCLAIMER
                  </summary>
                  <p style={{ marginTop: '0.5rem', fontSize: '0.7rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {sim.disclaimer}
                  </p>
                </details>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};