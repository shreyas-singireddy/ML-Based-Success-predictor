import React, { useMemo } from 'react';
import { usePrefersReducedMotion } from '../../hooks/usePrefersReducedMotion';

interface FuzzyTextProps {
  children: React.ReactNode;
  className?: string;
  seed?: number;
}

const BLURS = [
  '0 0 #6366F1',
  '0 0 #8B5CF6',
  '0 0 #06B6D4',
  '0 0 #F0F',
  '0 0 #FF2D20',
];

/**
 * Premium holographic word treatment. Each glyph gets a drifting colored blur.
 * Reduced-motion users receive a stationary (still colorful) treatment.
 */
export const FuzzyText: React.FC<FuzzyTextProps> = ({ children, className = '', seed = 1 }) => {
  const reduced = usePrefersReducedMotion();

  const shadow = useMemo(() => {
    const rnd = (s: number): number => {
      const x = Math.sin(seed + s * 999) * 10000;
      return x - Math.floor(x);
    };
    return BLURS.map((c, i) => {
      const sx = reduced ? 0 : (rnd(i) - 0.5) * 4;
      const sy = reduced ? 0 : (rnd(i + 7) - 0.5) * 3;
      const spread = reduced ? 2 : 1 + rnd(i + 3) * 3;
      return `${sx.toFixed(1)}px ${sy.toFixed(1)}px ${spread.toFixed(1)}px ${c}`;
    }).join(', ');
  }, [reduced, seed]);

  return (
    <span className={`fuzzy-text ${className}`} style={{ textShadow: shadow }}>
      {children}
    </span>
  );
};