import { useEffect, useState } from 'react';

/** Tracks the user's `prefers-reduced-motion` preference (SSR + live-safe). */
export function usePrefersReducedMotion(): boolean {
  const get = () =>
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const [reduced, setReduced] = useState<boolean>(get);

  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setReduced(query.matches);
    setReduced(get());
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, []);

  return reduced;
}

/** Whether the user prefers no motion. */
export const prefersReducedMotion = (): boolean =>
  typeof window !== 'undefined' &&
  typeof window.matchMedia === 'function' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/** Whether the current context supports the WebGL/Canvas features we rely on. */
export const supportsCanvas = (): boolean => typeof document !== 'undefined' && !!document.createElement('canvas').getContext;