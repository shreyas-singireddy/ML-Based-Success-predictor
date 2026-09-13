import { describe, expect, it } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { RiskGauge } from './RiskGauge';

describe('RiskGauge', () => {
  it('renders the numeric score, level text, and accessible label', () => {
    render(<RiskGauge score={62} level="MEDIUM" />);
    expect(screen.getAllByText('MEDIUM').length).toBeGreaterThan(0);
    expect(screen.getByText('62')).toBeInTheDocument();
    expect(screen.getByRole('img')).toHaveAccessibleName(
      'Academic risk score 62 out of 100. Risk level: MEDIUM.'
    );
  });

  it('clamps out-of-range scores to 0–100', () => {
    render(<RiskGauge score={140} level="CRITICAL" />);
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('exposes scale labels so color is never the only cue', () => {
    render(<RiskGauge score={30} level="LOW" />);
    for (const label of ['MINIMUM', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
  });

  it('still renders when hovered/focused (no throw)', () => {
    render(<RiskGauge score={15} level="MINIMUM" />);
    fireEvent.focus(document.querySelector('svg') as SVGElement);
    expect(screen.getByText('15')).toBeInTheDocument();
  });
});