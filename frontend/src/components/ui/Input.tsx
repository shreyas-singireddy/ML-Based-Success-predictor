import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="input-group">
      {label && <label htmlFor={inputId} className="input-label">{label}</label>}
      <input
        id={inputId}
        className={`input-control ${error ? 'border-danger' : ''} ${className}`}
        {...props}
      />
      {error && <span className="input-error">{error}</span>}
      {!error && helperText && <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{helperText}</span>}
    </div>
  );
};
