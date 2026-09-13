import React, { useState } from 'react';
import { LandingNav } from '../components/landing/LandingNav';
import { LandingFooter } from '../components/landing/LandingFooter';
import { CinematicIntro } from '../components/landing/CinematicIntro';
import { Hero } from '../components/landing/Hero';
import { AINetwork } from '../components/landing/AINetwork';
import { PredictionShowcase } from '../components/landing/PredictionShowcase';
import { RiskShowcase } from '../components/landing/RiskShowcase';
import { XaiShowcase } from '../components/landing/XaiShowcase';
import { FuturePreview } from '../components/landing/FuturePreview';

export const LandingPage: React.FC = () => {
  const [introDone, setIntroDone] = useState(false);

  return (
    <div className="landing">
      {!introDone && <CinematicIntro onDone={() => setIntroDone(true)} />}
      <LandingNav />
      <main id="main-content">
        <Hero />
        <AINetwork />
        <PredictionShowcase />
        <RiskShowcase />
        <XaiShowcase />
        <FuturePreview />
        <div className="cta-band">
          <h2 className="cta-title">READY TO SEE YOUR OWN TRAJECTORY?</h2>
          <a href="/app" className="btn btn-primary btn-lg">OPEN THE DASHBOARD</a>
          <p className="mono-label">AUTHENTICATED STUDENTS ONLY — REAL RECORDS, REAL INSIGHTS.</p>
        </div>
      </main>
      <LandingFooter />
    </div>
  );
};