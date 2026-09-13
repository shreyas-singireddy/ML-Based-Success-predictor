import React, { useEffect, useMemo } from 'react';
import { RefreshCw } from 'lucide-react';
import { AppPageHeader } from '../../components/layout/AppPageHeader';
import { MetricDisplay } from '../../components/dashboard/MetricDisplay';
import { CGPATrendChart, TrendPoint } from '../../components/dashboard/CGPATrendChart';
import { RiskGauge } from '../../components/dashboard/RiskGauge';
import { XaiPreview } from '../../components/dashboard/XaiPreview';
import { LoadingPanel } from '../../components/ui/Skeleton';
import { ErrorState } from '../../components/ui/ErrorState';
import { EmptyState } from '../../components/ui/EmptyState';
import { useStudentData } from '../../contexts/StudentDataContext';
import { buildPredictionPayload, getLatestRecord } from '../../lib/prediction';
import { predictionApi } from '../../services/predictionApi';
import { useAsync } from '../../hooks/useAsync';
import { riskColor } from '../../lib/risk';

export const DashboardPage: React.FC = () => {
  const { student, loading, error, refresh } = useStudentData();
  const payload = useMemo(() => buildPredictionPayload(student), [student]);

  const cgpa = useAsync(
    () => payload?.cgpa ? predictionApi.explainCgpa(payload.cgpa) : Promise.reject(new Error('NO_DATA')),
    [payload]
  );
  const risk = useAsync(
    () => payload?.risk ? predictionApi.predictRisk(payload.risk) : Promise.reject(new Error('NO_DATA')),
    [payload]
  );

  useEffect(() => {
    if (payload) {
      cgpa.run();
      risk.run();
    }
  }, [payload]);

  const latest = useMemo(() => getLatestRecord(student), [student]);

  if (loading) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="STUDENT OVERVIEW" title="Loading your academic profile…" />
        <LoadingPanel />
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="STUDENT OVERVIEW" title="Profile unavailable" />
        <ErrorState title="COULD NOT LOAD PROFILE" message={error} onRetry={refresh} />
      </div>
    );
  }

  if (!student) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="STUDENT OVERVIEW" title="No profile linked" />
        <EmptyState
          title="NO STUDENT PROFILE"
          body="Your user account has no associated student profile. Contact your institution."
        />
      </div>
    );
  }

  const trendData: TrendPoint[] = (student.academic_records ?? [])
    .slice()
    .sort((a, b) => a.semester - b.semester)
    .map((r) => ({
      semester: r.semester,
      label: `S${r.semester}`,
      value: r.semester_cgpa ?? null,
    }));

  if (cgpa.data && !trendData.some((d) => d.predicted)) {
    trendData.push({
      semester: (latest?.semester ?? 0) + 1,
      label: `S${(latest?.semester ?? 0) + 1}`,
      value: cgpa.data.predicted_cgpa,
      predicted: true,
    });
  }

  const backlogsTotal = (student.academic_records ?? []).reduce((s, r) => s + (r.backlogs ?? 0), 0);

  return (
    <div className="app-page">
      <AppPageHeader
        eyebrow={`STUDENT OVERVIEW // ${student.student_number}`}
        title={student.name.toUpperCase()}
        description={`${student.department_name ?? student.department_code ?? 'GENERAL'} · SEMESTER ${student.current_semester} · EST. ${student.enrollment_year}`}
        actions={
          <button className="btn btn-outline btn-sm" onClick={() => { refresh(); cgpa.run(); risk.run(); }}>
            <RefreshCw size={14} /> REFRESH
          </button>
        }
      />

      <div className="metric-grid">
        <MetricDisplay label="CURRENT CGPA" value={(student.cumulative_gpa ?? 0).toFixed(2)} sub="Cumulative performance" />
        <MetricDisplay
          label="LATEST SEMESTER"
          value={latest && latest.semester_cgpa != null ? latest.semester_cgpa.toFixed(2) : '—'}
          sub={latest ? `SEMESTER ${latest.semester}` : 'NO SEMESTER DATA'}
        />
        <MetricDisplay
          label="ATTENDANCE"
          value={latest ? `${latest.attendance_percentage.toFixed(0)}%` : '—'}
          sub="Latest semester"
          accent={latest && latest.attendance_percentage < 75 ? 'var(--risk-high)' : undefined}
        />
        <MetricDisplay
          label="OPEN BACKLOGS"
          value={backlogsTotal}
          sub="Across all semesters"
          accent={backlogsTotal > 0 ? 'var(--risk-high)' : undefined}
        />
      </div>

      <div className="dash-grid">
        <section className="panel dash-panel">
          <div className="panel-head">
            <span className="mono-label">CGPA TRAJECTORY</span>
            <span className="ggplot-status">
              <span className="dot" /> BACKEND VERIFIED
            </span>
          </div>
          {trendData.length === 0 ? (
            <EmptyState title="NO TREND" body="No semester results recorded for this student." />
          ) : (
            <CGPATrendChart data={trendData} />
          )}
        </section>

        <section className="panel dash-panel">
          <div className="panel-head">
            <span className="mono-label">ACADEMIC RISK</span>
            <span className="ggplot-status">
              <span className="dot" /> FROM SERVER
            </span>
          </div>
          {risk.loading && <LoadingPanel message="Evaluating risk…" />}
          {risk.error && !risk.data && (
            <ErrorState title={`RISK UNAVAILABLE`} message={risk.error} onRetry={() => risk.run()} />
          )}
          {risk.data && (
            <div className="risk-layout">
              <RiskGauge
                score={risk.data.risk_score}
                level={risk.data.risk_level}
                caption={`Predicted CGPA ${risk.data.predicted_cgpa.toFixed(2)} · ${risk.data.performance_category}`}
              />
              <RiskFactorsInline factors={risk.data.risk_factors} />
            </div>
          )}
          {!risk.data && !risk.loading && !risk.error && (
            <EmptyState title="RUN THE RISK ENGINE" body={!payload ? 'A complete verified semester record is required.' : 'Trigger a risk evaluation from the Academic Risk page.'} />
          )}
        </section>
      </div>

      <section className="panel dash-panel xai-strip">
        <div className="panel-head">
          <span className="mono-label">WHY THIS SCORE?</span>
          <span className="ggplot-status"><span className="dot" /> SHAP-ATTRIBUTED</span>
        </div>
        {cgpa.loading && <LoadingPanel message="Compiling explanation…" />}
        {cgpa.error && !cgpa.data && (
          <ErrorState title="EXPLANATION UNAVAILABLE" message={cgpa.error} onRetry={() => cgpa.run()} />
        )}
        {cgpa.data && <XaiPreview explanation={cgpa.data.explanation} task="cgpa" />}
        {!cgpa.data && !cgpa.loading && !cgpa.error && (
          <EmptyState title="NO EXPLANATION YET" body="Generate a prediction to see attributed factor explanations." />
        )}
      </section>
    </div>
  );
};

const RiskFactorsInline: React.FC<{ factors: Array<{ factor: string; level: string; value: number | string }> }> = ({ factors }) => {
  if (!factors?.length) return null;
  return (
    <div>
      <span className="mono-label" style={{ display: 'block', marginBottom: '0.5rem' }}>KEY DRIVERS</span>
      {factors.slice(0, 4).map((f) => (
        <div key={f.factor} className="inline-factor">
          <span style={{ color: riskColor(f.level) }}>{f.factor.toUpperCase().replace(/_/g, ' ')}</span>
          <span className="mono-label">{typeof f.value === 'number' && f.value % 1 === 0 ? f.value : f.value}</span>
        </div>
      ))}
    </div>
  );
};