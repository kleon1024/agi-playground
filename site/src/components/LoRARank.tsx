/**
 * Low-rank adaptation, made concrete: two thin matrices instead of one big one.
 *
 * The pitch for LoRA is usually a sentence — "freeze W, learn a low-rank
 * update ΔW = B·A instead" — and the sentence hides the two things that
 * actually matter. First, the parameter count: a d×d matrix costs d² to
 * fine-tune, while B (d×r) and A (r×d) together cost 2dr, so the saving is
 * real only because r is kept far below d. Second, the initialisation: B
 * starts at exactly zero and A starts small-random, so at step 0 the product
 * B·A is the zero matrix and the adapter is a provable no-op — the base
 * model's output is untouched until gradients move B away from zero.
 *
 * The misconception this kills is "more rank = more quality." Rank is a
 * capacity knob, not a quality knob: past whatever a task actually needs, the
 * extra rank has nowhere useful to go, and dragging r high enough starts
 * eating the parameter savings that were the point of using LoRA at all.
 */
import React, { useMemo, useState } from 'react';

/** Deterministic normal samples — same trick as SoftmaxScaling, so the "A is
 * random" visual does not reshuffle on every render. */
function gaussians(n: number, seed: number): number[] {
  let s = seed;
  const rand = () => {
    s |= 0;
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const out: number[] = [];
  for (let i = 0; i < n; i++) {
    const u = Math.max(rand(), 1e-9);
    const v = rand();
    out.push(Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v));
  }
  return out;
}

function fmtCount(x: number): string {
  if (x >= 1e6) return `${(x / 1e6).toFixed(2)}M`;
  if (x >= 1e3) return `${(x / 1e3).toFixed(1)}K`;
  return `${Math.round(x)}`;
}

const VISUAL = 140; // px side representing the full d×d square
const GRID_ROWS = 5;
const GRID_COLS = 12;

