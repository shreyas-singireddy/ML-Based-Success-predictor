import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

export const NotFound: React.FC = () => {
  return (
    <div className="not-found">
      <div className="not-found-code mono-label" style={{ opacity: 0.35 }}>404</div>
      <h1 className="not-found-title" style={{ letterSpacing: '-0.03em' }}>
        THIS SIGNAL HAS NO PATH
      </h1>
      <p className="not-found-sub">
        The route you requested doesn&rsquo;t exist. Return to a page that does.
      </p>
      <div className="hero-cta">
        <Link to="/" className="btn btn-primary">
          BACK TO LANDING <ArrowRight size={16} />
        </Link>
        <Link to="/app" className="btn btn-outline">GO TO DASHBOARD</Link>
      </div>
    </div>
  );
};