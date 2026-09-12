import React from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

interface AlertProps {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  children,
  className = ''
}) => {
  const icons = {
    info: <Info size={20} color="var(--color-info)" />,
    success: <CheckCircle size={20} color="var(--color-success)" />,
    warning: <AlertTriangle size={20} color="var(--color-warning)" />,
    error: <AlertCircle size={20} color="var(--color-danger)" />
  };

  const bgStyles = {
    info: 'var(--color-info-bg)',
    success: 'var(--color-success-bg)',
    warning: 'var(--color-warning-bg)',
    error: 'var(--color-danger-bg)'
  };

  const borderStyles = {
    info: 'rgba(6, 182, 212, 0.3)',
    success: 'rgba(16, 185, 129, 0.3)',
    warning: 'rgba(245, 158, 11, 0.3)',
    error: 'rgba(244, 63, 94, 0.3)'
  };

  return (
    <div
      className={className}
      style={{
        background: bgStyles[variant],
        border: `1px solid ${borderStyles[variant]}`,
        borderRadius: 'var(--radius-md)',
        padding: '1rem 1.25rem',
        display: 'flex',
        gap: '0.75rem',
        alignItems: 'flex-start',
        marginBottom: '1rem'
      }}
    >
      <div style={{ flexShrink: 0, marginTop: '2px' }}>{icons[variant]}</div>
      <div style={{ flex: 1 }}>
        {title && <h4 style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '0.2rem' }}>{title}</h4>}
        <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>{children}</div>
      </div>
    </div>
  );
};
