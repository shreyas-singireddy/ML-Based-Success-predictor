import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Sparkles,
  SlidersHorizontal,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import type { RecommendationItem, RecommendationPriority } from '../../types';

interface RecommendationCardProps {
  recommendation: RecommendationItem;
  rank?: number;
}

const getPriorityStyle = (priority: RecommendationPriority) => {
  switch (priority) {
    case 'CRITICAL':
      return {
        badgeBg: 'rgba(255, 45, 32, 0.15)',
        badgeBorder: 'rgba(255, 45, 32, 0.4)',
        badgeText: '#ff4d4f',
        accentBorder: '#ff4d4f',
        icon: <AlertTriangle size={15} style={{ color: '#ff4d4f' }} />,
      };
    case 'HIGH':
      return {
        badgeBg: 'rgba(255, 183, 3, 0.15)',
        badgeBorder: 'rgba(255, 183, 3, 0.4)',
        badgeText: '#ffc107',
        accentBorder: '#ffc107',
        icon: <ShieldAlert size={15} style={{ color: '#ffc107' }} />,
      };
    case 'MEDIUM':
      return {
        badgeBg: 'rgba(99, 102, 241, 0.15)',
        badgeBorder: 'rgba(99, 102, 241, 0.35)',
        badgeText: '#818cf8',
        accentBorder: '#6366f1',
        icon: <TrendingUp size={15} style={{ color: '#818cf8' }} />,
      };
    case 'LOW':
    default:
      return {
        badgeBg: 'rgba(85, 166, 48, 0.15)',
        badgeBorder: 'rgba(85, 166, 48, 0.35)',
        badgeText: '#6fbf38',
        accentBorder: '#55a630',
        icon: <CheckCircle2 size={15} style={{ color: '#6fbf38' }} />,
      };
  }
};

const formatCategory = (cat: string): string => {
  return cat.replace(/_/g, ' ');
};

