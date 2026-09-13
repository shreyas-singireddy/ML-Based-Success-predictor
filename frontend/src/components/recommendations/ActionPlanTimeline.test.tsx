import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ActionPlanTimeline } from './ActionPlanTimeline';
import type { ActionPlan } from '../../types';

describe('ActionPlanTimeline', () => {
  const mockActionPlan: ActionPlan = {
    this_week: [
      {
        id: 'rec-1',
        title: 'Immediate Attendance Focus',
        priority: 'CRITICAL',
        category: 'ATTENDANCE',
        evidence: [],
        action: 'Attend all labs.',
        expected_impact: 'HIGH',
        source: 'ACADEMIC_DATA',
        time_horizon: 'THIS_WEEK',
      },
    ],
    next_30_days: [
      {
        id: 'rec-2',
        title: 'Prepare for Mid-Terms',
        priority: 'MEDIUM',
        category: 'EXAM_PREPARATION',
        evidence: [],
        action: 'Review sample questions.',
        expected_impact: 'MEDIUM',
        source: 'RISK_POLICY',
        time_horizon: 'NEXT_30_DAYS',
      },
    ],
    longer_term: [],
    simulation_summary: {
      baseline_predicted_cgpa: 6.2,
      simulated_predicted_cgpa: 6.8,
      cgpa_delta: 0.6,
      baseline_risk_level: 'HIGH',
      simulated_risk_level: 'MEDIUM',
      risk_score_delta: -15.0,
      risk_transition: 'HIGH → MEDIUM',
      overall_impact: 'IMPROVED',
    },
  };

  it('renders time horizon groups and simulation outcome summary', () => {
    render(<ActionPlanTimeline actionPlan={mockActionPlan} />);

    expect(screen.getByText(/IMMEDIATE ACTIONS \/\/ THIS WEEK/)).toBeInTheDocument();
    expect(screen.getByText('Immediate Attendance Focus')).toBeInTheDocument();

    expect(screen.getByText(/MEDIUM-TERM MILESTONES \/\/ NEXT 30 DAYS/)).toBeInTheDocument();
    expect(screen.getByText('Prepare for Mid-Terms')).toBeInTheDocument();

    expect(screen.getByText('PROJECTED IMPACT: IMPROVED')).toBeInTheDocument();
    expect(screen.getByText('HIGH → MEDIUM')).toBeInTheDocument();
    expect(screen.getByText('6.20')).toBeInTheDocument();
    expect(screen.getByText('6.80')).toBeInTheDocument();
  });
});
