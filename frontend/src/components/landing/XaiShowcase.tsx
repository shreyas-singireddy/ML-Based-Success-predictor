import React from 'react';
import { AnimatedSection } from './AnimatedSection';
import type { FeatureContribution } from '../../types';

/** Demo cards assert the explainability promise. Labeled as illustrative. */
const DEMO_FACTORS: FeatureContribution[] = [
  {
    feature_name: 'attendance_percentage',
    display_name: 'Attendance',
    original_value: 84,
    unit: '%',
    shap_value: 0.34,
    contribution_direction: 'positive',
    impact_level: 'HIGH',
    is_demographic: false,
    student_explanation: 'Your attendance is above threshold, adding to your predicted GPA.',
  },
  {
    feature_name: 'backlogs',
    display_name: 'Backlogs',
    original_value: 2,
    unit: 'count',
    shap_value: -0.42,
    contribution_direction: 'negative',
    impact_level: 'HIGH',
    is_demographic: false,
    student_explanation: 'Open backlogs are the single largest drag on your predicted CGPA.',
  },
  {
    feature_name: 'mid_2',
    display_name: 'Mid-term 2',
    original_value: 71,
    unit: 'marks',
    shap_value: 0.11,
    contribution_direction: 'positive',
    impact_level: 'MEDIUM',
    is_demographic: false,
    student_explanation: 'Mid-2 marks support your current trajectory.',
  },
];

export const XaiShowcase: React.FC = () => {
  return (
    <AnimatedSection id="features" className="feature-section">
      <div className="section-label" style={{ textAlign: 'center' }}>
        <span className="mono-label">DEMO // EXPLAINABILITY</span>
        <h2>WHY LITERALLY THAT NUMBER?</h2>
      </div>

      <div className="xai-cards">
        {DEMO_FACTORS.map((f) => {
          const positive = f.contribution_direction === 'positive';
          const color = positive ? 'var(--color-primary)' : 'var(--risk-high)';
          return (
            <div key={f.feature_name} className="xai-card">
              <span className="xai-card-head">
                <span className={`xai-sign ${positive ? 'pos' : 'neg'}`}>
                  {positive ? '+' : '−'}
                </span>
                <span className="mono-label">{f.display_name} — {f.impact_level}</span>
              </span>
              <span className="xai-explanation" style={{ borderLeft: `2px solid ${color}`, paddingLeft: '0.6rem' }}>
                “{f.student_explanation}”
              </span>
              <span className="xai-value mono-label">{f.original_value}{f.unit}</span>
            </div>
          );
        })}
      </div>

      <div className="feature-note">
        <span className="mono-label">HUMAN-READABLE</span>
        <p>
          Every factor is explained in plain language over your actual values — balanced against a
          fairness audit on demographic features.
        </p>
      </div>
    </AnimatedSection>
  );
};