import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { RecommendationCard } from './RecommendationCard';
import type { RecommendationItem } from '../../types';

describe('RecommendationCard', () => {
  const mockRec: RecommendationItem = {
    id: 'rec-test-attendance',
    title: 'Improve Class Attendance',
    priority: 'HIGH',
    category: 'ATTENDANCE',
    evidence: [
      {
        factor: 'attendance_percentage',
        display_name: 'Class Attendance',
        current_value: 68.0,
        target_or_threshold: 80.0,
        unit: '%',
        source: 'COMBINED',
        simulated_value: 80.0,
        shap_contribution: -0.28,
        impact_detail: 'Simulating attendance to 80% yields +0.45 predicted CGPA.',
      },
    ],
    action: 'Prioritize attending upcoming scheduled classes to reach the safe target of 80%.',
    expected_impact: 'HIGH',
    source: 'COMBINED',
    time_horizon: 'THIS_WEEK',
    risk_factor: 'Attendance',
  };

  it('renders title, priority badge, category, and action guidance', () => {
    render(<RecommendationCard recommendation={mockRec} rank={1} />);

    expect(screen.getByText('Improve Class Attendance')).toBeInTheDocument();
    expect(screen.getAllByText('HIGH').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('ATTENDANCE')).toBeInTheDocument();
    expect(screen.getByText(/Prioritize attending upcoming scheduled classes/)).toBeInTheDocument();
    expect(screen.getByText('THIS WEEK')).toBeInTheDocument();
  });

  it('toggles expandable evidence drawer when button clicked', () => {
    render(<RecommendationCard recommendation={mockRec} />);

    const toggleBtn = screen.getByRole('button', { name: /View supporting evidence/i });
    expect(toggleBtn).toBeInTheDocument();

    // Click to expand
    fireEvent.click(toggleBtn);
    expect(screen.getByText('MULTI-LAYER VERIFIED EVIDENCE')).toBeInTheDocument();
    expect(screen.getByText('Class Attendance')).toBeInTheDocument();
    expect(screen.getByText('68 %')).toBeInTheDocument();
    expect(screen.getAllByText('80 %').length).toBeGreaterThanOrEqual(1);

    // Click to hide
    fireEvent.click(screen.getByRole('button', { name: /Hide evidence/i }));
    expect(screen.queryByText('MULTI-LAYER VERIFIED EVIDENCE')).not.toBeInTheDocument();
  });
});
