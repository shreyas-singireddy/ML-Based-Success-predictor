import React from 'react';
import { AnimatedSection } from './AnimatedSection';
import { RiskGauge } from '../dashboard/RiskGauge';

interface DemoFactor {
  name: string;
  level: 'minimal' | 'low' | 'medium' | 'high' | 'critical';
  value: string;
  detail: string;
}

const DEMO_FACTORS: DemoFactor[] = [
  { name: 'ATTENDANCE', level: 'medium', value: '67%', detail: 'Below the 75% threshold for this semester — primary risk driver.' },
  { name: 'BACKLOG COUNT', level: 'high', value: '3', detail: 'Recurring backlogs concentrate your risk score.' },
  { name: 'MID-TERM DIP', level: 'low', value: '−8%', detail: 'Mid-2 marks trailed mid-1; recoverable.' },
];

export const RiskShowcase: React.FC = () => {
  return (
    <AnimatedSection id="predictions" className="feature-section feature-section--risk">
      <div className="section-label" style={{ textAlign: 'center' }}>
        <span className="mono-label">DEMO // RISK ENGINE</span>
        <h2>KNOW YOUR RISK BEFORE THE RESULTS</h2>
      </div>

      <div className="feature-grid feature-grid--risk">
        <div className="demo-visual">
          <span className="demo-tag">ILLUSTRATIVE DATA — NOT YOUR RECORDS</span>
          <RiskGauge score={62} level="MEDIUM" />
        </div>
        <div className="factor-panel">
          <span className="mono-label">DRIVING FACTORS</span>
          {DEMO_FACTORS.map((f) => (
            <div key={f.name} className="factor-row demo">
              <div className="factor-name">{f.name}</div>
              <div className="factor-value">{f.value}</div>
              <div className="factor-detail">{f.detail}</div>
              <span className={`node-status-chip ${f.level}`}>{f.level}</span>
            </div>
          ))}
          <span className="mono-label" style={{ marginTop: 'auto' }}>EVERY DIGIT FROM THE SERVER</span>
        </div>
      </div>
    </AnimatedSection>
  );
};