/**
 * The DPO family as one plot, not three unrelated papers.
 *
 * DPO, IPO, and SimPO get taught as separate algorithms with separate names,
 * which hides how close together they actually sit: each is a loss function
 * over the same quantity — an implicit reward margin between a preferred and
 * a dispreferred completion — and they differ by what shape that loss takes,
 * not by what they are optimising for. DPO runs the margin through a
 * log-sigmoid (unbounded, pushes the margin toward +∞ forever). IPO replaces
 * that with a bounded quadratic that targets a finite margin instead of
 * infinity, which is precisely the fix for DPO's tendency to overfit preference
 * pairs. SimPO drops the reference model from the margin itself and shifts
 * the same log-sigmoid by a target-margin threshold γ. Same family, one knob
 * of difference each time.
 *
 * The second misconception this kills: DPO is not "RL without RL." It is the
 * closed-form solution to the KL-regularised reward-maximisation objective,
 * derived under a specific assumption — that preferences follow a
 * Bradley-Terry model and that the implicit reward is exactly β · log(π/π_ref).
 * That assumption is where DPO's limits come from: violate it (noisy labels,
 * non-transitive preferences, rewards that were never pairwise to begin with)
 * and the closed form is quietly solving the wrong problem, RL loop or not.
 */
import React, { useState } from 'react';
import { scaleLinear } from 'd3-scale';
import { line as d3line } from 'd3-shape';

import Chart, { type Frame } from './chart/Chart';

const X_MIN = -4;
const X_MAX = 4;
const Y_MAX = 6;
const HEIGHT = 230;
const PADDING = { top: 12, right: 14, bottom: 36, left: 34 };
const STEPS = 80;

/** Solid, dashed, dotted, so the three curves stay apart without colour. */
const CURVES = [
  { key: 'dpo', label: 'DPO', formula: 'L(h) = −log σ(β·h)', colour: 'var(--rehearse-action)', dash: undefined },
  { key: 'ipo', label: 'IPO', formula: 'L(h) = (β·h − 1)²', colour: 'var(--rehearse-emphasis)', dash: '7 4' },
  { key: 'simpo', label: 'SimPO', formula: 'L(h) = −log σ(β·h − γ)', colour: 'var(--rehearse-success)', dash: '2 4' },
] as const;

function sigmoid(z: number): number {
  return 1 / (1 + Math.exp(-z));
}

function safeLog(p: number): number {
  return Math.log(Math.max(p, 1e-6));
}

const scales = (frame: Frame) => ({
  x: scaleLinear().domain([X_MIN, X_MAX]).range([0, frame.innerWidth]),
  y: scaleLinear().domain([0, Y_MAX]).range([frame.innerHeight, 0]),
});

/**
 * Samples the loss across the axis. Values above the plotted range are dropped
 * rather than clamped: a clamped IPO curve draws as a flat line along the top
 * of the frame, which reads as "the loss is constant here" when it is in fact
 * climbing off the chart.
 */
function buildPath(fn: (x: number) => number, frame: Frame): string | undefined {
  const { x, y } = scales(frame);
  const points = Array.from({ length: STEPS + 1 }, (_, i) => {
    const h = X_MIN + ((X_MAX - X_MIN) * i) / STEPS;
    return [h, fn(h)] as [number, number];
  });
  return d3line<[number, number]>()
    .defined((p) => p[1] >= 0 && p[1] <= Y_MAX)
    .x((p) => x(p[0]))
    .y((p) => y(p[1]))(points) ?? undefined;
}

