import React from 'react';
import { riskColor, RISK_SCALE_LABELS } from '../../lib/risk';

interface RiskGaugeProps {
  score: number;
  level: string;
  size?: number;
  caption?: string;
}

const W = 260;
const H = 150;
const CX = 130;
const CY = 122;
const R = 94;
const STROKE = 12;

const ZONES: Array<{ from: number; to: number; level: string }> = [
  { from: 0, to: 20, level: 'MINIMUM' },
  { from: 20, to: 45, level: 'LOW' },
  { from: 45, to: 70, level: 'MEDIUM' },
  { from: 70, to: 88, level: 'HIGH' },
  { from: 88, to: 100, level: 'CRITICAL' },
];

function polar(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

/** Sweep clockwise from a1 (-180) to a2 (0). */
function arcPath(cx: number, cy: number, r: number, a1: number, a2: number) {
  const start = polar(cx, cy, r, a1);
  const end = polar(cx, cy, r, a2);
  const largeArc = a2 - a1 > 180 ? 1 : 0;
  return `M ${start.x.toFixed(2)} ${start.y.toFixed(2)} A ${r} ${r} 0 ${largeArc} 1 ${end.x.toFixed(2)} ${end.y.toFixed(2)}`;
}

/**
 * Premium risk gauge — semantic zones + needle. Never relies on color alone:
 * the numeric score, level text, and scale labels are always rendered.
 */
export const RiskGauge: React.FC<RiskGaugeProps> = ({ score, level, size = W, caption }) => {
  const clamped = Math.min(Math.max(score, 0), 100);
  const needleAngle = -180 + (clamped / 100) * 180;
  const needle = polar(CX, CY, R * 0.66, needleAngle);
  const levelColor = riskColor(level);
  const activeZone = ZONES.find((z) => clamped < z.to) ?? ZONES[ZONES.length - 1];

  return (
    <div className="gauge-wrap">
      <div className="gauge-canvas" style={{ width: size }}>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          width={size}
          height={(size / W) * H}
          role="img"
          aria-label={`Academic risk score ${clamped.toFixed(0)} out of 100. Risk level: ${level}.`}
        >
          <title>Academic risk: {level}, score {clamped.toFixed(0)}/100</title>

          {/* Zone track */}
          {ZONES.map((zone) => {
            const a1 = -180 + (zone.from / 100) * 180;
            const a2 = -180 + (zone.to / 100) * 180;
            const isActive = zone.level === activeZone.level;
            return (
              <path
                key={zone.level}
                d={arcPath(CX, CY, R, a1, a2)}
                fill="none"
                stroke={riskColor(zone.level)}
                strokeWidth={STROKE}
                strokeLinecap="butt"
                opacity={isActive ? 0.95 : 0.22}
              />
            );
          })}

          {/* Inner halo */}
          <path
            d={arcPath(CX, CY, R, -180, 0)}
            fill="none"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={1}
          />

          {/* Needle */}
          <line
            x1={CX}
            y1={CY}
            x2={needle.x}
            y2={needle.y}
            stroke={levelColor}
            strokeWidth={2.5}
            strokeLinecap="round"
          />
          <circle cx={CX} cy={CY} r={5.5} fill={levelColor} />
          <circle cx={CX} cy={CY} r={2.4} fill="var(--bg-app)" />
        </svg>

        <div className="gauge-scale">
          {RISK_SCALE_LABELS.map((s) => (
            <span key={s.label}>{s.label}</span>
          ))}
        </div>
      </div>

      <div className="gauge-status">
        <span className="mono-label" style={{ color: 'var(--text-muted)' }}>
          ACADEMIC RISK
        </span>
        <span
          className={`risk-badge risk-badge--${level.toLowerCase()}`}
        >
          <span className="dot" />
          {level}
        </span>
        <span style={{ fontSize: '2.6rem', fontWeight: 300, letterSpacing: '-0.03em', fontVariantNumeric: 'tabular-nums', lineHeight: 1 }}>
          {clamped.toFixed(0)}
          <span style={{ fontSize: '1rem', color: 'var(--text-muted)', fontWeight: 400 }}>/100</span>
        </span>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', maxWidth: 220 }}>
          {caption ?? 'Continuous risk score from the Phase 4 risk engine.'}
        </span>
      </div>
    </div>
  );
};