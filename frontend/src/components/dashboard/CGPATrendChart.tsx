import React, { useCallback, useEffect, useRef, useState } from 'react';
import { EmptyState } from '../ui/EmptyState';

export interface TrendPoint {
  semester: number;
  label?: string;
  value: number | null;
  predicted?: boolean;
}

interface CGPATrendChartProps {
  data: TrendPoint[];
  height?: number;
}

interface TooltipState {
  x: number;
  y: number;
  point: TrendPoint;
}

const Y_MIN = 0;
const Y_MAX = 10;
const PAD = { top: 18, right: 24, bottom: 34, left: 40 };

function useContainerWidth() {
  const ref = useRef<HTMLDivElement | null>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const measure = () => setWidth(el.clientWidth);
    measure();
    const observer = typeof ResizeObserver !== 'undefined'
      ? new ResizeObserver(measure)
      : null;
    if (observer) observer.observe(el);
    return () => observer?.disconnect();
  }, []);

  return { ref, width };
}

/**
 * CGPA trend — actual semesters (solid) then predicted CGPA (dashed/hollow).
 * Pure presentation; consumes backend values only.
 */
export const CGPATrendChart: React.FC<CGPATrendChartProps> = ({ data, height = 264 }) => {
  const { ref: wrapRef, width } = useContainerWidth();
  const [hover, setHover] = useState<TooltipState | null>(null);

  const plotted = data.filter((d) => d.value !== null);
  const hasPredicted = plotted.some((d) => d.predicted);
  const lastActualIndex = plotted.map((d) => d.predicted).lastIndexOf(false);

  const compute = useCallback(() => {
    const w = Math.max(width, 320);
    const h = height;
    const innerW = w - PAD.left - PAD.right;
    const innerH = h - PAD.top - PAD.bottom;
    const n = plotted.length;
    const xAt = (i: number) => PAD.left + (n === 1 ? innerW / 2 : (i / (n - 1)) * innerW);
    const yAt = (v: number) => PAD.top + innerH - ((Math.min(Math.max(v, Y_MIN), Y_MAX) - Y_MIN) / (Y_MAX - Y_MIN)) * innerH;

    return { w, h, innerW, innerH, n, xAt, yAt };
  }, [width, height, plotted.length]);

  const { w, h, xAt, yAt } = compute();

  const actualPoints = plotted.filter((d, i) => i <= lastActualIndex);
  const predictedPoints = plotted.filter((d) => d.predicted);

  const actualLine = actualPoints.map((d, i) => `${i === 0 ? 'M' : 'L'}${xAt(i)},${yAt(d.value as number)}`).join(' ');

  const predictionStartIndex = lastActualIndex >= 0 ? lastActualIndex : 0;
  const predictedLine = predictedPoints
    .map((d, i) => `L${xAt(predictionStartIndex + 1 + i)},${yAt(d.value as number)}`)
    .join(' ');

  const areaPath = actualPoints.length
    ? `${actualLine} L${xAt(actualPoints.length - 1)},${PAD.top + (h - PAD.top - PAD.bottom)} L${xAt(0)},${PAD.top + (h - PAD.top - PAD.bottom)} Z`
    : '';

  if (width === 0) {
    return (
      <div ref={wrapRef} style={{ width: '100%' }}>
        <div style={{ height }} />
      </div>
    );
  }

  if (plotted.length === 0) {
    return (
      <EmptyState title="NO CGPA HISTORY" body="Semester results are required to build a trend." />
    );
  }

  const summary = plotted
    .map((d) => `${d.label ?? `Semester ${d.semester}`}: ${d.value?.toFixed(2)}${d.predicted ? ' (predicted)' : ''}`)
    .join(', ');

  const handlePointHover = (point: TrendPoint, i: number, show: boolean) => {
    if (show) {
      setHover({ x: xAt(i), y: yAt(point.value as number), point });
    } else {
      setHover(null);
    }
  };

  return (
    <div>
      <div className="chart-wrap" ref={wrapRef} style={{ position: 'relative' }}>
        <svg
          width={w}
          height={h}
          role="img"
          aria-label={`CGPA trend chart. ${summary}. Solid line shows recorded CGPAs; dashed line shows predicted CGPA.`}
        >
          <title>CGPA trend: actual versus predicted</title>
          {/* Gridlines */}
          {[0, 2, 4, 6, 8, 10].map((g) => (
            <g key={g}>
              <line
                x1={PAD.left}
                x2={w - PAD.right}
                y1={yAt(g)}
                y2={yAt(g)}
                stroke="rgba(255,255,255,0.05)"
                strokeWidth={1}
              />
              <text
                x={PAD.left - 10}
                y={yAt(g) + 3}
                textAnchor="end"
                fontSize={10}
                fill="var(--text-muted)"
                fontFamily="var(--font-mono)"
              >
                {g.toFixed(0)}
              </text>
            </g>
          ))}

          {/* Area under actuals */}
          {areaPath && (
            <path d={areaPath} fill="rgba(99,102,241,0.07)" />
          )}

          {/* Actual line */}
          {actualLine && (
            <path
              d={actualLine}
              fill="none"
              stroke="var(--text-primary)"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Predicted connector (dashed) */}
          {predictedLine && (
            <path
              d={predictedLine}
              fill="none"
              stroke="var(--color-primary)"
              strokeWidth={2}
              strokeDasharray="5 5"
              strokeLinecap="round"
            />
          )}

          {/* Points */}
          {plotted.map((point, i) => {
            const cx = xAt(i);
            const cy = yAt(point.value as number);
            const isPredicted = !!point.predicted;
            return (
              <g
                key={`${point.semester}-${i}`}
                tabIndex={0}
                role="button"
                aria-label={`${point.label ? point.label : 'Semester ' + point.semester}: ${point.value?.toFixed(2)}${isPredicted ? ', predicted' : ''}`}
                onMouseEnter={() => handlePointHover(point, i, true)}
                onMouseLeave={() => handlePointHover(point, i, false)}
                onFocus={() => handlePointHover(point, i, true)}
                onBlur={() => handlePointHover(point, i, false)}
                style={{ outline: 'none', cursor: 'pointer' }}
              >
                {isPredicted ? (
                  <>
                    <rect
                      x={cx - 5}
                      y={cy - 5}
                      width={10}
                      height={10}
                      rx={2}
                      transform={`rotate(45 ${cx} ${cy})`}
                      fill="var(--bg-panel)"
                      stroke="var(--color-primary)"
                      strokeWidth={2}
                    />
                    <circle cx={cx} cy={cy} r={7} fill="transparent" />
                  </>
                ) : (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={5}
                    fill="var(--bg-panel)"
                    stroke="var(--text-primary)"
                    strokeWidth={2}
                  />
                )}
                <text
                  x={cx}
                  y={h - 8}
                  textAnchor="middle"
                  fontSize={10.5}
                  fill={isPredicted ? 'var(--color-primary)' : 'var(--text-muted)'}
                  fontFamily="var(--font-mono)"
                >
                  {point.label ?? `S${point.semester}`}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Tooltip */}
        {hover && (
          <div
            role="status"
            style={{
              position: 'absolute',
              left: Math.min(Math.max(hover.x - 60, 4), w - 124),
              top: Math.max(hover.y - 58, 4),
              width: 120,
              background: 'var(--bg-panel-elevated)',
              border: '1px solid var(--hairline)',
              borderRadius: 'var(--radius-md)',
              padding: '0.45rem 0.6rem',
              pointerEvents: 'none',
              boxShadow: 'var(--shadow-md)',
              zIndex: 2,
            }}
          >
            <div style={{ fontSize: '0.62rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              {hover.point.label ?? `Semester ${hover.point.semester}`} · {hover.point.predicted ? 'Predicted' : 'Actual'}
            </div>
            <div style={{ fontSize: '1.05rem', fontWeight: 400, fontVariantNumeric: 'tabular-nums' }}>
              {hover.point.value?.toFixed(2)}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="demo-legend" style={{ justifyContent: 'flex-start', marginTop: '0.4rem' }}>
        <span className="legend-key">
          <span className="swatch" /> Actual
        </span>
        {hasPredicted && (
          <span className="legend-key">
            <span className="swatch dashed" style={{ width: 22 }} /> Predicted
          </span>
        )}
      </div>

      {/* Accessible data table fallback */}
      <details style={{ marginTop: '0.9rem' }} aria-label="CGPA trend data table">
        <summary style={{ fontSize: '0.72rem', color: 'var(--text-muted)', cursor: 'pointer', fontFamily: 'var(--font-mono)' }}>
          VIEW DATA TABLE
        </summary>
        <table className="chart-data-table" style={{ marginTop: '0.6rem' }}>
          <thead>
            <tr>
              <th>Semester</th>
              <th>CGPA</th>
              <th>Type</th>
            </tr>
          </thead>
          <tbody>
            {plotted.map((point, i) => (
              <tr key={i}>
                <td>{point.semester}</td>
                <td>{point.value?.toFixed(2)}</td>
                <td>{point.predicted ? 'Predicted' : 'Actual'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
};

export const PredictedSeriesLegend = () => null;