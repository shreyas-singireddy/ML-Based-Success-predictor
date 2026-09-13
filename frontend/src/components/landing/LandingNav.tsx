import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Fingerprint } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

/** Brand mark shared by landing and app rail. */
export const BrandMark: React.FC<{ size?: number }> = ({ size = 24 }) => (
  <span
    className="brand-mark"
    style={{ width: size, height: size, fontSize: size * 0.45, borderRadius: Math.round(size * 0.3) }}
    aria-hidden="true"
  >
    <Fingerprint size={size * 0.62} />
  </span>
);

/** Fixed landing navigation. Transparent → blurred glass on scroll. */
export const LandingNav: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav className={`landing-nav ${scrolled ? 'is-scrolled' : ''}`} aria-label="Primary">
      <Link to="/" className="nav-brand">
        <BrandMark size={28} />
        <span className="nav-brand-text">
          <span>SUCCESS</span>
          <span className="dim">PREDICTOR</span>
        </span>
      </Link>
      <div className="nav-links">
        <a href="#features">FEATURES</a>
        <a href="#how-it-works">PIPELINE</a>
        <a href="#predictions">DEMO</a>
      </div>
      <div className="nav-actions">
        {user ? (
          <Link to="/app" className="btn btn-primary btn-sm">DASHBOARD</Link>
        ) : (
          <>
            <Link to="/login" className="btn btn-ghost btn-sm">SIGN IN</Link>
            <Link to="/login?mode=register" className="btn btn-primary btn-sm">GET STARTED</Link>
          </>
        )}
      </div>
    </nav>
  );
};