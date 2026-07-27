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

const MAX_STRATEGIES = 500;
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
  const [numStrategies, setNumStrategies] = useState(20);
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

  useEffect(() => {
    if (!playing) return;
    if (reducedMotion.current) {
      setNumStrategies(MAX_STRATEGIES);
      setPlaying(false);
      return;
    }
    const id = setInterval(() => {
      setNumStrategies((current) => {
        const next = current + 6;
        if (next >= MAX_STRATEGIES) {
          setPlaying(false);
          return MAX_STRATEGIES;
        }
        return next;
      });
    }, 90);
    return () => clearInterval(id);
  }, [playing]);

  const current = cumulative[numStrategies - 1];
  const visible = cumulative.slice(0, numStrategies);

  const width = 300;
  const height = 130;
  const margin = { left: 4, right: 4, top: 10, bottom: 10 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;

  const xFor = (n: number) => margin.left + ((n - 1) / (MAX_STRATEGIES - 1)) * plotWidth;
  const yFor = (v: number) =>
    margin.top + (1 - (v - yDomain.min) / (yDomain.max - yDomain.min)) * plotHeight;

  const inSamplePath = visible.map((p) => `${xFor(p.n)},${yFor(p.bestInSample)}`).join(' ');
  const outOfSamplePath = visible.map((p) => `${xFor(p.n)},${yFor(p.outOfSampleOfBest)}`).join(' ');
  const zeroY = yFor(0);

  return (
    <div className="learning-widget">
      <p style={{ marginTop: 0, fontSize: 'var(--type-xs)', color: 'var(--rehearse-copy-muted)' }}>
        Simulated: {MAX_STRATEGIES} independent seeded noise series, not market data.
      </p>

      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '0.9rem' }}>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span>Strategies tried <strong>{numStrategies}</strong></span>
          <input
            type="range"
            min={1}
            max={MAX_STRATEGIES}
            value={numStrategies}
            onChange={(event) => {
              setPlaying(false);
              setNumStrategies(Number(event.target.value));
            }}
            style={{ width: 160 }}
            aria-label="Number of strategies tried against the same history"
          />
        </label>
        <button
          onClick={() => setPlaying((p) => !p)}
          style={{ padding: '0.45rem 0.8rem', borderRadius: 6, cursor: 'pointer', minHeight: '44px' }}
        >
          {playing ? 'Pause' : numStrategies >= MAX_STRATEGIES ? 'Replay from 1' : 'Try more strategies'}
        </button>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-hidden="true"
        style={{ width: '100%', height: 'auto', display: 'block' }}
      >
        <line
          x1={margin.left}
          x2={width - margin.right}
          y1={zeroY}
          y2={zeroY}
          stroke="var(--rehearse-rule)"
          strokeWidth={1}
          strokeDasharray="3,3"
        />
        <polyline
          points={inSamplePath}
          fill="none"
          stroke="var(--brand-chart-danger)"
          strokeWidth={2}
          vectorEffect="non-scaling-stroke"
        />
        <polyline
          points={outOfSamplePath}
          fill="none"
          stroke="var(--brand-chart-action)"
          strokeWidth={2}
          vectorEffect="non-scaling-stroke"
        />
        {current && (
          <>
            <circle cx={xFor(current.n)} cy={yFor(current.bestInSample)} r={3} fill="var(--brand-chart-danger)" />
            <circle cx={xFor(current.n)} cy={yFor(current.outOfSampleOfBest)} r={3} fill="var(--brand-chart-action)" />
          </>
        )}
      </svg>

      <div style={{ display: 'flex', gap: '1.4rem', fontSize: 'var(--type-sm)', marginTop: '0.6rem', flexWrap: 'wrap' }}>
        <span>
          <span style={{ color: 'var(--brand-chart-danger)' }}>&#9632;</span>{' '}
          best in-sample Sharpe of {numStrategies} tried: <strong>{current?.bestInSample.toFixed(2)}</strong>
        </span>
        <span>
          <span style={{ color: 'var(--brand-chart-action)' }}>&#9632;</span>{' '}
          that same pick's out-of-sample Sharpe: <strong>{current?.outOfSampleOfBest.toFixed(2)}</strong>
        </span>
      </div>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.7rem' }}>
        The red line climbs because it is the maximum of more and more independent
        draws — sampling harder, not discovering skill. The blue line is that
        exact same strategy's result on data it was never selected against, and
        it stays flat because the noise in each strategy's two windows is
        independent by construction. Walk-forward validation, purging, and the
        deflated Sharpe ratio exist because this gap is invisible from the red
        line alone.
      </p>
    </div>
  );
}
