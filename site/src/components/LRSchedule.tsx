/**
 * Why warmup exists, and what happens to a schedule that skips it.
 *
 * Adam tracks running estimates of the gradient's mean and variance, both
 * initialised at zero. Early in training those estimates are heavily biased
 * toward zero and have seen only a handful of samples — they are noisy,
 * unreliable statistics. Applying a large, carefully-tuned peak learning
 * rate to an update built on top of that noise produces a big, essentially
 * random first step, and the rest of training spends its budget recovering
 * from wherever that step landed rather than making forward progress.
 *
 * Warmup sidesteps the problem by keeping the LR small while the moment
 * estimates are still forming, then ramping to peak once they have settled.
 * Turn the "no warmup" toggle on below and watch the curve jump straight to
 * peak at step zero instead of ramping — that discontinuity is exactly the
 * badly-biased-update scenario the warmup phase exists to avoid.
 */
import React, { useMemo, useRef, useState } from 'react';

interface ScheduleParams {
  totalSteps: number;
  warmupSteps: number;
  peakLR: number;
  minLRRatio: number;
  noWarmup: boolean;
}

/** Linear warmup into a cosine decay down to a floor of peakLR * minLRRatio. */
function lrAt(step: number, p: ScheduleParams): number {
  const warmup = p.noWarmup ? 0 : Math.min(p.warmupSteps, p.totalSteps - 1);
  const minLR = p.peakLR * p.minLRRatio;
  if (step < warmup) {
    return p.peakLR * (step / Math.max(warmup, 1));
  }
  const denom = Math.max(p.totalSteps - warmup, 1);
  const progress = Math.min((step - warmup) / denom, 1);
  return minLR + 0.5 * (p.peakLR - minLR) * (1 + Math.cos(Math.PI * progress));
}

function fmtLR(x: number): string {
  return x.toExponential(2);
}

const VB_W = 600;
const VB_H = 220;
const PAD_L = 50;
const PAD_R = 12;
const PAD_T = 12;
const PAD_B = 26;
const PLOT_W = VB_W - PAD_L - PAD_R;
const PLOT_H = VB_H - PAD_T - PAD_B;
const SAMPLES = 160;

