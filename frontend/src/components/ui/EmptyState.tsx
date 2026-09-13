import React from 'react';

interface EmptyStateProps {
  title: string;
  body?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}

/** Intentional empty state — zero is never presented as unavailable data. */
export const EmptyState: React.FC<EmptyStateProps> = ({ title, body, action, icon }) => {
  return (
    <div className="state-panel" role="status">
      {icon && <div style={{ color: 'var(--text-muted)' }}>{icon}</div>}
      <div className="state-title">{title}</div>
      {body && <div className="state-body">{body}</div>}
      {action}
    </div>
  );
};