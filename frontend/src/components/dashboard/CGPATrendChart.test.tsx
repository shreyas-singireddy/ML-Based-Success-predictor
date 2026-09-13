import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CGPATrendChart, TrendPoint } from './CGPATrendChart';

const DEMO: TrendPoint[] = [
  { semester: 1, label: 'S1', value: 6.2 },
  { semester: 2, label: 'S2', value: 6.8 },
  { semester: 3, label: 'S3', value: 7.1 },
  { semester: 4, label: 'S4', value: 7.4 },
  { semester: 5, label: 'S5', value: 7.6, predicted: true },
];

describe('CGPATrendChart', () => {
  it('renders a chart with an accessible summary naming both series', () => {
    const { container } = render(<CGPATrendChart data={DEMO} />);
    const chart = container.querySelector('svg[role="img"]');
    expect(chart).toBeInTheDocument();
    expect(chart?.getAttribute('aria-label')).toMatch(/predicted/i);
    expect(chart?.getAttribute('aria-label')).toMatch(/recorded/i);
    expect(screen.getAllByText('Actual').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Predicted').length).toBeGreaterThan(0);
  });

  it('marks the predicted point with a labelled hit target', () => {
    const { container } = render(<CGPATrendChart data={DEMO} />);
    const predictedPoint = container.querySelector('[aria-label*="predicted"]');
    expect(predictedPoint).toBeInTheDocument();
    expect(predictedPoint?.getAttribute('aria-label')).toMatch(/S5/);
  });

  it('provides a visible data table alongside the chart', () => {
    render(<CGPATrendChart data={DEMO} />);
    expect(screen.getByText('VIEW DATA TABLE')).toBeInTheDocument();
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getAllByText('7.60').length).toBeGreaterThan(0);
  });

  it('shows an intentional empty state when no points render', () => {
    render(<CGPATrendChart data={[]} />);
    expect(screen.getByText('NO CGPA HISTORY')).toBeInTheDocument();
  });
});