const formatTimeHorizon = (horizon: string): string => {
  switch (horizon) {
    case 'THIS_WEEK':
      return 'THIS WEEK';
    case 'NEXT_30_DAYS':
      return 'NEXT 30 DAYS';
    case 'LONGER_TERM':
      return 'LONGER TERM';
    default:
      return horizon.replace(/_/g, ' ');
  }
};

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  rank,
}) => {
  const [expanded, setExpanded] = useState(false);
  const pStyle = getPriorityStyle(recommendation.priority);

  return (
    <div
      className="panel"
      style={{
        borderLeft: `4px solid ${pStyle.accentBorder}`,
        background: 'var(--bg-panel)',
        borderRadius: 'var(--radius-md)',
        padding: '1.25rem',
        marginBottom: '1rem',
        boxShadow: 'var(--shadow-sm)',
        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
      }}
    >
      {/* Header bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '0.6rem',
          marginBottom: '0.8rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          {rank !== undefined && (
            <span
              className="mono-label"
              style={{
                background: 'rgba(255, 255, 255, 0.06)',
                padding: '0.2rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-muted)',
                fontSize: '0.72rem',
              }}
            >
              #{String(rank).padStart(2, '0')}
            </span>
          )}

          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              background: pStyle.badgeBg,
              border: `1px solid ${pStyle.badgeBorder}`,
              color: pStyle.badgeText,
              padding: '0.2rem 0.55rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.72rem',
              fontFamily: 'var(--font-mono)',
              fontWeight: 600,
              letterSpacing: '0.05em',
            }}
          >
            {pStyle.icon}
            {recommendation.priority}
          </span>

          <span
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--hairline-subtle)',
              color: 'var(--text-secondary)',
              padding: '0.2rem 0.55rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.72rem',
              fontFamily: 'var(--font-mono)',
              letterSpacing: '0.04em',
            }}
          >
            {formatCategory(recommendation.category)}
          </span>

          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem',
              color: 'var(--text-muted)',
              fontSize: '0.72rem',
              fontFamily: 'var(--font-mono)',
              marginLeft: '0.25rem',
            }}
          >
            <Clock size={12} />
            {formatTimeHorizon(recommendation.time_horizon)}
          </span>
        </div>

        {/* Expected Impact Tag */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            IMPACT:
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.72rem',
              fontWeight: 600,
              color:
                recommendation.expected_impact === 'HIGH'
                  ? 'var(--color-success)'
                  : recommendation.expected_impact === 'MEDIUM'
                  ? 'var(--color-info)'
                  : 'var(--text-secondary)',
            }}
          >
            {recommendation.expected_impact}
          </span>
        </div>
      </div>

      {/* Main Title */}
      <h3
        style={{
          fontSize: '1.05rem',
          fontWeight: 600,
          color: 'var(--text-primary)',
          margin: '0 0 0.5rem 0',
          letterSpacing: '-0.01em',
        }}
      >
        {recommendation.title}
      </h3>

      {/* Action Guidance */}
      <p
        style={{
          fontSize: '0.9rem',
          lineHeight: '1.5',
          color: 'var(--text-secondary)',
          margin: '0 0 0.9rem 0',
        }}
      >
        {recommendation.action}
      </p>

      {/* Toggle Evidence Bar */}
      <div
        style={{
          borderTop: '1px solid var(--hairline-subtle)',
          paddingTop: '0.65rem',
          marginTop: '0.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            EVIDENCE SOURCE:
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.72rem',
              color: 'var(--color-primary-hover)',
            }}
          >
            {recommendation.source}
          </span>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="btn btn-ghost btn-sm"
          style={{
            fontSize: '0.75rem',
            padding: '0.2rem 0.5rem',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.3rem',
          }}
          aria-expanded={expanded}
          aria-label={expanded ? 'Hide evidence' : 'View supporting evidence'}
        >
          {expanded ? (
            <>
              HIDE EVIDENCE <ChevronUp size={14} />
            </>
          ) : (
            <>
              VIEW EVIDENCE ({recommendation.evidence.length}) <ChevronDown size={14} />
            </>
          )}
        </button>
      </div>

      {/* Expanded Evidence Drawer */}
      {expanded && (
        <div
          style={{
            marginTop: '0.75rem',
            padding: '0.85rem',
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--hairline-subtle)',
          }}
        >
          <div
            className="mono-label"
            style={{
              fontSize: '0.68rem',
              color: 'var(--text-muted)',
              marginBottom: '0.6rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
            }}
          >
            <Sparkles size={12} style={{ color: 'var(--color-primary)' }} />
            MULTI-LAYER VERIFIED EVIDENCE
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {recommendation.evidence.map((ev, idx) => (
              <div
                key={idx}
                style={{
                  padding: '0.6rem',
                  background: 'rgba(255, 255, 255, 0.02)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--hairline-subtle)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '0.35rem',
                  }}
                >
                  <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                    {ev.display_name}
                  </span>
                  <span
                    className="mono-label"
                    style={{
                      fontSize: '0.68rem',
                      background: 'rgba(99, 102, 241, 0.1)',
                      color: 'var(--color-info)',
                      padding: '0.1rem 0.4rem',
                      borderRadius: '3px',
                    }}
                  >
                    {ev.source}
                  </span>
                </div>

                {/* Values Comparison */}
                <div
                  style={{
                    display: 'flex',
                    gap: '1rem',
                    flexWrap: 'wrap',
                    fontSize: '0.8rem',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-secondary)',
                    marginBottom: '0.3rem',
                  }}
                >
                  {ev.current_value !== null && ev.current_value !== undefined && (
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>CURRENT: </span>
                      <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                        {ev.current_value} {ev.unit}
                      </span>
                    </div>
                  )}

                  {ev.target_or_threshold !== null && ev.target_or_threshold !== undefined && (
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>TARGET/BENCHMARK: </span>
                      <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>
                        {ev.target_or_threshold} {ev.unit}
                      </span>
                    </div>
                  )}

                  {ev.simulated_value !== null && ev.simulated_value !== undefined && (
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>SIMULATED: </span>
                      <span style={{ color: 'var(--color-info)', fontWeight: 600 }}>
                        {ev.simulated_value} {ev.unit}
                      </span>
                    </div>
                  )}
                </div>

                {/* SHAP & Simulation Narrative */}
                {ev.shap_contribution !== null && ev.shap_contribution !== undefined && (
                  <div
                    style={{
                      fontSize: '0.75rem',
                      color: ev.shap_contribution < 0 ? 'var(--risk-high)' : 'var(--risk-minimum)',
                      marginTop: '0.2rem',
                    }}
                  >
                    Model Attribution: SHAP contribution {ev.shap_contribution > 0 ? '+' : ''}
                    {ev.shap_contribution.toFixed(4)} (
                    {ev.shap_contribution < 0 ? 'worsening risk / lowering projection' : 'supporting positive standing'})
                  </div>
                )}

                {ev.impact_detail && (
                  <div
                    style={{
                      fontSize: '0.78rem',
                      color: 'var(--text-secondary)',
                      marginTop: '0.25rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.3rem',
                    }}
                  >
                    <SlidersHorizontal size={12} style={{ color: 'var(--color-primary)' }} />
                    {ev.impact_detail}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
