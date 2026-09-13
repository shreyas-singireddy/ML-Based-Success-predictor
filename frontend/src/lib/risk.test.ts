import { describe, expect, it } from 'vitest';
import { riskColor, RISK_ORDER, RISK_META } from '../lib/risk';

describe('riskColor', () => {
  it('maps every backend risk level to a semantic token', () => {
    expect(riskColor('LOW')).toBe('var(--risk-low)');
    expect(riskColor('MEDIUM')).toBe('var(--risk-medium)');
    expect(riskColor('HIGH')).toBe('var(--risk-high)');
    expect(riskColor('CRITICAL')).toBe('var(--risk-critical)');
  });

  it('maps spec-level MINIMUM to the minimum token', () => {
    expect(riskColor('MINIMUM')).toBe('var(--risk-minimum)');
  });

  it('falls back to a neutral token for unknown levels', () => {
    expect(riskColor('UNCERTAIN')).toBe('var(--risk-neutral)');
  });
});

describe('RISK_ORDER / RISK_META', () => {
  it('orders levels lowest → highest', () => {
    expect(RISK_ORDER).toEqual(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']);
  });

  it('assigns increasing zones', () => {
    expect(RISK_META.LOW.zone).toBeLessThan(RISK_META.CRITICAL.zone);
  });
});