/**
 * Every arm of the architecture ladder, plotted against the nondeterminism
 * floor the ladder measured on itself.
 *
 * The chapter's finding is not a ranking, it is a threshold: three tiers fall
 * out of the same nine numbers depending on how large a difference you are
 * willing to act on. A table of per-seed differences states that; it does not
 * let you feel it. Here the reader moves the threshold and watches arms cross
 * out of "act on this" into "not resolved" — and sees that the two rungs whose
 * sign flips between seeds never become actionable at any threshold, because
 * consistency and magnitude are different properties.
 *
 * Every number is a per-seed validation-loss difference against that rung's
 * control, from `runs/2026-07-29-five-rungs.md` and `runs/2026-07-28-moe-rung.md`.
 * The floor is that record's own six-way replication of one configuration:
 * range 0.0018, so a claim resting on less than about 0.002 is resting on the
 * allocator. Nothing here is modelled, smoothed, or extrapolated.
 */
import React, { useState } from 'react';
import { scaleLinear } from 'd3-scale';

import Chart from './chart/Chart';

interface Arm {
  /** Short enough to fit the label gutter on a 390px screen. */
  label: string;
  rung: string;
  /** What changed, against that rung's control. */
  change: string;
  /** Validation-loss difference per seed. Negative means the arm won. */
  seeds: [number, number, number];
}

/** The measured nondeterminism floor: six replications of one config, range 0.0018. */
const FLOOR = 0.002;

const ARMS: Arm[] = [
  { label: 'no positions', rung: 'Position', change: 'no positional information vs RoPE', seeds: [0.0981, 0.1087, 0.1084] },
  { label: 'MoE (active)', rung: 'Feed-forward', change: 'MoE at equal active parameters vs dense', seeds: [-0.0942, -0.0940, -0.0822] },
  { label: 'learned pos', rung: 'Position', change: 'learned absolute positions vs RoPE', seeds: [0.0762, 0.0884, 0.0813] },
  { label: '16L x 320', rung: 'Depth/width', change: '16 layers at d_model 320 vs 8 at 512', seeds: [0.0618, 0.0636, 0.0699] },
  { label: '1 KV head', rung: 'Attention', change: 'multi-query attention vs 8 KV heads', seeds: [0.0307, 0.0421, 0.0617] },
  { label: '2 KV heads', rung: 'Attention', change: '2 KV heads vs 8', seeds: [0.0152, 0.0183, 0.0408] },
  { label: '4 KV heads', rung: 'Attention', change: '4 KV heads vs 8', seeds: [0.0096, 0.0004, 0.0177] },
  { label: '4L x 752', rung: 'Depth/width', change: '4 layers at d_model 752 vs 8 at 512', seeds: [-0.0121, -0.0087, -0.0024] },
  { label: 'GELU', rung: 'Activation', change: 'GELU vs SwiGLU at matched parameters', seeds: [0.0001, -0.0115, -0.0031] },
  { label: 'LayerNorm', rung: 'Norm', change: 'LayerNorm vs RMSNorm', seeds: [-0.0023, 0.0052, 0.0091] },
  { label: 'MoE (total)', rung: 'Feed-forward', change: 'MoE at equal total parameters vs dense', seeds: [-0.0034, 0.0002, 0.0029] },
];

const ROW_H = 30;
const PADDING = { top: 24, right: 16, bottom: 40, left: 104 };
const HEIGHT = PADDING.top + ARMS.length * ROW_H + PADDING.bottom;

type Verdict = 'act' | 'under' | 'flipped';

function verdictOf(arm: Arm, threshold: number): Verdict {
  const consistent = arm.seeds.every((s) => s > 0) || arm.seeds.every((s) => s < 0);
  if (!consistent) return 'flipped';
  const mean = (arm.seeds[0] + arm.seeds[1] + arm.seeds[2]) / 3;
  return Math.abs(mean) >= threshold ? 'act' : 'under';
}

