import React from 'react';
import { BrandMark } from './LandingNav';
import { useAuth } from '../../contexts/AuthContext';

export const LandingFooter: React.FC = () => {
  const { user } = useAuth();
  const year = new Date().getFullYear();

  return (
    <footer className="landing-footer">
      <div className="landing-footer-inner">
        <div className="landing-footer-brand">
          <BrandMark size={26} />
          <span className="nav-brand-text" style={{ color: 'var(--text-primary)' }}>
            <span>SUCCESS</span>
            <span className="dim">PREDICTOR</span>
          </span>
        </div>
        <p className="footer-note">
          Every prediction, risk score, and explanation on this platform is computed
          <strong> server-side</strong>. No fabricated results — ever.
        </p>
        <div className="footer-links">
          <a href="/#features">FEATURES</a>
          <a href="/#how-it-works">PIPELINE</a>
          <a href="/#demo">DEMO</a>
          {user ? (
            <a href="/app">DASHBOARD</a>
          ) : (
            <a href="/login">SIGN IN</a>
          )}
        </div>
        <p className="footer-copy">© {year} STUDENT SUCCESS PREDICTOR — ENGINEERED ON EXPLAINABLE ML.</p>
      </div>
    </footer>
  );
};