export default function DPOLossFamily(): React.ReactElement {
  const [beta, setBeta] = useState(1);
  const [gamma, setGamma] = useState(0.5);

  const dpo = (h: number) => -safeLog(sigmoid(beta * h));
  const ipo = (h: number) => (beta * h - 1) ** 2;
  const simpo = (h: number) => -safeLog(sigmoid(beta * h - gamma));

  const fns: Record<string, (h: number) => number> = { dpo, ipo, simpo };

  return (
    <div className="learning-widget">
      <div className="widget-controls">
        <label>
          <span>β</span>
          <input
            type="range"
            min={0.1}
            max={5}
            step={0.1}
            value={beta}
            onChange={(e) => setBeta(Number(e.target.value))}
          />
          <strong>{beta.toFixed(1)}</strong>
        </label>
        <label>
          <span>SimPO γ</span>
          <input
            type="range"
            min={0}
            max={2}
            step={0.1}
            value={gamma}
            onChange={(e) => setGamma(Number(e.target.value))}
          />
          <strong>{gamma.toFixed(1)}</strong>
        </label>
      </div>

      <ul className="widget-legend">
        {CURVES.map((c) => (
          <li key={c.key}>
            <svg width="26" height="8" aria-hidden="true">
              <line
                x1="0"
                y1="4"
                x2="26"
                y2="4"
                stroke={c.colour}
                strokeWidth="2.5"
                strokeDasharray={c.dash}
              />
            </svg>
            {c.label} <span>{c.formula}</span>
          </li>
        ))}
      </ul>

      <Chart
        height={HEIGHT}
        padding={PADDING}
        label="DPO, IPO and SimPO loss against the preference margin"
      >
        {(frame) => {
          const { innerWidth, innerHeight } = frame;
          const { x, y } = scales(frame);
          return (
            <g transform={`translate(${PADDING.left},${PADDING.top})`}>
              <line x1={0} x2={0} y1={0} y2={innerHeight} stroke="var(--rehearse-rule)" />
              <line x1={0} x2={innerWidth} y1={innerHeight} y2={innerHeight} stroke="var(--rehearse-rule)" />
              <line
                x1={x(0)}
                x2={x(0)}
                y1={0}
                y2={innerHeight}
                stroke="var(--rehearse-rule)"
                strokeDasharray="3 3"
              />
              {[Y_MAX, 0].map((tick) => (
                <text
                  key={tick}
                  x={-8}
                  y={y(tick) + (tick === 0 ? 0 : 10)}
                  textAnchor="end"
                  fill="var(--rehearse-copy-muted)"
                  fontSize={13}
                >
                  {tick}
                </text>
              ))}
              <text
                x={x(0)}
                y={innerHeight + 20}
                textAnchor="middle"
                fill="var(--rehearse-copy-muted)"
                fontSize={13}
              >
                h=0
              </text>
              <text
                x={innerWidth}
                y={innerHeight + 20}
                textAnchor="end"
                fill="var(--rehearse-copy-muted)"
                fontSize={13}
              >
                margin h &rarr;
              </text>

              {CURVES.map((c) => (
                <path
                  key={c.key}
                  d={buildPath(fns[c.key], frame)}
                  fill="none"
                  stroke={c.colour}
                  strokeWidth={2}
                  strokeDasharray={c.dash}
                />
              ))}
            </g>
          );
        }}
      </Chart>

      <p className="widget-caption">
        h is the implicit margin between the preferred and dispreferred
        completion — for DPO and IPO that is β times a log-probability ratio
        difference against a frozen reference model; SimPO computes the same
        kind of margin with no reference model at all, then subtracts its own
        target γ before the sigmoid. Raise β and all three curves sharpen,
        because β is the knob controlling how hard any of them punishes a
        small margin. Notice DPO&rsquo;s solid blue curve keeps falling forever as h
        grows — nothing stops it from pushing the margin to infinity, which is
        the overfitting behaviour IPO&rsquo;s dashed red bowl is built to prevent;
        the bowl leaves the top of the frame on both sides rather than flattening
        against it, because the loss keeps climbing past what is plotted.
        (IPO's actual paper parameterises its target margin as 1/(2β) in raw
        log-ratio space; it is plotted here on the same β-scaled axis as the
        other two so the three curves stay directly comparable.) None of this
        is "RL without RL" — it is RL's closed-form solution under the
        Bradley-Terry assumption, and everywhere that assumption breaks is
        exactly where DPO-family methods break too.
      </p>
    </div>
  );
}
