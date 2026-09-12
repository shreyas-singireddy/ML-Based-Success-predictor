import React, { useState } from 'react';
import type {
  ExplanationData,
  FeatureContribution,
  ImpactLevel,
} from '../types';

// -----------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------

interface ExplanationPanelProps {
  explanation: ExplanationData;
  taskType: 'cgpa_regression' | 'risk_classification';
  predictedCGPA?: number;
  riskLevel?: string;
  riskScore?: number;
}

// -----------------------------------------------------------------------
// Constants
// -----------------------------------------------------------------------

const IMPACT_COLORS: Record<ImpactLevel, string> = {
  HIGH: '#ef4444',
  MEDIUM: '#f59e0b',
  LOW: '#6b7280',
};

const IMPACT_BG: Record<ImpactLevel, string> = {
  HIGH: 'rgba(239, 68, 68, 0.1)',
  MEDIUM: 'rgba(245, 158, 11, 0.1)',
  LOW: 'rgba(107, 114, 128, 0.08)',
};

const DIRECTION_COLORS = {
  positive: '#22c55e',
  negative: '#ef4444',
};

const DIRECTION_ICONS = {
  positive: '▲',
  negative: '▼',
};

const RISK_LEVEL_COLORS: Record<string, string> = {
  LOW: '#22c55e',
  MEDIUM: '#f59e0b',
  HIGH: '#ef4444',
  CRITICAL: '#7c3aed',
};

// -----------------------------------------------------------------------
// Sub-components
// -----------------------------------------------------------------------

function ImpactBadge({ level }: { level: ImpactLevel }) {
  return (
    <span
      style={{
        fontSize: '0.65rem',
        fontWeight: 700,
        letterSpacing: '0.08em',
        color: IMPACT_COLORS[level],
        background: IMPACT_BG[level],
        borderRadius: '4px',
        padding: '2px 7px',
        border: `1px solid ${IMPACT_COLORS[level]}33`,
        whiteSpace: 'nowrap',
      }}
    >
      {level}
    </span>
  );
}

function ContributionBar({ shap_value, maxMagnitude }: { shap_value: number; maxMagnitude: number }) {
  const normalized = maxMagnitude > 0 ? (Math.abs(shap_value) / maxMagnitude) * 100 : 0;
  const color = shap_value >= 0 ? DIRECTION_COLORS.positive : DIRECTION_COLORS.negative;
  return (
    <div
      style={{
        height: '6px',
        borderRadius: '3px',
        background: 'rgba(255,255,255,0.06)',
        overflow: 'hidden',
        flex: 1,
        maxWidth: '120px',
      }}
    >
      <div
        style={{
          height: '100%',
          width: `${normalized}%`,
          background: color,
          borderRadius: '3px',
          transition: 'width 0.4s ease',
        }}
      />
    </div>
  );
}

