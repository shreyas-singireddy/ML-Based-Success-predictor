import React, { useEffect, useMemo } from 'react';
import { AppPageHeader } from '../../components/layout/AppPageHeader';
import { CGPATrendChart, TrendPoint } from '../../components/dashboard/CGPATrendChart';
import { LoadingPanel } from '../../components/ui/Skeleton';
import { ErrorState } from '../../components/ui/ErrorState';
import { EmptyState } from '../../components/ui/EmptyState';
import { useStudentData } from '../../contexts/StudentDataContext';
import { buildPredictionPayload } from '../../lib/prediction';
import { predictionApi } from '../../services/predictionApi';
import { useAsync } from '../../hooks/useAsync';

export const PerformancePage: React.FC = () => {
  const { student, loading, error, refresh } = useStudentData();
  const payload = useMemo(() => buildPredictionPayload(student), [student]);

  const cgpa = useAsync(
    () => payload?.cgpa ? predictionApi.predictCgpa(payload.cgpa) : Promise.reject(new Error('NO_DATA')),
    [payload]
  );

  useEffect(() => {
    if (payload) cgpa.run();
  }, [payload]);

  if (loading) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="ACADEMIC PERFORMANCE" title="Loading records…" />
        <LoadingPanel />
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="ACADEMIC PERFORMANCE" title="Records unavailable" />
        <ErrorState title="COULD NOT LOAD RECORDS" message={error} onRetry={refresh} />
      </div>
    );
  }

  if (!student) {
    return (
      <div className="app-page">
        <AppPageHeader eyebrow="ACADEMIC PERFORMANCE" title="No profile linked" />
        <EmptyState title="NO STUDENT PROFILE" />
      </div>
    );
  }

  const records = useMemo(
    () => (student.academic_records ?? []).slice().sort((a, b) => a.semester - b.semester),
    [student]
  );

  const trendData: TrendPoint[] = records.map((r) => ({
    semester: r.semester,
    label: `S${r.semester}`,
    value: r.semester_cgpa ?? null,
  }));

  if (cgpa.data) {
    const lastSem = records[records.length - 1]?.semester ?? 0;
    trendData.push({
      semester: lastSem + 1,
      label: `S${lastSem + 1}`,
      value: cgpa.data.predicted_cgpa,
      predicted: true,
    });
  }

  return (
    <div className="app-page">
      <AppPageHeader
        eyebrow="ACADEMIC PERFORMANCE"
        title="YOUR CGPA HISTORY"
        description="Recorded semester performance with the next prediction overlaid."
      />

      {/* Trend */}
      <section className="panel dash-panel">
        <div className="panel-head">
          <span className="mono-label">CGPA BY SEMESTER</span>
          <span className="ggplot-status"><span className="dot" /> SOLID = ACTUAL · DASHED = PREDICTED</span>
        </div>
        {cgpa.loading && !trendData.length ? (
          <LoadingPanel message="Building trend…" />
        ) : trendData.length === 0 ? (
          <EmptyState title="NO RECORDS" />
        ) : (
          <CGPATrendChart data={trendData} />
        )}
      </section>

      {/* Semester table */}
      <section className="panel dash-panel">
        <div className="panel-head">
          <span className="mono-label">SEMESTER BREAKDOWN</span>
        </div>
        {records.length === 0 ? (
          <EmptyState title="NO SEMESTER RECORDS" body="Academic records will appear here once recorded by your institution." />
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>SEM</th>
                  <th>CGPA</th>
                  <th>GRADE</th>
                  <th>ATTENDANCE</th>
                  <th>MID 1 / MID 2</th>
                  <th>INTERNAL</th>
                  <th>BACKLOGS</th>
                  <th>RISK TREND</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td>S{r.semester}</td>
                    <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                      {r.semester_cgpa != null ? r.semester_cgpa.toFixed(2) : '—'}
                    </td>
                    <td>{r.grade ?? '—'}</td>
                    <td>{r.attendance_percentage.toFixed(0)}%</td>
                    <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                      {r.mid_1 ?? '—'} / {r.mid_2 ?? '—'}
                    </td>
                    <td>{r.internal_marks ?? '—'}</td>
                    <td>{r.backlogs ?? 0}</td>
                    <td>
                      {r.historical_risk_level ? (
                        <span className={`risk-badge risk-badge--${r.historical_risk_level.toLowerCase()}`}>
                          <span className="dot" /> {r.historical_risk_level}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};