const STROKE: Record<Verdict, string> = {
  act: 'var(--rehearse-action)',
  under: 'var(--rehearse-caution)',
  flipped: 'var(--rehearse-copy-muted)',
};

export default function AblationLadder(): React.ReactElement {
  const [threshold, setThreshold] = useState(FLOOR);

  const verdicts = ARMS.map((arm) => verdictOf(arm, threshold));
  const acted = verdicts.filter((v) => v === 'act').length;
  const under = verdicts.filter((v) => v === 'under').length;
  const flipped = verdicts.filter((v) => v === 'flipped').length;

  /* The cheapest arm you would still act on — the one the next click drops. */
  const marginal = ARMS
    .map((arm, i) => ({ arm, v: verdicts[i], mean: (arm.seeds[0] + arm.seeds[1] + arm.seeds[2]) / 3 }))
    .filter((row) => row.v === 'act')
    .sort((a, b) => Math.abs(a.mean) - Math.abs(b.mean))[0];

  return (
    <div className="learning-widget">
      <p>
        Every arm of the ladder, as its three per-seed differences against that
        rung&rsquo;s control: one circle per seed, the line between them their spread,
        and the upright bar the three-seed mean. Left of zero means the arm beat
        the control. Drag the threshold to set how large a difference you are
        willing to act on.
      </p>

      <label>
        Act on differences of at least
        {' '}
        <strong style={{ fontVariantNumeric: 'tabular-nums' }}>{threshold.toFixed(4)}</strong>
        {' '}
        validation loss
        <input
          type="range"
          min={0}
          max={0.09}
          step={0.0005}
          value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
        />
      </label>

      <Chart
        height={HEIGHT}
        padding={PADDING}
        label={
          `Per-seed validation-loss differences for ${ARMS.length} architecture arms. `
          + `At a threshold of ${threshold.toFixed(4)}, ${acted} arms are actionable, `
          + `${under} are directionally consistent but under it, and ${flipped} flip sign between seeds.`
        }
      >
        {(frame) => {
          const { padding, innerWidth, innerHeight } = frame;
          const x = scaleLinear().domain([-0.12, 0.12]).range([0, innerWidth]).clamp(true);
          const zero = x(0);
          const bandLeft = x(-threshold);
          const bandRight = x(threshold);

          return (
            <g transform={`translate(${padding.left},${padding.top})`}>
              {/* The threshold, as the region where a difference buys you nothing. */}
              <rect
                x={bandLeft}
                y={-6}
                width={Math.max(1, bandRight - bandLeft)}
                height={innerHeight + 6}
                fill="var(--rehearse-caution-soft)"
              />
              <line
                x1={zero}
                x2={zero}
                y1={-6}
                y2={innerHeight}
                stroke="var(--rehearse-ink)"
                strokeWidth={1}
              />

              {ARMS.map((arm, i) => {
                const y = i * ROW_H + ROW_H / 2;
                const verdict = verdicts[i];
                const colour = STROKE[verdict];
                const lo = Math.min(...arm.seeds);
                const hi = Math.max(...arm.seeds);
                const mean = (arm.seeds[0] + arm.seeds[1] + arm.seeds[2]) / 3;
                return (
                  <g key={arm.label}>
                    <text
                      x={-10}
                      y={y + 4}
                      textAnchor="end"
                      fill={verdict === 'flipped' ? 'var(--rehearse-copy-muted)' : 'var(--rehearse-ink)'}
                      fontSize={13}
                    >
                      {arm.label}
                    </text>
                    {/* Seed spread first, so the three points sit on top of it. */}
                    <line
                      x1={x(lo)}
                      x2={x(hi)}
                      y1={y}
                      y2={y}
                      stroke={colour}
                      strokeWidth={2}
                      opacity={0.45}
                    />
                    {arm.seeds.map((seed, s) => (
                      <circle
                        key={s}
                        cx={x(seed)}
                        cy={y}
                        r={3.5}
                        fill="var(--rehearse-warm-white)"
                        stroke={colour}
                        strokeWidth={1.6}
                      />
                    ))}
                    <line
                      x1={x(mean)}
                      x2={x(mean)}
                      y1={y - 8}
                      y2={y + 8}
                      stroke={colour}
                      strokeWidth={2.5}
                    />
                  </g>
                );
              })}

              {/* Axis last: it labels a plot the reader has already seen. Five
                  ticks crowd into each other once the plot is phone-width. */}
              <g transform={`translate(0,${innerHeight + 6})`}>
                <line x1={0} x2={innerWidth} y1={0} y2={0} stroke="var(--rehearse-rule)" />
                {(innerWidth < 260 ? [-0.1, 0, 0.1] : [-0.1, -0.05, 0, 0.05, 0.1]).map((tick) => (
                  <g key={tick} transform={`translate(${x(tick)},0)`}>
                    <line y1={0} y2={5} stroke="var(--rehearse-rule)" />
                    <text y={20} textAnchor="middle" fill="var(--rehearse-copy-muted)" fontSize={13}>
                      {tick > 0 ? `+${tick}` : tick}
                    </text>
                  </g>
                ))}
                <text
                  x={innerWidth}
                  y={35}
                  textAnchor="end"
                  fill="var(--rehearse-copy-muted)"
                  fontSize={13}
                >
                  worse than control &rarr;
                </text>
              </g>
            </g>
          );
        }}
      </Chart>

      <ul className="widget-legend">
        {([
          ['act', 'Act on it: every seed agrees, mean clears your threshold'],
          ['under', 'Consistent, but the mean is inside your threshold'],
          ['flipped', 'Sign flips between seeds: no result at any threshold'],
        ] as [Verdict, string][]).map(([verdict, text]) => (
          <li key={verdict}>
            <svg width="26" height="12" aria-hidden="true">
              <line x1={1} x2={25} y1={6} y2={6} stroke={STROKE[verdict]} strokeWidth={2} opacity={0.45} />
              <circle cx={13} cy={6} r={3.5} fill="var(--rehearse-warm-white)" stroke={STROKE[verdict]} strokeWidth={1.6} />
            </svg>
            {text}
          </li>
        ))}
      </ul>

      <div className="objective-readout">
        <div>
          <span>Arms you would act on</span>
          <strong>{acted} of {ARMS.length}</strong>
        </div>
        <div>
          <span>Consistent but under threshold</span>
          <strong>{under}</strong>
        </div>
        <div>
          <span>Sign flips between seeds</span>
          <strong>{flipped}</strong>
        </div>
      </div>

      <p className="widget-caption">
        {threshold < FLOOR ? (
          <>
            Below the measured floor of {FLOOR.toFixed(3)}. Six replications of one
            unchanged configuration spread by 0.0018 on this hardware, so a threshold
            this low ranks arms on the memory allocator as much as on the architecture.
          </>
        ) : marginal ? (
          <>
            <strong>{marginal.arm.rung}: {marginal.arm.change}</strong> is the closest
            call you are still acting on, at a mean of {marginal.mean.toFixed(4)}.
            {' '}
            {flipped} arms never reach any threshold — their sign flips between seeds,
            and no amount of lowering the bar makes an inconsistent direction into a result.
          </>
        ) : (
          <>
            Nothing on the ladder clears {threshold.toFixed(4)}. The largest effect
            measured here, RoPE against no positional information at all, is 0.1051.
          </>
        )}
      </p>

      <p>
        The floor is not an assumption. It is the six times this ladder ran the
        same configuration by accident, because the control appears in every rung:
        identical seeds, identical batches, identical code, and a 0.0018 spread in
        the answer. That is the resolution the hardware gives you, and it is why
        the norm and activation rungs are reported as no result rather than as a
        narrow win.
      </p>
    </div>
  );
}
