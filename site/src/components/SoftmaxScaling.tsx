/**
 * Why attention divides by sqrt(d_k), demonstrated rather than asserted.
 *
 * The argument in prose is: if query and key entries are independent unit
 * Gaussians, their dot product sums d_k unit-variance terms, so scores scale
 * like sqrt(d_k). At d_k = 64 raw scores routinely reach ±16, and softmax of
 * numbers that far apart is a one-hot vector — which means near-zero gradient
 * for every position that is not the argmax.
 *
 * That is a lot of words for something a slider settles in two seconds. Drag
 * d_k up with scaling off and watch the distribution collapse; turn scaling on
 * and watch it stay a distribution.
 */
import React, { useMemo, useState } from 'react';

/** Deterministic normal samples, so the demo does not reshuffle on every keystroke. */
function gaussians(n: number, seed: number): number[] {
  let s = seed;
  const rand = () => {
    // Mulberry32 — small, deterministic, good enough for a visual.
    s |= 0;
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const out: number[] = [];
  for (let i = 0; i < n; i++) {
    // Box-Muller
    const u = Math.max(rand(), 1e-9);
    const v = rand();
    out.push(Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v));
  }
  return out;
}

function softmax(xs: number[]): number[] {
  const m = Math.max(...xs);
  const e = xs.map((x) => Math.exp(x - m));
  const sum = e.reduce((a, b) => a + b, 0);
  return e.map((x) => x / sum);
}

const KEYS = 8;

export default function SoftmaxScaling(): React.ReactElement {
  const [dk, setDk] = useState(64);
  const [scaled, setScaled] = useState(false);

  const { scores, probs, entropy, maxProb } = useMemo(() => {
    // One query against KEYS keys, each a d_k-dimensional unit Gaussian vector.
    const q = gaussians(dk, 12345);
    const raw: number[] = [];
    for (let k = 0; k < KEYS; k++) {
      const key = gaussians(dk, 999 + k * 7919);
      raw.push(q.reduce((acc, qi, i) => acc + qi * key[i], 0));
    }
    const s = scaled ? raw.map((x) => x / Math.sqrt(dk)) : raw;
    const p = softmax(s);
    const H = -p.reduce((a, x) => a + (x > 0 ? x * Math.log(x) : 0), 0);
    return { scores: s, probs: p, entropy: H, maxProb: Math.max(...p) };
  }, [dk, scaled]);

  const maxEntropy = Math.log(KEYS);

  return (
    <div className="learning-widget">
      <div
        style={{
          display: 'flex',
          gap: '1.5rem',
          alignItems: 'center',
          flexWrap: 'wrap',
          marginBottom: '1rem',
        }}
      >
        <label style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          <span style={{ minWidth: '3.2rem' }}>
            d<sub>k</sub> = <strong>{dk}</strong>
          </span>
          <input
            type="range"
            min={1}
            max={512}
            step={1}
            value={dk}
            onChange={(e) => setDk(Number(e.target.value))}
            style={{ width: 190 }}
          />
        </label>
        <label style={{ cursor: 'pointer', userSelect: 'none' }}>
          <input
            type="checkbox"
            checked={scaled}
            onChange={(e) => setScaled(e.target.checked)}
          />{' '}
          divide by √d<sub>k</sub>
        </label>
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 150 }}>
        {probs.map((p, i) => (
          <div key={i} style={{ flex: 1, textAlign: 'center' }}>
            <div
              title={`score ${scores[i].toFixed(2)} → p ${p.toFixed(4)}`}
              style={{
                height: `${Math.max(p * 130, 1.5)}px`,
                background: p > 0.9 ? 'var(--brand-chart-danger-fill)' : 'var(--brand-chart-positive-fill)',
                borderRadius: '3px 3px 0 0',
                transition: 'height 120ms ease-out, background 120ms',
              }}
            />
            <div style={{ fontSize: 'var(--type-xs)', opacity: 0.65, marginTop: 3 }}>
              {scores[i].toFixed(1)}
            </div>
          </div>
        ))}
      </div>

      <div
        style={{
          display: 'flex',
          gap: '1.5rem',
          fontSize: 'var(--type-sm)',
          marginTop: '0.75rem',
          flexWrap: 'wrap',
        }}
      >
        <span>
          largest weight <strong>{(maxProb * 100).toFixed(1)}%</strong>
        </span>
        <span>
          entropy <strong>{entropy.toFixed(2)}</strong> / {maxEntropy.toFixed(2)}
        </span>
        <span style={{ color: maxProb > 0.9 ? 'var(--brand-chart-danger)' : 'inherit' }}>
          {maxProb > 0.9
            ? 'saturated — one position takes everything, gradients vanish elsewhere'
            : 'a genuine distribution over positions'}
        </span>
      </div>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.75rem' }}>
        Eight keys, one query, entries drawn as unit Gaussians. Raise d
        <sub>k</sub> with scaling <strong>off</strong> and the distribution
        collapses onto a single position — softmax of scores spread ±√d
        <sub>k</sub> apart is effectively one-hot, so every other position
        receives almost no gradient. Turn scaling <strong>on</strong> and the
        variance stays fixed at 1 regardless of d<sub>k</sub>, which is the
        entire reason the division is in the formula.
      </p>
    </div>
  );
}
