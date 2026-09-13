import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { FuzzyText } from './FuzzyText';
import { GeneratedLight } from './GeneratedLight';
import { useAuth } from '../../contexts/AuthContext';

export const Hero: React.FC = () => {
  const { user, isLoading } = useAuth();
  const primaryTarget = user ? '/app' : '/login';

  return (
    <section className="hero" id="hero">
      <GeneratedLight intensity={0.7} />
      <div className="hero-grid" />
      <div className="hero-content">
        <span className="mono-label">ACADEMIC INTELLIGENCE // V6</span>
        <h1 className="hero-title">
          <span>YOUR SUCCESS,</span>
          <FuzzyText seed={7}>PREDICTED</FuzzyText>
          <span>WITH PRECISION</span>
        </h1>
        <p className="hero-sub">
          An explainable AI system that anticipates your CGPA and academic risk months
          before results — and shows you exactly why.
        </p>
        <div className="hero-cta">
          <Link to={primaryTarget} className="btn btn-primary btn-lg">
            {user ? 'OPEN DASHBOARD' : 'GET STARTED'} <ArrowRight size={16} />
          </Link>
          <Link to="/app/explainability" className="btn btn-outline btn-lg">
            SEE HOW IT WORKS
          </Link>
        </div>
        <p className="hero-note">
          {isLoading ? 'SIGNING IN…' : user ? 'WELCOME BACK.' : 'NO CARD EXPECTED — SIGN IN WITH YOUR ACADEMIC CREDENTIALS.'}
        </p>
      </div>
      <div className="hero-stats">
        <div className="hero-stat">
          <span className="mono-label">MODEL</span>
          <span>XGBOOST TUNED</span>
        </div>
        <div className="hero-stat">
          <span className="mono-label">CORRECTNESS</span>
          <span>SHAP-EXPLAINED</span>
        </div>
        <div className="hero-stat">
          <span className="mono-label">GUARANTEE</span>
          <span>0 FABRICATED RESULTS</span>
        </div>
      </div>
    </section>
  );
};