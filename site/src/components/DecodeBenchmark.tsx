/**
 * The measured decode benchmark that inverts the expected story.
 *
 * Recomputing the whole prefix every step is quadratic work, so the KV
 * cache's advantage should widen as sequences grow — instead it shrinks and
 * then inverts: at 512 new tokens the cached engine is slower than the naive
 * one (0.92x). The naive row explains why: it rises from 104.7 to 132.8
 * tok/s as sequences lengthen, which an engine limited by the quadratic work
 * it redoes could not do. The bottleneck is the rate at which decode steps
 * can be issued, not arithmetic.
 *
 * Every value is transcribed from
 * 01-language-model/05-serve/runs/2026-07-29-engine-bench-corrected.md
 * (one request, greedy decoding, stage-03 chat checkpoint). Nothing between
 * the five measured lengths is interpolated — the marker snaps to measured
 * points.
 */
import React, { useState } from 'react';
import { scaleLinear } from 'd3-scale';
import { line as d3line } from 'd3-shape';

import Chart, { type Frame } from './chart/Chart';

interface Point {
  tokens: number;
  naive: number;
  cache: number;
}

const ROWS: Point[] = [
  { tokens: 32, naive: 104.7, cache: 126.6 },
  { tokens: 64, naive: 112.3, cache: 126.3 },
  { tokens: 128, naive: 117.5, cache: 123.8 },
  { tokens: 256, naive: 119.7, cache: 120.6 },
  { tokens: 512, naive: 132.8, cache: 122.2 },
];

const HEIGHT = 250;
const PADDING = { top: 18, right: 14, bottom: 44, left: 48 };
const Y_LO = 100;
const Y_HI = 135;

const scales = (frame: Frame) => ({
  x: scaleLinear().domain([ROWS[0].tokens, ROWS[ROWS.length - 1].tokens]).range([0, frame.innerWidth]),
  y: scaleLinear().domain([Y_LO, Y_HI]).range([frame.innerHeight, 0]),
});

export default function DecodeBenchmark(): React.ReactElement {
  const [i, setI] = useState(ROWS.length - 1);
  const at = ROWS[i];
  const speedup = at.cache / at.naive;

  const caption = (() => {
    if (speedup >= 1) {
      return `${at.tokens} new tokens: the cache wins at ${speedup.toFixed(2)}x. The advantage over recomputing the prefix is real here — the naive engine redoes the whole sequence every step.`;
    }
    return `${at.tokens} new tokens: the cache loses at ${speedup.toFixed(2)}x. The naive engine now extracts more arithmetic per kernel launch — each launch covers the whole sequence — than the cached engine saves by keeping keys and values.`;
  })();

  return (
    <div className="learning-widget">
      <p>
        One request, greedy decoding, the stage-03 chat checkpoint. Point at a
        length or drag the slider and read the speedup — and notice the naive
        row rising as sequences lengthen, which is the signature of a
        launch-rate bottleneck rather than an arithmetic one.
      </p>

      <ul className="widget-legend">
        <li>
          <svg width="26" height="8" aria-hidden="true">
            <line x1="0" y1="4" x2="26" y2="4" stroke="var(--rehearse-action)" strokeWidth="2.5" />
          </svg>
          KV cache
        </li>
        <li>
          <svg width="26" height="8" aria-hidden="true">
            <line x1="0" y1="4" x2="26" y2="4" stroke="var(--rehearse-caution)" strokeWidth="2.5" strokeDasharray="6 4" />
          </svg>
          Naive recompute <span>full prefix every step</span>
        </li>
      </ul>

      <Chart
        height={HEIGHT}
        padding={PADDING}
        label="Decode throughput in tokens per second against new tokens generated, for the naive and KV-cache engines"
        onPointerAt={(x, frame) => {
          if (x === null) return;
          const tokens = scales(frame).x.invert(x);
          setI(
            ROWS.reduce((best, p, n) =>
              Math.abs(p.tokens - tokens) < Math.abs(ROWS[best].tokens - tokens) ? n : best, 0),
          );
        }}
      >
        {(frame) => {
          const s = scales(frame);
          const make = (key: 'naive' | 'cache') =>
            d3line<Point>()
              .x((p) => s.x(p.tokens))
              .y((p) => s.y(p[key]))(ROWS) ?? '';
          return (
            <>
              {[32, 64, 128, 256, 512].map((t) => (
                <line
                  key={t}
                  x1={s.x(t)}
                  x2={s.x(t)}
                  y1={0}
                  y2={frame.innerHeight}
                  stroke="var(--rehearse-rule)"
                  strokeDasharray="2 4"
                />
              ))}
              <path d={make('cache')} fill="none" stroke="var(--rehearse-action)" strokeWidth="2.5" />
              <path d={make('naive')} fill="none" stroke="var(--rehearse-caution)" strokeWidth="2.5" strokeDasharray="6 4" />
              <circle cx={s.x(at.tokens)} cy={s.y(at.cache)} r={4.5} fill="var(--rehearse-action)" />
              <circle cx={s.x(at.tokens)} cy={s.y(at.naive)} r={4.5} fill="var(--rehearse-caution)" />
              {ROWS.map((p) => (
                <text
                  key={p.tokens}
                  x={s.x(p.tokens)}
                  y={frame.innerHeight + 18}
                  textAnchor="middle"
                  fontSize="12"
                  fill="var(--rehearse-copy-muted)"
                >
                  {p.tokens}
                </text>
              ))}
              <text
                x={frame.innerWidth}
                y={frame.innerHeight + 18}
                textAnchor="end"
                fontSize="12"
                fill="var(--rehearse-copy-muted)"
              >
                new tokens
              </text>
            </>
          );
        }}
      </Chart>

      <label style={{ display: 'flex', gap: '0.8rem', alignItems: 'center', margin: '0.9rem 0' }}>
        <span style={{ minWidth: '9.5rem' }}>
          new tokens = <strong>{at.tokens}</strong>
        </span>
        <input
          type="range"
          min={0}
          max={ROWS.length - 1}
          step={1}
          value={i}
          onChange={(e) => setI(Number(e.target.value))}
          style={{ width: '100%', maxWidth: 260 }}
        />
      </label>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '0.6rem',
          marginBottom: '0.9rem',
        }}
      >
        {[
          ['Naive, tok/s', at.naive.toFixed(1)],
          ['KV cache, tok/s', at.cache.toFixed(1)],
          ['Speedup', `${speedup.toFixed(2)}x`],
        ].map(([label, value]) => (
          <div key={label} style={{ border: '1px solid var(--rehearse-rule)', padding: '0.5rem 0.65rem' }}>
            <div style={{ fontSize: 'var(--type-xs)', opacity: 0.65 }}>{label}</div>
            <div style={{ fontWeight: 600 }}>{value}</div>
          </div>
        ))}
      </div>

      <p>{caption}</p>

      <p>
        The cache is not useless — the asymptotics are real. It is that this
        scale does not reach them: at batch 1 the fixed per-step cost of
        issuing a few hundred tiny kernel launches dominates, and graph
        execution (513 launches per decode step, host time 6.87x device time)
        is where the 3x actually lives. The benchmark's job is to stop a
        serving team from claiming a speedup it did not measure — which is why
        this record exists at all: the first version of this benchmark
        attended to position 0 alone, flattered the cache, and had to be
        re-measured.
      </p>
    </div>
  );
}
