import React from 'react';

interface MetricDisplayProps {
  label: string;
  value: string | number;
  sub?: string;
  hint?: string;
  accent?: string;
  icon?: React.ReactNode;
}

/** Cohesive information-system metric — typography + hairlines, not a floating card. */
export const MetricDisplay: React.FC<MetricDisplayProps> = ({
  label,
  value,
  sub,
  hint,
  accent,
  icon,
}) => {
  return (
    <div className="metric">
      <span className="metric-label">
        {icon}
        {label}
      </span>
      <span className="metric-value" style={accent ? { color: accent } : undefined}>
        {value}
      </span>
      {sub && <span className="metric-sub">{sub}</span>}
      {hint && <span className="metric-hint">{hint}</span>}
    </div>
  );
};