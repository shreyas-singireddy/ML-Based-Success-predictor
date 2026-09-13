import React from 'react';
import { Loader2 } from 'lucide-react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
  style?: React.CSSProperties;
  label?: string;
}

/**
 * Accessible loading placeholder. Announces progress to screen readers.
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '1rem',
  className = '',
  style,
  label = 'Loading',
}) => {
  return (
    <span
      className={`skeleton ${className}`}
      style={{ width, height, display: 'block', ...style }}
      role="status"
      aria-label={label}
    >
      <span className="sr-only">{label}…</span>
    </span>
  );
};

interface LoadingPanelProps {
  message?: string;
}

/** Full-block loading state for API-driven sections. */
export const LoadingPanel: React.FC<LoadingPanelProps> = ({
  message = 'Analyzing academic data…',
}) => {
  return (
    <div className="state-panel">
      <Loader2 size={22} className="animate-spin" style={{ color: 'var(--color-primary)' }} />
      <div className="state-title">{message}</div>
    </div>
  );
};