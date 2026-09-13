import React from 'react';

interface AppPageHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export const AppPageHeader: React.FC<AppPageHeaderProps> = ({
  eyebrow,
  title,
  description,
  actions,
}) => {
  return (
    <header className="app-page-header">
      <div>
        {eyebrow && <span className="mono-label">{eyebrow}</span>}
        <h1 className="app-page-title">{title}</h1>
        {description && <p className="app-page-desc">{description}</p>}
      </div>
      {actions && <div className="app-page-actions">{actions}</div>}
    </header>
  );
};