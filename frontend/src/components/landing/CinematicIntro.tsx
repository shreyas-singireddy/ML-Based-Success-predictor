import React, { useEffect, useState } from 'react';
import { Fingerprint, BrainCircuit } from 'lucide-react';
import { usePrefersReducedMotion } from '../../hooks/usePrefersReducedMotion';

const PHRASES = [
  { text: 'YOUR SUCCESS', icon: Fingerprint },
  { text: 'PREDICTED WITH', icon: null },
  { text: 'PRECISION', icon: BrainCircuit },
];

interface CinematicIntroProps {
  onDone?: () => void;
}

const PHRASE_MS = 950;
const FADE_MS = 620;

/**
 * Opening reveal. Skipped entirely under reduced motion. Decorative only —
 * `aria-hidden`, screen readers get the real hero content below.
 */
export const CinematicIntro: React.FC<CinematicIntroProps> = ({ onDone }) => {
  const reduced = usePrefersReducedMotion();
  const [idx, setIdx] = useState(0);
  const [leaving, setLeaving] = useState(false);
  const [mounted, setMounted] = useState(true);

  useEffect(() => {
    if (reduced) {
      setMounted(false);
      onDone?.();
      return;
    }
    const total = PHRASES.length * PHRASE_MS + FADE_MS;
    const timers: ReturnType<typeof setTimeout>[] = [];
    PHRASES.forEach((_, i) => {
      timers.push(setTimeout(() => setIdx(i), i * PHRASE_MS));
    });
    timers.push(
      setTimeout(() => setLeaving(true), PHRASES.length * PHRASE_MS),
      setTimeout(() => {
        setMounted(false);
        onDone?.();
      }, total)
    );
    return () => timers.forEach(clearTimeout);
  }, [reduced, onDone]);

  if (!mounted) return null;

  const current = PHRASES[idx];

  return (
    <div
      className={`intro-overlay ${leaving ? 'intro-overlay--leaving' : ''}`}
      style={{ animationDuration: `${PHRASE_MS}ms` }}
      aria-hidden="true"
    >
      <div className="intro-content">
        <div className="intro-brand">
          <span className="brand-mark">
            <Fingerprint size={20} />
          </span>
          <span className="intro-brand-line-top">{'// STUDENT SUCCESS'}</span>
          <span className="intro-brand-line-bottom">{'PREDICTION SYSTEM'}</span>
        </div>
        <div className="intro-words">
          {PHRASES.map((phrase, i) => (
            <span key={i} className={`intro-word ${i === idx ? 'is-active' : ''}`}>
              {phrase.text}
            </span>
          ))}
        </div>
        <div className="intro-loader">
          <span />
          <span />
          <span />
        </div>
      </div>
      <div className="intro-skip" onClick={() => { setLeaving(true); setTimeout(() => { setMounted(false); onDone?.(); }, 300); }}>
        SKIP →
      </div>
    </div>
  );
};