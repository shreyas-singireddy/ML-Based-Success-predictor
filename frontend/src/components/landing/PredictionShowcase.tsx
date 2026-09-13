import React from 'react';
import { AnimatedSection } from './AnimatedSection';
import { CGPATrendChart, TrendPoint } from '../dashboard/CGPATrendChart';
import { MetricDisplay } from '../dashboard/MetricDisplay';

/**
 * Landing demo — real chart components fed ILLUSTRATIVE data. Honest labeling
 * is mandatory: this is not the signed-in user's record.
 */

const DEMO_TREND: TrendPoint[] = [
  { semester: 1, label: 'S1', value: 6.2 },
  { semester: 2, label: 'S2', value: 6.8 },
  { semester: 3, label: 'S3', value: 7.1 },
  { semester: 4, label: 'S4', value: 7.4 },
  { semester: 5, label: 'S5', value: 7.6, predicted: true },
];

const DEMO_METRICS = [
  { label: 'ATTENDANCE', value: '84%', sub: 'Latest semester' },
  { label: 'CURRENT GPA', value: '7.4', sub: 'Cumulative' },
  { label: 'PREDICTED GPA', value: '7.6', sub: 'Next semester', accent: 'var(--color-primary)' },
];

export const PredictionShowcase: React.FC = () => {
  return (
    <AnimatedSection id="predictions" className="feature-section">
      <div className="section-label" style={{ textAlign: 'center' }}>
        <span className="mono-label">DEMO // CGPA ENGINE</span>
        <h2>PREDICT YOUR TRAJECTORY</h2>
      </div>

      <div className="demo-visual">
        <span className="demo-tag">ILLUSTRATIVE DATA — NOT YOUR RECORDS</span>
        <div className="demo-metrics">
          {DEMO_METRICS.map((m) => (
            <MetricDisplay key={m.label} {...m} />
          ))}
        </div>
        <div className="demo-chart">
          <CGPATrendChart data={DEMO_TREND} height={230} />
        </div>
      </div>

      <div className="feature-note">
        <span className="mono-label">TRUTHFUL LABELING</span>
        <p>
          Trends show recorded semesters in solid line, the predicted CGPA in dashed line — with a
          data table below every chart. The signed-in dashboard plots your real, backend-verified
          records.
        </p>
      </div>
    </AnimatedSection>
  );
};