function FactorCard({
  factor,
  maxMagnitude,
  index,
}: {
  factor: FeatureContribution;
  maxMagnitude: number;
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const dirColor = DIRECTION_COLORS[factor.contribution_direction];
  const dirIcon = DIRECTION_ICONS[factor.contribution_direction];

  return (
    <div
      style={{
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.07)',
        borderLeft: `3px solid ${dirColor}`,
        borderRadius: '10px',
        padding: '14px 16px',
        marginBottom: '10px',
        cursor: 'pointer',
        transition: 'background 0.2s',
      }}
      onClick={() => setExpanded(e => !e)}
      onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.055)')}
      onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.03)')}
      role="button"
      aria-expanded={expanded}
      id={`factor-card-${index}`}
    >
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        {/* Rank */}
        <span
          style={{
            fontSize: '0.7rem',
            fontWeight: 700,
            color: 'rgba(255,255,255,0.3)',
            minWidth: '18px',
          }}
        >
          #{index + 1}
        </span>

        {/* Direction indicator */}
        <span style={{ fontSize: '0.75rem', color: dirColor, fontWeight: 700 }}>
          {dirIcon}
        </span>

        {/* Feature display name */}
        <span
          style={{
            fontSize: '0.88rem',
            fontWeight: 600,
            color: 'rgba(255,255,255,0.9)',
            flex: 1,
            minWidth: '120px',
          }}
        >
          {factor.display_name}
          {factor.is_demographic && (
            <span
              title="Demographic feature — see fairness note"
              style={{
                fontSize: '0.65rem',
                color: '#a78bfa',
                marginLeft: '5px',
                fontWeight: 500,
              }}
            >
              [demographic]
            </span>
          )}
        </span>

        {/* Original value */}
        {factor.original_value !== null && (
          <span
            style={{
              fontSize: '0.8rem',
              color: 'rgba(255,255,255,0.55)',
              fontWeight: 500,
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {factor.original_value.toFixed(1)}
            {factor.unit && (
              <span style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.3)', marginLeft: '2px' }}>
                {factor.unit}
              </span>
            )}
          </span>
        )}

        {/* SHAP value */}
        <span
          style={{
            fontSize: '0.78rem',
            fontWeight: 700,
            color: dirColor,
            fontVariantNumeric: 'tabular-nums',
            minWidth: '58px',
            textAlign: 'right',
          }}
        >
          {factor.shap_value >= 0 ? '+' : ''}
          {factor.shap_value.toFixed(3)}
        </span>

        {/* Bar */}
        <ContributionBar shap_value={factor.shap_value} maxMagnitude={maxMagnitude} />

        {/* Impact badge */}
        <ImpactBadge level={factor.impact_level} />

        {/* Expand chevron */}
        <span
          style={{
            fontSize: '0.75rem',
            color: 'rgba(255,255,255,0.3)',
            marginLeft: '2px',
            transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s',
          }}
        >
          ▾
        </span>
      </div>

      {/* Expanded explanation */}
      {expanded && (
        <div
          style={{
            marginTop: '10px',
            padding: '10px 14px',
            background: 'rgba(255,255,255,0.04)',
            borderRadius: '7px',
            fontSize: '0.82rem',
            color: 'rgba(255,255,255,0.65)',
            lineHeight: 1.6,
            borderLeft: `2px solid ${dirColor}44`,
          }}
        >
          {factor.student_explanation}
        </div>
      )}
    </div>
  );
}

