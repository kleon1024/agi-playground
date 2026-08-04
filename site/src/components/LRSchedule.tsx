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
import React, { useMemo, useState } from 'react';
import { scaleLinear } from 'd3-scale';
import { line as d3line } from 'd3-shape';
import Chart from './chart/Chart';

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

const CHART_HEIGHT = 230;
/* The two rates worth reading are the peak and the floor, so those are the y
   ticks — which is also what makes the min-LR slider's effect visible, where an
   unlabelled axis made it invisible. Ticks live in a 62px gutter rather than
   inside the plot: annotated in-plot, they collided with the warmup marker. */
const PADDING = { top: 26, right: 18, bottom: 30, left: 62 };
const SAMPLES = 240;

export default function LRSchedule(): React.ReactElement {
  const [totalSteps, setTotalSteps] = useState(10000);
  const [warmupSteps, setWarmupSteps] = useState(500);
  const [peakExp, setPeakExp] = useState(Math.log10(6e-4));
  const [minLRRatio, setMinLRRatio] = useState(0.1);
  const [noWarmup, setNoWarmup] = useState(false);
  const [hoverStep, setHoverStep] = useState<number | null>(null);

  const peakLR = 10 ** peakExp;
  const warmup = Math.min(warmupSteps, totalSteps - 1);
  const params: ScheduleParams = { totalSteps, warmupSteps: warmup, peakLR, minLRRatio, noWarmup };
  const minLR = peakLR * minLRRatio;

  const samples = useMemo(
    () =>
      Array.from({ length: SAMPLES + 1 }, (_, i) => {
        const step = (i / SAMPLES) * totalSteps;
        return [step, lrAt(step, params)] as [number, number];
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [totalSteps, warmup, peakLR, minLRRatio, noWarmup],
  );

  /* With nothing being pointed at, the readout still reports a real point of the
     schedule rather than an instruction, so the widget says something on a
     device that cannot hover at all. */
  const readStep = hoverStep ?? (noWarmup ? 0 : warmup);
  const readLR = lrAt(readStep, params);

  return (
    <div className="learning-widget">
      {/* Four sliders stacked one per row pushed the chart off the first screen.
          They pair up as soon as the container can hold two 14rem columns. */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(14rem, 1fr))',
          gap: '0 1.5rem',
          marginBottom: '0.5rem',
        }}
      >
        <label style={{ display: 'grid' }}>
          <span>
            total steps <strong>{totalSteps.toLocaleString()}</strong>
          </span>
          <input
            type="range"
            min={500}
            max={50000}
            step={100}
            value={totalSteps}
            onChange={(e) => setTotalSteps(Number(e.target.value))}
          />
        </label>
        <label style={{ display: 'grid' }}>
          <span>
            warmup steps <strong>{warmup.toLocaleString()}</strong>
          </span>
          <input
            type="range"
            min={0}
            max={5000}
            step={50}
            value={warmupSteps}
            onChange={(e) => setWarmupSteps(Number(e.target.value))}
            disabled={noWarmup}
            style={{ opacity: noWarmup ? 0.4 : 1 }}
          />
        </label>
        <label style={{ display: 'grid' }}>
          <span>
            peak LR <strong>{fmtLR(peakLR)}</strong>
          </span>
          <input
            type="range"
            min={-5}
            max={-2}
            step={0.02}
            value={peakExp}
            onChange={(e) => setPeakExp(Number(e.target.value))}
          />
        </label>
        <label style={{ display: 'grid' }}>
          <span>
            min-LR floor <strong>{(minLRRatio * 100).toFixed(0)}%</strong> of peak
          </span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={minLRRatio}
            onChange={(e) => setMinLRRatio(Number(e.target.value))}
          />
        </label>
      </div>

      <label style={{ userSelect: 'none' }}>
        <input type="checkbox" checked={noWarmup} onChange={(e) => setNoWarmup(e.target.checked)} />
        <span style={{ marginLeft: '0.5rem' }}>no warmup — jump straight to peak</span>
      </label>

      <Chart
        height={CHART_HEIGHT}
        padding={PADDING}
        label={`Learning-rate schedule over ${totalSteps.toLocaleString()} steps, ${
          noWarmup ? 'with no warmup' : `warming up over ${warmup.toLocaleString()} steps`
        }, peaking at ${fmtLR(peakLR)} and decaying to ${fmtLR(minLR)}`}
        onPointerAt={(x, frame) =>
          setHoverStep(x === null ? null : (x / frame.innerWidth) * totalSteps)
        }
      >
        {(frame) => {
          const { padding, innerWidth, innerHeight } = frame;
          const x = scaleLinear().domain([0, totalSteps]).range([0, innerWidth]);
          const y = scaleLinear().domain([0, peakLR]).range([innerHeight, 0]);
          const path = d3line<[number, number]>()
            .x((d) => x(d[0]))
            .y((d) => y(d[1]))(samples);

          const floorY = y(minLR);
          const warmupX = x(warmup);
          /* Skipped when the floor tick would sit on top of the peak tick above
             it or the zero tick below it. */
          const showFloorTick = floorY > 16 && floorY < innerHeight - 16;

          return (
            <g transform={`translate(${padding.left},${padding.top})`}>
              <line x1={0} y1={0} x2={0} y2={innerHeight} stroke="var(--rehearse-rule)" />
              <line
                x1={0}
                y1={innerHeight}
                x2={innerWidth}
                y2={innerHeight}
                stroke="var(--rehearse-rule)"
              />
              <text x={0} y={innerHeight + 20} fill="var(--rehearse-copy-muted)">
                step 0
              </text>
              <text
                x={innerWidth}
                y={innerHeight + 20}
                textAnchor="end"
                fill="var(--rehearse-copy-muted)"
              >
                {totalSteps.toLocaleString()}
              </text>

              {/* Peak and floor as y ticks in the gutter. Labelled inside the
                  plot they collided with the warmup marker, and an unlabelled
                  axis left the min-LR slider with no visible consequence. */}
              <line x1={0} y1={0} x2={innerWidth} y2={0} stroke="var(--rehearse-rule)" strokeDasharray="3 4" />
              <text x={-8} y={4} textAnchor="end" fill="var(--rehearse-copy-muted)">
                {fmtLR(peakLR)}
              </text>
              <line
                x1={0}
                y1={floorY}
                x2={innerWidth}
                y2={floorY}
                stroke="var(--rehearse-rule)"
                strokeDasharray="3 4"
              />
              {showFloorTick && (
                <text x={-8} y={floorY + 4} textAnchor="end" fill="var(--rehearse-copy-muted)">
                  {fmtLR(minLR)}
                </text>
              )}
              <text x={-8} y={innerHeight + 4} textAnchor="end" fill="var(--rehearse-copy-muted)">
                0
              </text>

              {!noWarmup && warmup > 0 && (
                <>
                  <line
                    x1={warmupX}
                    y1={0}
                    x2={warmupX}
                    y2={innerHeight}
                    stroke="var(--rehearse-emphasis)"
                    strokeWidth={1.5}
                    strokeDasharray="5 4"
                  />
                  {/* Above the plot, the one band nothing else occupies: at the
                      top of the plot this label sat on the curve, which is flat
                      at peak exactly there, and at the foot it sat on the floor
                      gridline. */}
                  <text
                    x={warmupX > innerWidth * 0.6 ? warmupX - 6 : warmupX + 6}
                    y={-8}
                    textAnchor={warmupX > innerWidth * 0.6 ? 'end' : 'start'}
                    fill="var(--rehearse-emphasis)"
                  >
                    warmup ends
                  </text>
                </>
              )}

              <path
                d={path ?? undefined}
                fill="none"
                stroke={noWarmup ? 'var(--rehearse-caution-strong)' : 'var(--rehearse-action)'}
                strokeWidth={2.5}
              />

              <line
                x1={x(readStep)}
                y1={0}
                x2={x(readStep)}
                y2={innerHeight}
                stroke="var(--rehearse-ink)"
              />
              <circle cx={x(readStep)} cy={y(readLR)} r={4.5} fill="var(--rehearse-ink)" />
            </g>
          );
        }}
      </Chart>

      <div className="widget-controls">
        <span className="widget-controls__status">
          step {Math.round(readStep).toLocaleString()} &middot; lr {fmtLR(readLR)}
          {hoverStep === null && !noWarmup && warmup > 0 ? ' · warmup ends' : ''}
        </span>
      </div>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.75rem' }}>
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
