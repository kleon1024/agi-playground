/**
 * Why "one run per arm" cannot answer a data-mixture question.
 *
 * Two arms — a baseline mixture and a candidate — each produce a score that
 * varies with nothing but their random seed, because everything else in the
 * comparison (architecture, token budget, evaluation set) is held fixed. At
 * one seed, whichever arm happened to score higher looks like a winner. The
 * only way to tell a real gap from seed noise is to run more seeds and watch
 * whether the gap survives being measured against its own spread.
 *
 * All numbers here are illustrative: a deterministic pseudo-random generator
 * stands in for training runs nobody has executed, so the display is stable
 * across reloads but is not a measured result. Nothing in this component
 * should be read next to this repository's actual runs as though they were
 * the same kind of number.
 */
import React, { useMemo, useState } from 'react';

const MAX_SEEDS = 24;
const ILLUSTRATIVE_MEAN_A = 42.0; // baseline mixture, illustrative eval score
const ILLUSTRATIVE_MEAN_B = 42.9; // candidate mixture, illustrative eval score
const ILLUSTRATIVE_SEED_SD = 2.6; // seed-to-seed spread, illustrative and larger than the gap
const Z95 = 1.96;

// Deterministic PRNG (mulberry32) so the illustrative samples are identical
// on every render and every reload, rather than reshuffling like Math.random.
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

function sampleArm(seedBase: number, mean: number): number[] {
  const rand = mulberry32(seedBase);
  return Array.from({ length: MAX_SEEDS }, () => mean + ILLUSTRATIVE_SEED_SD * gaussian(rand));
}

function mean(values: number[]): number {
  return values.reduce((a, b) => a + b, 0) / values.length;
}

export default function SeedVariance(): React.ReactElement {
  const [seeds, setSeeds] = useState(2);

  // Fixed once: the same 24 illustrative draws per arm regardless of how many
  // the slider currently shows, so raising the seed count reveals more of the
  // same run rather than resampling a fresh one.
  const armA = useMemo(() => sampleArm(1337, ILLUSTRATIVE_MEAN_A), []);
  const armB = useMemo(() => sampleArm(4242, ILLUSTRATIVE_MEAN_B), []);

  const { meanA, meanB, armMargin, diffMargin, diff, overlapsZero } = useMemo(() => {
    const a = armA.slice(0, seeds);
    const b = armB.slice(0, seeds);
    const mA = mean(a);
    const mB = mean(b);
    const se = ILLUSTRATIVE_SEED_SD / Math.sqrt(seeds); // same generating spread, same n, both arms
    const perArmMargin = Z95 * se; // each arm's own 95% band, shown on its bar
    const diffM = Z95 * Math.sqrt(se * se + se * se); // 95% margin on the difference itself
    const d = mB - mA;
    return {
      meanA: mA,
      meanB: mB,
      armMargin: perArmMargin,
      diffMargin: diffM,
      diff: d,
      overlapsZero: Math.abs(d) <= diffM,
    };
  }, [armA, armB, seeds]);

  const axisMin = 35;
  const axisMax = 50;
  const toPct = (v: number) => ((v - axisMin) / (axisMax - axisMin)) * 100;

  return (
    <div className="learning-widget">
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '0.9rem' }}>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          seeds per arm <strong>{seeds}</strong>
          <input
            type="range"
            min={1}
            max={MAX_SEEDS}
            step={1}
            value={seeds}
            onChange={(e) => setSeeds(Number(e.target.value))}
            style={{ width: 180 }}
            aria-label="seeds per arm"
          />
        </label>
        <span style={{ fontSize: 'var(--type-xs)', opacity: 0.7 }}>illustrative, not measured</span>
      </div>

      {(['A', 'B'] as const).map((arm) => {
        const m = arm === 'A' ? meanA : meanB;
        const label = arm === 'A' ? 'mixture A (baseline)' : 'mixture B (candidate)';
        const lo = toPct(m - armMargin);
        const hi = toPct(m + armMargin);
        const center = toPct(m);
        return (
          <div key={arm} style={{ marginBottom: '0.8rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--type-sm)' }}>
              <span>{label}</span>
              <strong>{m.toFixed(2)}</strong>
            </div>
            <div style={{ position: 'relative', height: 22, background: 'var(--rehearse-paper)', border: '1px solid var(--rehearse-rule)' }}>
              <div
                style={{
                  position: 'absolute',
                  left: `${Math.max(0, Math.min(100, lo))}%`,
                  width: `${Math.max(0, Math.min(100, hi) - Math.max(0, lo))}%`,
                  top: 0,
                  bottom: 0,
                  background: overlapsZero ? 'var(--brand-chart-warning-fill)' : 'var(--brand-chart-positive-fill)',
                  transition: 'left 200ms ease-out, width 200ms ease-out',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  left: `${Math.max(0, Math.min(100, center))}%`,
                  top: 0,
                  bottom: 0,
                  width: 2,
                  background: 'var(--rehearse-ink)',
                  transition: 'left 200ms ease-out',
                }}
              />
            </div>
          </div>
        );
      })}

      <div style={{ display: 'flex', gap: '1.2rem', fontSize: 'var(--type-sm)', flexWrap: 'wrap', marginTop: '0.6rem' }}>
        <span>apparent difference (B - A) <strong>{diff >= 0 ? '+' : ''}{diff.toFixed(2)}</strong></span>
        <span>95% margin on the difference <strong>&plusmn;{diffMargin.toFixed(2)}</strong></span>
        <span style={{ color: overlapsZero ? 'var(--brand-chart-warning)' : 'var(--brand-chart-positive)' }}>
          {overlapsZero
            ? `NOT DETECTABLE at ${seeds} seed${seeds === 1 ? '' : 's'}/arm`
            : `detectable at ${seeds} seeds/arm`}
        </span>
      </div>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.7rem' }}>
        Both bands are illustrative draws from the same underlying gap at every
        seed count — only how much of it you are allowed to look at changes.
        At one or two seeds the bands overlap and the apparent difference is
        an anecdote. Raise the seed count and the bands narrow around their
        true means; the same gap that looked like noise either survives as a
        real difference or was noise all along. This is the same seed-variance
        mechanism the evaluation chapter measures for scores, applied here to
        a training decision instead.
      </p>
    </div>
  );
}
