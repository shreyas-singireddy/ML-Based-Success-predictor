import React, { useEffect, useMemo } from 'react';
import { RefreshCw, Lightbulb, ArrowRight, Bot } from 'lucide-react';
import { Link } from 'react-router-dom';
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
import { recommendationApi } from '../../services/recommendationApi';
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
  const recs = useAsync(
    () => payload?.cgpa ? recommendationApi.generate(payload.cgpa) : Promise.reject(new Error('NO_DATA')),
    [payload]
  );

  useEffect(() => {
    if (payload) {
      cgpa.run();
      risk.run();
      recs.run();
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

      <div
        className="panel"
        style={{
          marginBottom: '1.25rem',
          padding: '1rem 1.25rem',
          background: 'linear-gradient(90deg, rgba(56, 189, 248, 0.1) 0%, var(--bg-panel) 100%)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.8rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', flex: 1, minWidth: '260px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'var(--color-info)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              flexShrink: 0,
            }}
          >
            <Bot size={18} />
          </div>
          <div>
            <div className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--color-info)', marginBottom: '0.25rem' }}>
              GENAI ACADEMIC ASSISTANT // GROUNDED ANSWERS
            </div>
            <div style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
              Ask anything about your CGPA, risk, what drives your score, or what-if scenarios.
            </div>
          </div>
        </div>

        <Link
          to="/app/assistant"
          className="btn btn-primary btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          ASK AI ASSISTANT <ArrowRight size={14} />
        </Link>
      </div>

      {recs.data && recs.data.recommendations.length > 0 && (
        <div
          className="panel"
          style={{
            marginBottom: '1.25rem',
            padding: '1rem 1.25rem',
            background: 'linear-gradient(90deg, rgba(99, 102, 241, 0.12) 0%, var(--bg-panel) 100%)',
            border: '1px solid rgba(99, 102, 241, 0.35)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '0.8rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', flex: 1, minWidth: '260px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'var(--color-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                flexShrink: 0,
              }}
            >
              <Lightbulb size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                <span className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--color-primary-hover)' }}>
                  PRIORITY 01 // {recs.data.recommendations[0].priority}
                </span>
                <span
                  style={{
                    fontSize: '0.7rem',
                    background: 'rgba(255, 255, 255, 0.06)',
                    padding: '0.1rem 0.4rem',
                    borderRadius: '3px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  {recs.data.recommendations[0].category.replace(/_/g, ' ')}
                </span>
              </div>
              <div style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                {recs.data.recommendations[0].title}
              </div>
            </div>
          </div>

          <Link
            to="/app/recommendations"
            className="btn btn-primary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            VIEW ACTION PLAN ({recs.data.recommendations.length}) <ArrowRight size={14} />
          </Link>
        </div>
      )}

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