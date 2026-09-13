import React from 'react';
import { Clock, Calendar, CheckSquare, Sparkles, ArrowRight, SlidersHorizontal } from 'lucide-react';
import type { ActionPlan, RecommendationItem } from '../../types';
import { RecommendationCard } from './RecommendationCard';

interface ActionPlanTimelineProps {
  actionPlan: ActionPlan;
}

export const ActionPlanTimeline: React.FC<ActionPlanTimelineProps> = ({ actionPlan }) => {
  const { this_week, next_30_days, longer_term, simulation_summary } = actionPlan;

  const totalActions = this_week.length + next_30_days.length + longer_term.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Simulation Aggregate Highlights if available */}
      {simulation_summary && (
        <div
          className="panel"
          style={{
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(15, 15, 17, 0.95) 100%)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.5rem',
              marginBottom: '0.8rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <SlidersHorizontal size={16} style={{ color: 'var(--color-primary)' }} />
              <span className="mono-label" style={{ color: 'var(--color-primary-hover)', fontWeight: 600 }}>
                WHAT-IF SIMULATION // ACTION PLAN PROJECTED TRAJECTORY
              </span>
            </div>
            <span
              className="mono-label"
              style={{
                fontSize: '0.7rem',
                background: 'rgba(85, 166, 48, 0.15)',
                color: 'var(--color-success)',
                padding: '0.15rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              PROJECTED IMPACT: {simulation_summary.overall_impact}
            </span>
          </div>

          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', margin: '0 0 1rem 0' }}>
            Executing the recommended action plan and achieving the target benchmarks simulates the following model outcomes:
          </p>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
            }}
          >
            <div
              style={{
                padding: '0.75rem',
                background: 'rgba(255, 255, 255, 0.03)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--hairline-subtle)',
              }}
            >
              <div className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                PREDICTED CGPA DELTA
              </div>
              <div
                style={{
                  fontSize: '1.2rem',
                  fontWeight: 700,
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  marginTop: '0.2rem',
                }}
              >
                <span>{simulation_summary.baseline_predicted_cgpa.toFixed(2)}</span>
                <ArrowRight size={14} style={{ color: 'var(--text-muted)' }} />
                <span style={{ color: 'var(--color-success)' }}>
                  {simulation_summary.simulated_predicted_cgpa.toFixed(2)}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-success)' }}>
                  ({simulation_summary.cgpa_delta >= 0 ? '+' : ''}
                  {simulation_summary.cgpa_delta.toFixed(2)})
                </span>
              </div>
            </div>

            <div
              style={{
                padding: '0.75rem',
                background: 'rgba(255, 255, 255, 0.03)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--hairline-subtle)',
              }}
            >
              <div className="mono-label" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                RISK TRANSITION
              </div>
              <div
                style={{
                  fontSize: '1.1rem',
                  fontWeight: 700,
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--color-info)',
                  marginTop: '0.2rem',
                }}
              >
                {simulation_summary.risk_transition}
                {simulation_summary.risk_score_delta !== 0 && (
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                    (score {simulation_summary.risk_score_delta >= 0 ? '+' : ''}
                    {simulation_summary.risk_score_delta.toFixed(1)})
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Horizon 1: THIS WEEK */}
      <section>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '0.8rem',
            borderBottom: '1px solid var(--hairline-subtle)',
            paddingBottom: '0.4rem',
          }}
        >
          <Clock size={16} style={{ color: '#ff4d4f' }} />
          <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            IMMEDIATE ACTIONS // THIS WEEK ({this_week.length})
          </h4>
        </div>

        {this_week.length === 0 ? (
          <div
            style={{
              padding: '1rem',
              color: 'var(--text-muted)',
              fontSize: '0.85rem',
              fontFamily: 'var(--font-mono)',
            }}
          >
            No immediate critical interventions required for this week.
          </div>
        ) : (
          this_week.map((item, idx) => (
            <RecommendationCard key={item.id} recommendation={item} rank={idx + 1} />
          ))
        )}
      </section>

      {/* Horizon 2: NEXT 30 DAYS */}
      <section>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '0.8rem',
            borderBottom: '1px solid var(--hairline-subtle)',
            paddingBottom: '0.4rem',
          }}
        >
          <Calendar size={16} style={{ color: 'var(--color-info)' }} />
          <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            MEDIUM-TERM MILESTONES // NEXT 30 DAYS ({next_30_days.length})
          </h4>
        </div>

        {next_30_days.length === 0 ? (
          <div
            style={{
              padding: '1rem',
              color: 'var(--text-muted)',
              fontSize: '0.85rem',
              fontFamily: 'var(--font-mono)',
            }}
          >
            No 30-day milestone tasks scheduled.
          </div>
        ) : (
          next_30_days.map((item, idx) => (
            <RecommendationCard key={item.id} recommendation={item} rank={this_week.length + idx + 1} />
          ))
        )}
      </section>

      {/* Horizon 3: LONGER TERM */}
      {longer_term.length > 0 && (
        <section>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginBottom: '0.8rem',
              borderBottom: '1px solid var(--hairline-subtle)',
              paddingBottom: '0.4rem',
            }}
          >
            <CheckSquare size={16} style={{ color: 'var(--color-success)' }} />
            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              STRATEGIC GOALS & HABITS // LONGER TERM ({longer_term.length})
            </h4>
          </div>

          {longer_term.map((item, idx) => (
            <RecommendationCard
              key={item.id}
              recommendation={item}
              rank={this_week.length + next_30_days.length + idx + 1}
            />
          ))}
        </section>
      )}
    </div>
  );
};
