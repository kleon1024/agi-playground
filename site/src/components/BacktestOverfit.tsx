/**
 * Why "we tried 200 strategies and this one has a Sharpe of 2.1" proves nothing.
 *
 * Every series in this widget is deterministic pseudo-random noise, seeded so
 * it reproduces exactly — never market data. That is the whole point: nothing
 * underneath any of these "strategies" has any real edge, by construction. As
 * the number of strategies tried (N) grows, the best in-sample result among
 * them climbs, because a maximum over more independent draws is mechanically
 * larger almost regardless of the underlying distribution. The same
 * strategy's out-of-sample result does not climb with it, because its
 * in-sample and out-of-sample windows are independent noise draws with no
 * shared skill to have selected on in the first place. That gap between a
 * rising in-sample line and a flat out-of-sample line is backtest
 * overfitting, and it appears from multiple testing alone — before a single
 * real trade, or a single genuine edge, ever enters the picture.
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { scaleLinear } from 'd3-scale';
import { line as d3line } from 'd3-shape';

import Chart from './chart/Chart';
import { useFrameLoop } from './useMotionClock';

const MAX_STRATEGIES = 500;
const HEIGHT = 210;
const PADDING = { top: 24, right: 14, bottom: 34, left: 40 };
/** The line that climbs is the one that misleads, so it carries the emphasis. */
const IN_SAMPLE = 'var(--rehearse-emphasis)';
const OUT_OF_SAMPLE = 'var(--rehearse-action)';
const DAYS_IN_SAMPLE = 120;
const DAYS_OUT_OF_SAMPLE = 120;
const DAILY_VOL = 0.012; // roughly a single-stock daily volatility
const SEED = 20260427;