export default function LRSchedule(): React.ReactElement {
  const [totalSteps, setTotalSteps] = useState(10000);
  const [warmupSteps, setWarmupSteps] = useState(500);
  const [peakExp, setPeakExp] = useState(Math.log10(6e-4));
  const [minLRRatio, setMinLRRatio] = useState(0.1);
  const [noWarmup, setNoWarmup] = useState(false);
  const [hoverStep, setHoverStep] = useState<number | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);

  const peakLR = 10 ** peakExp;
  const warmup = Math.min(warmupSteps, totalSteps - 1);
  const params: ScheduleParams = { totalSteps, warmupSteps: warmup, peakLR, minLRRatio, noWarmup };

  const xScale = (step: number) => PAD_L + (step / totalSteps) * PLOT_W;
  const yScale = (lr: number) => PAD_T + (1 - lr / peakLR) * PLOT_H;

  const path = useMemo(() => {
    const pts: string[] = [];
    for (let i = 0; i <= SAMPLES; i++) {
      const step = (i / SAMPLES) * totalSteps;
      const lr = lrAt(step, params);
      pts.push(`${i === 0 ? 'M' : 'L'} ${xScale(step).toFixed(1)},${yScale(lr).toFixed(1)}`);
    }
    return pts.join(' ');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [totalSteps, warmup, peakLR, minLRRatio, noWarmup]);

  const handleMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const relX = ((e.clientX - rect.left) / rect.width) * VB_W;
    const step = ((relX - PAD_L) / PLOT_W) * totalSteps;
    setHoverStep(Math.max(0, Math.min(totalSteps, step)));
  };

  const hoverLR = hoverStep === null ? null : lrAt(hoverStep, params);

  return (
    <div style={{ margin: '1.5rem 0' }}>
      <div style={{ display: 'grid', gap: '0.6rem', marginBottom: '1rem' }}>
        <label style={{ display: 'flex', gap: '0.7rem', alignItems: 'center' }}>
          <span style={{ minWidth: '9rem' }}>total steps <strong>{totalSteps.toLocaleString()}</strong></span>
          <input type="range" min={500} max={50000} step={100} value={totalSteps}
                 onChange={(e) => setTotalSteps(Number(e.target.value))}
                 style={{ flex: 1, maxWidth: 260 }} />
        </label>
        <label style={{ display: 'flex', gap: '0.7rem', alignItems: 'center' }}>
          <span style={{ minWidth: '9rem' }}>warmup steps <strong>{warmup.toLocaleString()}</strong></span>
          <input type="range" min={0} max={5000} step={50} value={warmupSteps}
                 onChange={(e) => setWarmupSteps(Number(e.target.value))}
                 disabled={noWarmup}
                 style={{ flex: 1, maxWidth: 260, opacity: noWarmup ? 0.4 : 1 }} />
        </label>
        <label style={{ display: 'flex', gap: '0.7rem', alignItems: 'center' }}>
          <span style={{ minWidth: '9rem' }}>peak LR <strong>{fmtLR(peakLR)}</strong></span>
          <input type="range" min={-5} max={-2} step={0.02} value={peakExp}
                 onChange={(e) => setPeakExp(Number(e.target.value))}
                 style={{ flex: 1, maxWidth: 260 }} />
        </label>
        <label style={{ display: 'flex', gap: '0.7rem', alignItems: 'center' }}>
          <span style={{ minWidth: '9rem' }}>min-LR floor <strong>{(minLRRatio * 100).toFixed(0)}%</strong> of peak</span>
          <input type="range" min={0} max={1} step={0.01} value={minLRRatio}
                 onChange={(e) => setMinLRRatio(Number(e.target.value))}
                 style={{ flex: 1, maxWidth: 260 }} />
        </label>
        <label style={{ cursor: 'pointer', userSelect: 'none' }}>
          <input type="checkbox" checked={noWarmup} onChange={(e) => setNoWarmup(e.target.checked)} />{' '}
          no warmup — jump straight to peak
        </label>
      </div>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        style={{ width: '100%', height: 'auto', cursor: 'crosshair' }}
        onMouseMove={handleMove}
        onMouseLeave={() => setHoverStep(null)}
      >
        {/* axes */}
        <line x1={PAD_L} y1={PAD_T} x2={PAD_L} y2={VB_H - PAD_B} stroke="var(--ifm-color-emphasis-400)" />
        <line x1={PAD_L} y1={VB_H - PAD_B} x2={VB_W - PAD_R} y2={VB_H - PAD_B} stroke="var(--ifm-color-emphasis-400)" />
        <text x={PAD_L - 6} y={PAD_T + 4} textAnchor="end" fontSize={9} fill="var(--ifm-font-color-base)" opacity={0.7}>
          {fmtLR(peakLR)}
        </text>
        <text x={PAD_L - 6} y={VB_H - PAD_B} textAnchor="end" fontSize={9} fill="var(--ifm-font-color-base)" opacity={0.7}>
          0
        </text>
        <text x={PAD_L} y={VB_H - 8} fontSize={9} fill="var(--ifm-font-color-base)" opacity={0.7}>0</text>
        <text x={VB_W - PAD_R} y={VB_H - 8} textAnchor="end" fontSize={9} fill="var(--ifm-font-color-base)" opacity={0.7}>
          {totalSteps.toLocaleString()}
        </text>

        {/* warmup boundary marker */}
        {!noWarmup && warmup > 0 && (
          <>
            <line
              x1={xScale(warmup)} y1={PAD_T} x2={xScale(warmup)} y2={VB_H - PAD_B}
              stroke="var(--brand-chart-warning)" strokeWidth={1} strokeDasharray="4 3"
            />
            <text x={xScale(warmup) + 4} y={PAD_T + 10} fontSize={9} fill="var(--brand-chart-warning)">
              warmup ends
            </text>
          </>
        )}

        {/* the schedule curve */}
        <path d={path} fill="none" stroke={noWarmup ? 'var(--brand-chart-danger)' : 'var(--brand-chart-positive)'} strokeWidth={2} />

        {/* hover readout */}
        {hoverStep !== null && hoverLR !== null && (
          <>
            <line
              x1={xScale(hoverStep)} y1={PAD_T} x2={xScale(hoverStep)} y2={VB_H - PAD_B}
              stroke="var(--ifm-color-emphasis-500)" strokeWidth={1}
            />
            <circle cx={xScale(hoverStep)} cy={yScale(hoverLR)} r={3.5} fill="var(--brand-chart-danger)" />
          </>
        )}
      </svg>

      <div style={{ display: 'flex', gap: '1.4rem', fontSize: '0.85rem', flexWrap: 'wrap', minHeight: '1.2rem' }}>
        {hoverStep !== null && hoverLR !== null ? (
          <span>
            step <strong>{Math.round(hoverStep).toLocaleString()}</strong> → lr <strong>{fmtLR(hoverLR)}</strong>
          </span>
        ) : (
          <span style={{ opacity: 0.6 }}>hover the curve to read the LR at a step</span>
        )}
      </div>

      <p style={{ fontSize: '0.8rem', opacity: 0.75, marginTop: '0.75rem' }}>
        With warmup on, the LR ramps linearly to peak over the marked region —
        by the time it arrives, Adam&apos;s bias-corrected moment estimates have
        seen enough gradients to be trustworthy. Flip <strong>no warmup</strong>{' '}
        on and the curve jumps straight to peak at step zero: the full learning
        rate hits estimates built from a single noisy gradient, which is the
        instability warmup is designed to prevent. The cosine tail after
        warmup decays toward the min-LR floor, never quite reaching zero.
      </p>
    </div>
  );
}