function GlobalImportanceChart({ features }: { features: Record<string, number> }) {
  const sorted = Object.entries(features).sort(([, a], [, b]) => b - a).slice(0, 8);
  const maxVal = sorted.length > 0 ? sorted[0][1] : 1;

  return (
    <div>
      {sorted.map(([name, pct]) => {
        const displayName = name
          .replace(/^enc_/, '')
          .replace(/_/g, ' ')
          .replace(/\b\w/g, c => c.toUpperCase());
        return (
          <div key={name} style={{ marginBottom: '8px' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '4px',
              }}
            >
              <span
                style={{
                  fontSize: '0.78rem',
                  color: 'rgba(255,255,255,0.65)',
                  fontWeight: 500,
                  maxWidth: '70%',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {displayName}
              </span>
              <span
                style={{
                  fontSize: '0.72rem',
                  color: 'rgba(255,255,255,0.4)',
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {pct.toFixed(1)}%
              </span>
            </div>
            <div
              style={{
                height: '5px',
                borderRadius: '3px',
                background: 'rgba(255,255,255,0.06)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${(pct / maxVal) * 100}%`,
                  background: 'linear-gradient(90deg, #818cf8 0%, #a78bfa 100%)',
                  borderRadius: '3px',
                  transition: 'width 0.5s ease',
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// -----------------------------------------------------------------------
// Main ExplanationPanel Component
// -----------------------------------------------------------------------

export default function ExplanationPanel({
  explanation,
  taskType,
  predictedCGPA,
  riskLevel,
  riskScore,
}: ExplanationPanelProps) {
  const [showGlobal, setShowGlobal] = useState(false);
  const [showFairness, setShowFairness] = useState(false);

  const maxMagnitude =
    explanation.top_factors.length > 0
      ? Math.max(...explanation.top_factors.map(f => Math.abs(f.shap_value)))
      : 1;

  const isCGPA = taskType === 'cgpa_regression';
  const accentColor = isCGPA ? '#818cf8' : riskLevel ? RISK_LEVEL_COLORS[riskLevel] : '#f59e0b';

  if (!explanation.explanation_available) {
    return (
      <div
        id="explanation-panel-unavailable"
        style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: '14px',
          padding: '20px 24px',
          marginTop: '16px',
          textAlign: 'center',
          color: 'rgba(255,255,255,0.4)',
          fontSize: '0.85rem',
        }}
      >
        <span style={{ fontSize: '1.4rem', display: 'block', marginBottom: '8px' }}>⚠️</span>
        Detailed explanations are not available for this model type ({explanation.model_type}).
        <br />
        The prediction is still valid and reliable.
      </div>
    );
  }

  return (
    <div
      id="explanation-panel"
      style={{
        background: 'rgba(15, 15, 30, 0.6)',
        backdropFilter: 'blur(12px)',
        border: `1px solid ${accentColor}33`,
        borderRadius: '16px',
        padding: '24px',
        marginTop: '20px',
        fontFamily: "'Inter', 'Segoe UI', sans-serif",
      }}
    >
      {/* Panel Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: `${accentColor}22`,
            border: `1px solid ${accentColor}44`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1rem',
          }}
        >
          🧠
        </div>
        <div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: 'rgba(255,255,255,0.92)' }}>
            Why This Prediction?
          </div>
          <div style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.4)', marginTop: '1px' }}>
            {explanation.explainer_type} · {explanation.model_name} · {explanation.model_version}
          </div>
        </div>

        {/* Model additive check */}
        {predictedCGPA !== undefined && (
          <div
            style={{
              marginLeft: 'auto',
              textAlign: 'right',
            }}
          >
            <div
              style={{
                fontSize: '1.4rem',
                fontWeight: 800,
                color: accentColor,
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {predictedCGPA.toFixed(2)}
            </div>
            <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.3)' }}>
              Predicted CGPA
            </div>
          </div>
        )}
        {riskLevel && riskScore !== undefined && (
          <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
            <div
              style={{
                fontSize: '1.1rem',
                fontWeight: 800,
                color: RISK_LEVEL_COLORS[riskLevel] || accentColor,
              }}
            >
              {riskLevel}
            </div>
            <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.3)' }}>
              Risk · Score {riskScore.toFixed(0)}/100
            </div>
          </div>
        )}
      </div>

      {/* Positive / Negative split summary */}
      <div
        style={{
          display: 'flex',
          gap: '12px',
          marginBottom: '20px',
          flexWrap: 'wrap',
        }}
      >
        <div
          style={{
            flex: 1,
            minWidth: '120px',
            background: 'rgba(34, 197, 94, 0.07)',
            border: '1px solid rgba(34, 197, 94, 0.18)',
            borderRadius: '10px',
            padding: '12px 16px',
          }}
        >
          <div
            style={{ fontSize: '0.68rem', color: '#22c55e', fontWeight: 600, letterSpacing: '0.06em', marginBottom: '4px' }}
          >
            ▲ SUPPORTING FACTORS
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#22c55e' }}>
            {explanation.positive_factors.length}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.35)', marginTop: '2px' }}>
            features helping your outcome
          </div>
        </div>
        <div
          style={{
            flex: 1,
            minWidth: '120px',
            background: 'rgba(239, 68, 68, 0.07)',
            border: '1px solid rgba(239, 68, 68, 0.18)',
            borderRadius: '10px',
            padding: '12px 16px',
          }}
        >
          <div
            style={{ fontSize: '0.68rem', color: '#ef4444', fontWeight: 600, letterSpacing: '0.06em', marginBottom: '4px' }}
          >
            ▼ RISK FACTORS
          </div>
          <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ef4444' }}>
            {explanation.negative_factors.length}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.35)', marginTop: '2px' }}>
            features hurting your outcome
          </div>
        </div>
        {explanation.explained_class && (
          <div
            style={{
              flex: 1,
              minWidth: '120px',
              background: `${RISK_LEVEL_COLORS[explanation.explained_class] || accentColor}11`,
              border: `1px solid ${RISK_LEVEL_COLORS[explanation.explained_class] || accentColor}33`,
              borderRadius: '10px',
              padding: '12px 16px',
            }}
          >
            <div
              style={{
                fontSize: '0.68rem',
                color: RISK_LEVEL_COLORS[explanation.explained_class] || accentColor,
                fontWeight: 600,
                letterSpacing: '0.06em',
                marginBottom: '4px',
              }}
            >
              EXPLAINING CLASS
            </div>
            <div
              style={{
                fontSize: '1.15rem',
                fontWeight: 700,
                color: RISK_LEVEL_COLORS[explanation.explained_class] || accentColor,
              }}
            >
              {explanation.explained_class}
            </div>
          </div>
        )}
      </div>

      {/* Section: Top Contributing Factors */}
      <div style={{ marginBottom: '20px' }}>
        <div
          style={{
            fontSize: '0.72rem',
            fontWeight: 700,
            color: 'rgba(255,255,255,0.4)',
            letterSpacing: '0.1em',
            marginBottom: '12px',
            textTransform: 'uppercase',
          }}
        >
          TOP CONTRIBUTING FACTORS
        </div>
        {explanation.top_factors.length === 0 ? (
          <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: '0.85rem', padding: '10px 0' }}>
            No factor data available.
          </div>
        ) : (
          explanation.top_factors.map((factor, i) => (
            <FactorCard key={factor.feature_name} factor={factor} maxMagnitude={maxMagnitude} index={i} />
          ))
        )}
      </div>

      {/* Toggle: Global Importance */}
      <div style={{ marginBottom: '12px' }}>
        <button
          id="btn-toggle-global-importance"
          onClick={() => setShowGlobal(s => !s)}
          style={{
            width: '100%',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '9px',
            padding: '10px 16px',
            color: 'rgba(255,255,255,0.6)',
            fontSize: '0.83rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            transition: 'background 0.2s',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.07)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.04)')}
        >
          <span>📊 Global Model Feature Importance</span>
          <span style={{ transform: showGlobal ? 'rotate(180deg)' : '', transition: 'transform 0.2s' }}>▾</span>
        </button>
        {showGlobal && (
          <div
            style={{
              background: 'rgba(255,255,255,0.025)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderTop: 'none',
              borderRadius: '0 0 9px 9px',
              padding: '16px',
            }}
          >
            <div style={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)', marginBottom: '12px' }}>
              Mean |SHAP| across training data, normalized to 100%. Reflects model-level patterns,
              not this individual prediction.
            </div>
            <GlobalImportanceChart features={explanation.top_global_features} />
          </div>
        )}
      </div>

      {/* Toggle: Fairness Note */}
      <div>
        <button
          id="btn-toggle-fairness-note"
          onClick={() => setShowFairness(s => !s)}
          style={{
            width: '100%',
            background: explanation.contains_demographic_factors
              ? 'rgba(167, 139, 250, 0.06)'
              : 'rgba(255,255,255,0.04)',
            border: explanation.contains_demographic_factors
              ? '1px solid rgba(167, 139, 250, 0.2)'
              : '1px solid rgba(255,255,255,0.08)',
            borderRadius: '9px',
            padding: '10px 16px',
            color: explanation.contains_demographic_factors
              ? '#a78bfa'
              : 'rgba(255,255,255,0.5)',
            fontSize: '0.83rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            transition: 'background 0.2s',
          }}
        >
          <span>
            ⚖️ Limitations & Fairness Disclosure
            {explanation.contains_demographic_factors && (
              <span
                style={{
                  marginLeft: '8px',
                  background: 'rgba(167, 139, 250, 0.15)',
                  color: '#a78bfa',
                  fontSize: '0.62rem',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '4px',
                  letterSpacing: '0.05em',
                }}
              >
                DEMOGRAPHIC FACTOR PRESENT
              </span>
            )}
          </span>
          <span style={{ transform: showFairness ? 'rotate(180deg)' : '', transition: 'transform 0.2s' }}>▾</span>
        </button>
        {showFairness && (
          <div
            style={{
              background: 'rgba(167, 139, 250, 0.04)',
              border: '1px solid rgba(167, 139, 250, 0.12)',
              borderTop: 'none',
              borderRadius: '0 0 9px 9px',
              padding: '16px',
              fontSize: '0.8rem',
              color: 'rgba(255,255,255,0.55)',
              lineHeight: 1.65,
            }}
          >
            {explanation.fairness_note}
          </div>
        )}
      </div>
    </div>
  );
}