// A tiny deterministic PRNG (mulberry32) so the "market" is reproducible —
// same seed, same numbers, every reader who loads this page.
function mulberry32(seed: number): () => number {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gaussian(rand: () => number): number {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

function annualizedSharpe(returns: number[]): number {
  const n = returns.length;
  const mean = returns.reduce((sum, r) => sum + r, 0) / n;
  const variance = returns.reduce((sum, r) => sum + (r - mean) ** 2, 0) / (n - 1);
  const std = Math.sqrt(variance);
  return std === 0 ? 0 : (mean / std) * Math.sqrt(252);
}

interface Strategy {
  inSample: number;
  outOfSample: number;
}

interface CumulativePoint {
  n: number;
  bestInSample: number;
  outOfSampleOfBest: number;
}

export default function BacktestOverfit(): React.ReactElement {
  /* Starts at the full pool, not at 20: the static reading has to be the finished
     comparison. At 20 of 500 the plot is a stub in the left 4% of the frame, which
     is what a reader with reduced motion or no JavaScript would be left with. */
  const [numStrategies, setNumStrategies] = useState(MAX_STRATEGIES);
  const [playing, setPlaying] = useState(false);
  const reducedMotion = useRef(false);

  useEffect(() => {
    reducedMotion.current =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }, []);

  // Draw the full pool of strategies once. Every strategy is pure noise with
  // no relationship between its in-sample and out-of-sample window — none of
  // them has, or could have, a real edge.
  const strategies = useMemo<Strategy[]>(() => {
    const rand = mulberry32(SEED);
    const pool: Strategy[] = [];
    for (let i = 0; i < MAX_STRATEGIES; i++) {
      const inSampleReturns = Array.from({ length: DAYS_IN_SAMPLE }, () => gaussian(rand) * DAILY_VOL);
      const outOfSampleReturns = Array.from({ length: DAYS_OUT_OF_SAMPLE }, () => gaussian(rand) * DAILY_VOL);
      pool.push({
        inSample: annualizedSharpe(inSampleReturns),
        outOfSample: annualizedSharpe(outOfSampleReturns),
      });
    }
    return pool;
  }, []);

  // For every N, track the best in-sample Sharpe found among the first N
  // strategies, and that SAME strategy's out-of-sample Sharpe — the contrast
  // this widget exists to show.
  const cumulative = useMemo<CumulativePoint[]>(() => {
    let bestIndex = 0;
    return strategies.map((strategy, index) => {
      if (strategy.inSample > strategies[bestIndex].inSample) bestIndex = index;
      return {
        n: index + 1,
        bestInSample: strategies[bestIndex].inSample,
        outOfSampleOfBest: strategies[bestIndex].outOfSample,
      };
    });
  }, [strategies]);

  const yDomain = useMemo(() => {
    const values = cumulative.flatMap((p) => [p.bestInSample, p.outOfSampleOfBest]);
    const min = Math.min(0, ...values);
    const max = Math.max(0, ...values);
    const pad = (max - min) * 0.12 || 0.5;
    return { min: min - pad, max: max + pad };
  }, [cumulative]);

  /* Reduced motion asks for no animation, not for no answer: pressing the button
     jumps straight to the full pool rather than sweeping to it. */
  useEffect(() => {
    if (playing && reducedMotion.current) {
      setNumStrategies(MAX_STRATEGIES);
      setPlaying(false);
    }
  }, [playing]);

  useFrameLoop(playing, (dt) => {
    setNumStrategies((n) => {
      const next = Math.min(MAX_STRATEGIES, n + Math.max(1, Math.round(dt / 15)));
      if (next >= MAX_STRATEGIES) setPlaying(false);
      return next;
    });
  });

  const current = cumulative[numStrategies - 1];
  const visible = cumulative.slice(0, numStrategies);

  return (
    <div className="learning-widget">
      <p>
        Simulated: {MAX_STRATEGIES} independent seeded noise series, not market data. Try more
        of them against the same history and watch which of the two lines moves.
      </p>

      <div className="widget-controls">
        <label>
          <span>Strategies tried</span>
          <input
            type="range"
            min={1}
            max={MAX_STRATEGIES}
            value={numStrategies}
            onChange={(event) => {
              setPlaying(false);
              setNumStrategies(Number(event.target.value));
            }}
            aria-label="Number of strategies tried against the same history"
          />
          <strong>{numStrategies}</strong>
        </label>
        <button
          type="button"
          onClick={() => {
            /* The label promised a replay from 1 and the toggle alone never
               delivered one: at the full pool the loop starts and stops on the
               same frame. Rewind first. */
            if (!playing && numStrategies >= MAX_STRATEGIES) setNumStrategies(1);
            setPlaying((p) => !p);
          }}
        >
          {playing ? 'Pause' : numStrategies >= MAX_STRATEGIES ? 'Replay from 1' : 'Try more strategies'}
        </button>
      </div>

      <ul className="widget-legend">
        <li>
          <svg width="26" height="8" aria-hidden="true">
            <line x1="0" y1="4" x2="26" y2="4" stroke={IN_SAMPLE} strokeWidth="2.5" />
          </svg>
          Best in-sample Sharpe <span>of the {numStrategies} tried</span>
        </li>
        <li>
          <svg width="26" height="8" aria-hidden="true">
            <line
              x1="0"
              y1="4"
              x2="26"
              y2="4"
              stroke={OUT_OF_SAMPLE}
              strokeWidth="2.5"
              strokeDasharray="6 4"
            />
          </svg>
          That same pick out of sample <span>data it was never selected against</span>
        </li>
      </ul>

      <Chart
        height={HEIGHT}
        padding={PADDING}
        label="Best in-sample Sharpe and the same strategy's out-of-sample Sharpe, against the number of strategies tried"
      >
        {(frame) => {
          const { innerWidth, innerHeight } = frame;
          const x = scaleLinear().domain([1, MAX_STRATEGIES]).range([0, innerWidth]);
          const y = scaleLinear().domain([yDomain.min, yDomain.max]).range([innerHeight, 0]);
          const path = (key: 'bestInSample' | 'outOfSampleOfBest') =>
            d3line<CumulativePoint>().x((p) => x(p.n)).y((p) => y(p[key]))(visible) ?? undefined;

          return (
            <g transform={`translate(${PADDING.left},${PADDING.top})`}>
              {[-1, 0, 1, 2, 3, 4].filter((t) => t > yDomain.min && t < yDomain.max).map((tick) => (
                <g key={tick}>
                  <line
                    x1={0}
                    x2={innerWidth}
                    y1={y(tick)}
                    y2={y(tick)}
                    stroke="var(--rehearse-rule)"
                    strokeDasharray={tick === 0 ? undefined : '3 3'}
                  />
                  <text
                    x={-8}
                    y={y(tick) + 4}
                    textAnchor="end"
                    fill="var(--rehearse-copy-muted)"
                    fontSize={13}
                  >
                    {tick}
                  </text>
                </g>
              ))}

              <path d={path('bestInSample')} fill="none" stroke={IN_SAMPLE} strokeWidth={2} />
              <path
                d={path('outOfSampleOfBest')}
                fill="none"
                stroke={OUT_OF_SAMPLE}
                strokeWidth={2}
                strokeDasharray="6 4"
              />
              {current && (
                <>
                  <circle cx={x(current.n)} cy={y(current.bestInSample)} r={4} fill={IN_SAMPLE} />
                  <circle cx={x(current.n)} cy={y(current.outOfSampleOfBest)} r={4} fill={OUT_OF_SAMPLE} />
                </>
              )}

              <text x={0} y={innerHeight + 22} fill="var(--rehearse-copy-muted)" fontSize={13}>
                1 strategy
              </text>
              <text
                x={innerWidth}
                y={innerHeight + 22}
                textAnchor="end"
                fill="var(--rehearse-copy-muted)"
                fontSize={13}
              >
                {MAX_STRATEGIES} tried &rarr;
              </text>
              <text
                x={-PADDING.left}
                y={-8}
                fill="var(--rehearse-copy-muted)"
                fontSize={13}
              >
                Sharpe
              </text>
            </g>
          );
        }}
      </Chart>

      <div className="objective-readout">
        <div>
          <span>Best in-sample Sharpe</span>
          <strong>{current?.bestInSample.toFixed(2)}</strong>
        </div>
        <div>
          <span>Same pick, out of sample</span>
          <strong>{current?.outOfSampleOfBest.toFixed(2)}</strong>
        </div>
        <div>
          <span>Gap the selection bought</span>
          <strong>
            {current ? (current.bestInSample - current.outOfSampleOfBest).toFixed(2) : '—'}
          </strong>
        </div>
      </div>

      <p className="widget-caption">
        The solid line climbs because it is the maximum of more and more independent
        draws — sampling harder, not discovering skill. The dashed line is that
        exact same strategy&rsquo;s result on data it was never selected against. It does
        not climb with the solid one; it steps to whatever the new pick happened to score
        on a window nobody sorted, because the noise in each strategy&rsquo;s two windows is
        independent by construction. At 50 strategies it reads 1.12 and at 500 it reads
        0.06 &mdash; movement without direction. The third readout is the whole distance
        between the two lines: it is not edge, it is what the selection bought.
        Walk-forward validation, purging, and the deflated Sharpe ratio exist because that
        gap is invisible from the solid line alone.
      </p>
    </div>
  );
}
