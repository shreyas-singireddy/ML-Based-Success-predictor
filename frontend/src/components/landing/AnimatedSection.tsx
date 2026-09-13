import React from 'react';
import { useInView } from '../../hooks/useInView';

interface AnimatedSectionProps {
  id?: string;
  className?: string;
  children: React.ReactNode;
  as?: 'section' | 'div' | 'footer';
}

/**
 * Scroll-reveal wrapper. Adds `.in-view` once the block enters the viewport;
 * elements inside opt in via `.reveal`. Unobservable/no-IO environments always
 * render visible.
 */
export const AnimatedSection: React.FC<AnimatedSectionProps> = ({ id, className = '', children, as = 'section' }) => {
  const { ref, inView } = useInView<HTMLElement>({ once: true, threshold: 0.12 });
  const Tag = as as React.ElementType;
  return (
    <Tag
      id={id}
      ref={ref}
      className={`${inView ? 'in-view' : ''} ${className}`.trim()}
      style={{ willChange: 'opacity, transform' }}
    >
      {children}
    </Tag>
  );
};