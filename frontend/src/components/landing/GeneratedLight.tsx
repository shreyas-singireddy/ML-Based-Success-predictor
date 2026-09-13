import React, { useEffect, useRef } from 'react';
import { prefersReducedMotion } from '../../hooks/usePrefersReducedMotion';

interface GeneratedLightProps {
  className?: string;
  intensity?: number;
  color?: string;
  seed?: number;
}

/**
 * Canvas-2D ambient light field. Animates layered radial gradients; renders a
 * single static frame when the user prefers reduced motion. No WebGL required.
 * `aria-hidden` — decorative only. Cleanup covers rAF + observers.
 */
export const GeneratedLight: React.FC<GeneratedLightProps> = ({
  className = '',
  intensity = 0.5,
  color = '99,102,241',
  seed = 3,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const reducedRef = useRef(prefersReducedMotion());

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let raf = 0;
    let width = 0;
    let height = 0;
    const reduced = reducedRef.current;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const blobs = Array.from({ length: 5 }, (_, i) => ({
      x: (0.1 + ((i * 37 + seed * 13) % 100) / 100) * 1,
      y: (0.12 + ((i * 53 + seed * 7) % 100) / 100) * 1,
      r: 0.18 + ((i * 11 + seed * 5) % 10) / 22,
      drift: 0.0004 + (i % 3) * 0.0002,
      phase: (i * 1.7 + seed) % (Math.PI * 2),
    }));

    const resize = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      width = rect?.width ?? canvas.clientWidth;
      height = rect?.height ?? canvas.clientHeight;
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const draw = (t: number) => {
      ctx.clearRect(0, 0, width, height);
      blobs.forEach((b) => {
        const x = b.x * width + Math.sin(t * b.drift * 60 + b.phase) * width * 0.03;
        const y = b.y * height + Math.cos(t * b.drift * 45 + b.phase) * height * 0.03;
        const r = Math.max(b.r * width * 1.1, b.r * height * 1.1);
        const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
        grad.addColorStop(0, `rgba(${color},${0.16 * intensity})`);
        grad.addColorStop(0.6, `rgba(${color},${0.05 * intensity})`);
        grad.addColorStop(1, `rgba(${color},0)`);
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, width, height);
      });
    };

    const frame = (t: number) => {
      if (reduced) {
        draw(t);
        return;
      }
      draw(t);
      raf = requestAnimationFrame(frame);
    };

    resize();
    if (reduced) {
      draw(0);
    } else {
      raf = requestAnimationFrame(frame);
    }

    const observer = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(resize) : null;
    if (observer) observer.observe(canvas.parentElement ?? canvas);

    return () => {
      cancelAnimationFrame(raf);
      observer?.disconnect();
    };
  }, [color, intensity, seed]);

  return (
    <canvas
      ref={canvasRef}
      className={`generated-light ${className}`}
      aria-hidden="true"
      style={{ pointerEvents: 'none' }}
    />
  );
};