export default function LoRARank(): React.ReactElement {
  const [d, setD] = useState(512);
  const [r, setR] = useState(8);
  const [alpha, setAlpha] = useState(16);

  const rMax = Math.min(d, 512);
  const rClamped = Math.min(r, rMax);

  const { fullParams, loraParams, ratio, scale } = useMemo(() => {
    const full = d * d;
    const lora = 2 * d * rClamped;
    return {
      fullParams: full,
      loraParams: lora,
      ratio: full / lora,
      scale: alpha / rClamped,
    };
  }, [d, rClamped, alpha]);

  // B and A rendered to scale against the full square, clamped so a thin
  // matrix never disappears entirely.
  const bWidth = Math.max(3, Math.round((VISUAL * rClamped) / d));
  const aHeight = Math.max(3, Math.round((VISUAL * rClamped) / d));

  const aInit = useMemo(() => gaussians(GRID_ROWS * GRID_COLS, 4242), []);
  const aMax = Math.max(...aInit.map((x) => Math.abs(x)));

  return (
    <div style={{ margin: '1.5rem 0' }}>
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
          <span style={{ minWidth: '5rem' }}>
            d = <strong>{d}</strong>
          </span>
          <input
            type="range"
            min={64}
            max={2048}
            step={64}
            value={d}
            onChange={(e) => setD(Number(e.target.value))}
            style={{ width: 170 }}
          />
        </label>
        <label style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          <span style={{ minWidth: '5rem' }}>
            rank r = <strong>{rClamped}</strong>
          </span>
          <input
            type="range"
            min={1}
            max={rMax}
            step={1}
            value={rClamped}
            onChange={(e) => setR(Number(e.target.value))}
            style={{ width: 170 }}
          />
        </label>
        <label style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
          <span style={{ minWidth: '5.5rem' }}>
            α = <strong>{alpha}</strong>
          </span>
          <input
            type="range"
            min={1}
            max={64}
            step={1}
            value={alpha}
            onChange={(e) => setAlpha(Number(e.target.value))}
            style={{ width: 130 }}
          />
        </label>
      </div>

      <div
        style={{
          display: 'flex',
          gap: '1.4rem',
          fontSize: '0.85rem',
          flexWrap: 'wrap',
          marginBottom: '1rem',
        }}
      >
        <span>full fine-tune <strong>{fmtCount(fullParams)}</strong> params</span>
        <span>LoRA <strong>{fmtCount(loraParams)}</strong> params</span>
        <span style={{ color: ratio >= 1 ? 'var(--brand-chart-positive)' : 'var(--brand-chart-danger)' }}>
          {ratio >= 1 ? `${ratio.toFixed(1)}× smaller` : `${(1 / ratio).toFixed(1)}× LARGER — r too high to save anything`}
        </span>
        <span>scale α/r = <strong>{scale.toFixed(2)}</strong></span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.4rem', flexWrap: 'wrap' }}>
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: VISUAL,
              height: VISUAL,
              background: 'var(--brand-chart-action-fill)',
              borderRadius: 4,
              opacity: 0.85,
            }}
          />
          <div style={{ fontSize: '0.7rem', opacity: 0.7, marginTop: 4 }}>
            W — {d}×{d}
          </div>
        </div>

        <span style={{ fontSize: '1.3rem', opacity: 0.6 }}>vs</span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ textAlign: 'center' }}>
            <div
              style={{
                width: bWidth,
                height: VISUAL,
                background: 'var(--brand-chart-positive-fill)',
                borderRadius: 3,
              }}
            />
            <div style={{ fontSize: '0.7rem', opacity: 0.7, marginTop: 4 }}>
              B — {d}×{rClamped}
            </div>
          </div>
          <span style={{ fontSize: '1.1rem', opacity: 0.6 }}>×</span>
          <div style={{ textAlign: 'center' }}>
            <div
              style={{
                width: VISUAL,
                height: aHeight,
                background: 'var(--brand-chart-danger-fill)',
                borderRadius: 3,
              }}
            />
            <div style={{ fontSize: '0.7rem', opacity: 0.7, marginTop: 4 }}>
              A — {rClamped}×{d}
            </div>
          </div>
          <span style={{ fontSize: '1.1rem', opacity: 0.6 }}>=</span>
          <div style={{ textAlign: 'center' }}>
            <div
              style={{
                width: VISUAL,
                height: VISUAL,
                border: '2px dashed var(--ifm-color-emphasis-400)',
                borderRadius: 4,
              }}
            />
            <div style={{ fontSize: '0.7rem', opacity: 0.7, marginTop: 4 }}>
              ΔW — rank ≤ {rClamped}
            </div>
          </div>
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          gap: '2rem',
          flexWrap: 'wrap',
          marginTop: '1.2rem',
          alignItems: 'flex-start',
        }}
      >
        <div>
          <div style={{ fontSize: '0.75rem', opacity: 0.7, marginBottom: 4 }}>
            B at step 0 — every entry exactly 0
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${GRID_COLS}, 10px)`, gap: 2 }}>
            {Array.from({ length: GRID_ROWS * GRID_COLS }).map((_, i) => (
              <div
                key={i}
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: 2,
                  background: 'var(--ifm-color-emphasis-200)',
                }}
              />
            ))}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', opacity: 0.7, marginBottom: 4 }}>
            A at step 0 — small random normal
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${GRID_COLS}, 10px)`, gap: 2 }}>
            {aInit.map((v, i) => (
              <div
                key={i}
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: 2,
                  background: v >= 0
                    ? `rgba(94, 234, 212, ${Math.min(Math.abs(v) / aMax, 1).toFixed(2)})`
                    : `rgba(252, 165, 165, ${Math.min(Math.abs(v) / aMax, 1).toFixed(2)})`,
                }}
              />
            ))}
          </div>
        </div>
      </div>

      <p style={{ fontSize: '0.8rem', opacity: 0.75, marginTop: '1rem' }}>
        Because B is zero, B·A is the zero matrix regardless of what A
        contains — the adapter starts as an exact no-op and the frozen base
        model is unchanged at step 0; only as training pushes B away from zero
        does A&apos;s random direction start to matter. ΔW is scaled by α/r
        before being added to W, which is why practitioners often hold α/r
        fixed while sweeping r rather than retuning it from scratch. And
        watch the compression line above: push r high enough relative to d
        and LoRA stops being cheap at all — rank buys capacity, not quality,
        and past whatever the task needs, more of it just spends your
        parameter budget back.
      </p>
    </div>
  );
}
