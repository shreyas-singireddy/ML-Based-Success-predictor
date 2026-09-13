import React, { useEffect, useMemo, useRef } from 'react';
import { Fingerprint } from 'lucide-react';
import { prefersReducedMotion } from '../../hooks/usePrefersReducedMotion';

type NodeStatus = 'ready' | 'soon';

interface NetworkNode {
  code: string;
  title: string;
  blurb: string;
  status: NodeStatus;
  orbit: { x: number; y: number };
}

const NODES: NetworkNode[] = [
  { code: '01', title: 'SIGNAL INTAKE', blurb: 'Attendance, previous CGPA, mid & internal marks per semester.', status: 'ready', orbit: { x: 16, y: 30 } },
  { code: '02', title: 'CGPA ENGINE', blurb: 'Delivers your predicted semester CGPA from academic inputs.', status: 'ready', orbit: { x: 82, y: 22 } },
  { code: '03', title: 'RISK ENGINE', blurb: 'Classifies academic risk as MINIMUM → CRITICAL, scored 0–100.', status: 'ready', orbit: { x: 88, y: 72 } },
  { code: '04', title: 'EXPLAINABILITY', blurb: 'Assigns SHAP-attributed credit and blame to each factor.', status: 'ready', orbit: { x: 20, y: 76 } },
  { code: '05', title: 'WHAT-IF SIMULATOR', blurb: 'Tune inputs to preview improved CGPA, risk level, and delta vs baseline.', status: 'ready', orbit: { x: 50, y: 12 } },
  { code: '06', title: 'RECOMMENDATIONS', blurb: 'Prescriptive next-semester actions from your risk drivers.', status: 'soon', orbit: { x: 50, y: 92 } },
];

const CENTER = { x: 50, y: 50 };

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const ease = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

/**
 * Sticky-scroll "engine" visualization. Nodes travel from the edges toward
 * their orbits while the active stage lights up. Under reduced motion the
 * whole pipeline renders as a static rack. Cost: transform/opacity only.
 */
export const AINetwork: React.FC = () => {
  const reduced = useMemo(() => prefersReducedMotion(), []);
  const sectionRef = useRef<HTMLElement | null>(null);
  const nodeRefs = useRef<Array<HTMLDivElement | null>>([]);
  const linkRefs = useRef<Array<SVGPathElement | null>>([]);
  const infoRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (reduced) return;
    let raf = 0;
    const section = sectionRef.current;
    const viewport = section?.querySelector('.network-viewport') as HTMLElement | null;
    if (!section || !viewport) return;

    const frame = () => {
      const rect = section.getBoundingClientRect();
      const total = rect.height - window.innerHeight;
      const raw = -rect.top / Math.max(total, 1);
      const p = Math.min(Math.max(raw, 0), 1);
      const e = ease(p);

      nodeRefs.current.forEach((el, i) => {
        if (!el) return;
        const node = NODES[i];
        const startX = lerp(12, node.orbit.x, 0.25);
        const startY = lerp(10 + (i % 3) * 26, node.orbit.y, 0.25);
        const x = lerp(startX, node.orbit.x, e);
        const y = lerp(startY, node.orbit.y, e);
        el.style.left = `${x}%`;
        el.style.top = `${y}%`;

        // Active threshold by index
        const active = p >= i / NODES.length && p < (i + 1) / NODES.length;
        el.classList.toggle('is-active', active);
        if (active && infoRef.current) {
          infoRef.current.innerHTML =
            `<span class="mono-label">STAGE ${node.code} // ${node.status === 'soon' ? 'WHAT-IF · RECOMMENDATIONS' : 'LIVE'}</span><span class="network-info-title">${node.title}</span><span class="network-info-blurb">${node.blurb}</span>`;
        }
      });

      const vw = viewport.clientWidth;
      const vh = viewport.clientHeight;
      linkRefs.current.forEach((path, i) => {
        if (!path) return;
        const el = nodeRefs.current[i];
        if (!el) return;
        const nx = (parseFloat(el.style.left) / 100) * vw;
        const ny = (parseFloat(el.style.top) / 100) * vh;
        const cx = (CENTER.x / 100) * vw;
        const cy = (CENTER.y / 100) * vh;
        path.setAttribute('d', `M ${nx.toFixed(1)} ${ny.toFixed(1)} L ${cx.toFixed(1)} ${cy.toFixed(1)}`);
      });

      raf = requestAnimationFrame(frame);
    };

    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  }, [reduced]);

  // --- Reduced-motion static rack -------------------------------------------
  if (reduced) {
    return (
      <section id="how-it-works" className="network-section network-section--static">
        <div className="network-static">
          <div className="section-label">
            <span className="mono-label">HOW THE ENGINE WORKS</span>
            <h2>SEVEN STAGES. ZERO FICTION.</h2>
          </div>
          <div className="network-static-grid">
            {NODES.map((node) => (
              <div key={node.code} className={`network-node network-node--static ${node.status}`}>
                <span className="node-code">{node.code}</span>
                <span className="node-title">{node.title}</span>
                <span className="node-blurb">{node.blurb}</span>
                <span className={`node-status ${node.status}`}>
                  {node.status === 'ready' ? 'AVAILABLE' : 'IN DEVELOPMENT'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section id="how-it-works" className="network-section" ref={sectionRef} aria-labelledby="network-heading">
      <div className="network-viewport">
        <div className="section-label" style={{ position: 'absolute', top: 'clamp(64px, 10vh, 110px)', left: '50%', transform: 'translateX(-50%)', textAlign: 'center', zIndex: 3 }}>
          <span className="mono-label">HOW THE ENGINE WORKS</span>
          <h2 id="network-heading">SEVEN STAGES. ZERO FICTION.</h2>
        </div>

        <svg className="network-links" aria-hidden="true">
          {NODES.map((node) => (
            <path
              key={`link-${node.code}`}
              ref={(el) => {
                linkRefs.current[Number(node.code) - 1] = el;
              }}
            />
          ))}
        </svg>

        {/* Engine core */}
        <div className="network-core">
          <span className="brand-mark"><Fingerprint size={20} /></span>
          <span>PHASE 6 · EXPLAINABLE CORE</span>
        </div>

        {NODES.map((node, i) => (
          <div
            key={node.code}
            className={`network-node ${node.status}`}
            ref={(el) => {
              nodeRefs.current[i] = el;
            }}
            style={{ left: lerp(12, node.orbit.x, 0.25) + '%', top: lerp(10 + (i % 3) * 26, node.orbit.y, 0.25) + '%' }}
          >
            <span className="node-chip">
              <span className="node-code">{node.code}</span>
              <span className="node-title">{node.title}</span>
            </span>
            <span className={`node-status-chip ${node.status}`}>
              {node.status === 'ready' ? 'LIVE' : 'SOON'}
            </span>
          </div>
        ))}

        <div className="network-info" ref={infoRef}>
          <span className="mono-label">STAGE 01 // LIVE</span>
          <span className="network-info-title">{NODES[0].title}</span>
          <span className="network-info-blurb">{NODES[0].blurb}</span>
        </div>

        <div className="network-scroll-hint">
          <span className="mono-label">SCROLL TO TRAVERSE THE PIPELINE</span>
        </div>
      </div>
    </section>
  );
};