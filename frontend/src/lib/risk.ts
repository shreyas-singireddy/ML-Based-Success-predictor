import type { RiskLevel } from '../types';

export const RISK_ORDER: RiskLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

export const RISK_META: Record<RiskLevel, { color: string; zone: number }> = {
  LOW: { color: 'var(--risk-low)', zone: 1 },
  MEDIUM: { color: 'var(--risk-medium)', zone: 2 },
  HIGH: { color: 'var(--risk-high)', zone: 3 },
  CRITICAL: { color: 'var(--risk-critical)', zone: 4 },
};

/**
 * Maps a risk level to its semantic color.
 * Levels not present in the backend (e.g. MINIMUM) map to the LOW token.
 */
export function riskColor(level: string): string {
  switch (level) {
    case 'MINIMUM':
      return 'var(--risk-minimum)';
    case 'LOW':
      return 'var(--risk-low)';
    case 'MEDIUM':
      return 'var(--risk-medium)';
    case 'HIGH':
      return 'var(--risk-high)';
    case 'CRITICAL':
      return 'var(--risk-critical)';
    default:
      return 'var(--risk-neutral)';
  }
}

/** Level → human descriptor for gauge scale labels. */
export const RISK_SCALE_LABELS: { level: string; label: string }[] = [
  { level: 'MINIMUM', label: 'MINIMUM' },
  { level: 'LOW', label: 'LOW' },
  { level: 'MEDIUM', label: 'MEDIUM' },
  { level: 'HIGH', label: 'HIGH' },
  { level: 'CRITICAL', label: 'CRITICAL' },
];