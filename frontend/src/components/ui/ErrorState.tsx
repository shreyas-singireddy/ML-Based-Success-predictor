import React from 'react';
import { AlertCircle } from 'lucide-react';

interface ErrorStateProps {
  title: string;
  message?: string;
  onRetry?: () => void;
  retryLabel?: string;
}

/** Recoverable error state. Announces to screen readers via role="alert". */
export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  message,
  onRetry,
  retryLabel = 'Try Again',
}) => {
  return (
    <div className="state-panel" role="alert">
      <div style={{ color: 'var(--color-danger)' }}>
        <AlertCircle size={22} />
      </div>
      <div className="state-title">{title}</div>
      {message && <div className="state-body">{message}</div>}
      {onRetry && (
        <button className="btn btn-outline btn-sm" onClick={onRetry} style={{ marginTop: '0.5rem' }}>
          {retryLabel}
        </button>
      )}
    </div>
  );
};