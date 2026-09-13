import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import type { ExplanationData } from '../../types';

interface XaiPreviewProps {
  explanation: ExplanationData;
  task: 'cgpa' | 'risk';
  linkTo?: string;
}

/**
 * Concise "WHY THIS SCORE?" panel for the dashboard.
 * Uses real Phase 5 factors — never fabricated.
 */
export const XaiPreview: React.FC<XaiPreviewProps> = ({ explanation, task, linkTo = '/app/explainability' }) => {
  const factors = useMemo(
    () => (explanation?.top_factors ?? []).slice(0, 4),
    [explanation]
  );

  if (!explanation?.explanation_available) {
    return (
      <div className="state-panel" style={{ padding: '1.5rem' }}>
        <div className="state-title">EXPLANATION UNAVAILABLE</div>
        <div className="state-body">Explanation details are unavailable for this model type.</div>
      </div>
    );
  }

  const maxMag = Math.max(1, ...factors.map((f) => Math.abs(f.shap_value)));

  return (
    <div>
      <div className="mono-label" style={{ marginBottom: '0.75rem' }}>
        {task === 'cgpa' ? 'WHY THIS SCORE?' : 'WHY IS MY RISK THIS LEVEL?'}
      </div>

      {factors.length === 0 ? (
        <div className="state-body">No factor data available for this explanation.</div>
      ) : (
        <div>
          {factors.map((factor) => {
            const positive = factor.contribution_direction === 'positive';
            const color = positive ? 'var(--color-primary)' : 'var(--risk-high)';
            const pct = (Math.abs(factor.shap_value) / maxMag) * 100;
            return (
              <div key={factor.feature_name} className="factor-row">
                <div className="factor-name" title={factor.student_explanation}>
                  {factor.display_name}
                </div>
                <div className="factor-track">
                  <span style={{ width: `${pct}%`, background: color }} />
                </div>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontFamily: 'var(--font-mono)',
                    color,
                    minWidth: 48,
                    textAlign: 'right',
                    textTransform: 'uppercase',
                  }}
                >
                  {factor.impact_level.toLowerCase()} / {positive ? 'boost' : 'drag'}
                </span>
              </div>
            );
          })}
        </div>
      )}

      <Link
        to={linkTo}
        className="btn btn-outline btn-sm"
        style={{ marginTop: '1rem' }}
      >
        VIEW FULL ANALYSIS <ArrowRight size={14} />
      </Link>
    </div>
  );
};