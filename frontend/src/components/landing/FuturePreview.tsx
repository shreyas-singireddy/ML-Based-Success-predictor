import React from 'react';
import { AnimatedSection } from './AnimatedSection';
import { Sparkles, Smartphone, ArrowRight, SlidersHorizontal } from 'lucide-react';

const FUTURES: Array<{
  icon: React.ElementType;
  title: string;
  blurb: string;
  status: 'ready' | 'soon';
  href?: string;
}> = [
  {
    icon: SlidersHorizontal,
    title: 'WHAT-IF SIMULATOR',
    blurb: 'Change attendance, clear a backlog, shift mid marks — see the CGPA impact before it happens.',
    status: 'ready',
    href: '/app/what-if',
  },
  {
    icon: Sparkles,
    title: 'PRESCRIPTIVE RECOMMENDATIONS',
    blurb: 'Actionable next-semester moves ranked by their expected impact on your risk profile.',
    status: 'soon',
  },
  {
    icon: Smartphone,
    title: 'MOBILE EXPERIENCE',
    blurb: 'The full explainable dashboard, optimized for on-the-go review.',
    status: 'soon',
  },
];

/** Honest future state — live features link through; others are marked clearly. */
export const FuturePreview: React.FC = () => {
  return (
    <AnimatedSection id="future" className="feature-section">
      <div className="section-label" style={{ textAlign: 'center' }}>
        <span className="mono-label">ROADMAP STATUS</span>
        <h2>WHAT IS LIVE, WHAT IS NEXT</h2>
      </div>
      <div className="future-grid">
        {FUTURES.map((f) => (
          <div key={f.title} className="future-card">
            <span className={`node-status-chip ${f.status}`}>
              {f.status === 'ready' ? 'AVAILABLE NOW' : 'IN DEVELOPMENT'}
            </span>
            <f.icon size={22} style={{ color: 'var(--color-primary)' }} />
            <span className="future-title">{f.title}</span>
            <span className="future-blurb">{f.blurb}</span>
            {f.href && (
              <a href={f.href} className="btn btn-outline btn-sm">
                OPEN SIMULATOR <ArrowRight size={13} />
              </a>
            )}
          </div>
        ))}
      </div>
    </AnimatedSection>
  );
};