/**
 * Why speculative decoding is free tokens, not a quality trade.
 *
 * A small, cheap draft model proposes K tokens; the big target model checks
 * all K+1 positions in a single forward pass and accepts a prefix under
 * modified rejection sampling. People hear "a smaller model is writing your
 * tokens" and assume that must cost some quality — it does not. Modified
 * rejection sampling is constructed so the accepted sequence has *exactly*
 * the target model's distribution, token for token, as if the target had
 * generated alone. What speculative decoding actually trades is wall-clock
 * time for a cheap, wasted forward pass when the draft guesses wrong — and
 * that trade stops paying off once you're compute-bound (large batch, GPUs
 * already saturated) rather than memory-bandwidth-bound.
 */
import React, { useEffect, useMemo, useState } from 'react';

const TICK_MS = 420;

/** Deterministic per-round "coin flips," so the animation is reproducible. */
function mulberry32(seed: number): () => number {
  let s = seed | 0;
  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** How many of the K draft tokens survive verification this round. */
function roundAccepted(round: number, k: number, alpha: number): number {
  const rand = mulberry32(round * 7919 + 13);
  let accepted = 0;
  for (let i = 0; i < k; i++) {
    if (rand() < alpha) accepted++;
    else break;
  }
  return accepted;
}

type Phase = 'drafting' | 'verifying' | 'resolved';

export default function SpeculativeDecoding(): React.ReactElement {
  const [alpha, setAlpha] = useState(0.7);
  const [k, setK] = useState(4);
  const [cost, setCost] = useState(0.2);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(true);

  useEffect(() => {
    setStep(0);
  }, [k, alpha]);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setStep((s) => s + 1), TICK_MS);
    return () => clearInterval(id);
  }, [playing]);

  const { round, phase, revealedDraft, accepted, roundsCompleted, totalTokens } = useMemo(() => {
    const stepsPerRound = k + 2;
    const r = Math.floor(step / stepsPerRound);
    const within = step % stepsPerRound;
    const phase: Phase = within < k ? 'drafting' : within === k ? 'verifying' : 'resolved';
    const revealedDraft = phase === 'drafting' ? within + 1 : k;
    const accepted = roundAccepted(r, k, alpha);

    const completed = phase === 'resolved' ? r + 1 : r;
    let totalTokens = 0;
    for (let i = 0; i < completed; i++) totalTokens += roundAccepted(i, k, alpha) + 1;

    return {
      round: r,
      phase,
      revealedDraft,
      accepted,
      roundsCompleted: completed,
      totalTokens,
    };
  }, [step, k, alpha]);

  // Closed-form expectations — these describe the process, independent of
  // any single animated round's luck.
  const expectedTokens = (1 - Math.pow(alpha, k + 1)) / (1 - alpha);
  const costPerRound = k * cost + 1;
  const speedup = expectedTokens / costPerRound;
  const kStar = -1 / Math.log(alpha);
  const runningAvg = roundsCompleted > 0 ? totalTokens / roundsCompleted : 0;

  return (
    <div style={{ margin: '1.5rem 0' }}>
      <div style={{ display: 'flex', gap: '1.4rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          α <strong>{alpha.toFixed(2)}</strong>
          <input
            type="range"
            min={0.05}
            max={0.95}
            step={0.05}
            value={alpha}
            onChange={(e) => setAlpha(Number(e.target.value))}
            style={{ width: 130 }}
          />
        </label>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          K <strong>{k}</strong>
          <input
            type="range"
            min={1}
            max={10}
            step={1}
            value={k}
            onChange={(e) => setK(Number(e.target.value))}
            style={{ width: 110 }}
          />
        </label>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          draft cost <strong>{cost.toFixed(2)}×</strong>
          <input
            type="range"
            min={0.05}
            max={0.5}
            step={0.05}
            value={cost}
            onChange={(e) => setCost(Number(e.target.value))}
            style={{ width: 110 }}
          />
        </label>
        <button
          onClick={() => setPlaying((p) => !p)}
          style={{ padding: '0.25rem 0.7rem', borderRadius: 6, cursor: 'pointer' }}
        >
          {playing ? '⏸ pause' : '▶ play'}
        </button>
      </div>

      <div style={{ fontSize: '0.75rem', opacity: 0.7, marginBottom: '0.4rem' }}>
        round {round + 1} · {phase === 'drafting' ? 'draft model proposing…' : phase === 'verifying' ? 'target model verifying…' : 'resolved'}
      </div>

      <div style={{ display: 'flex', gap: 6, alignItems: 'center', minHeight: 36 }}>
        {Array.from({ length: k }).map((_, i) => {
          let background = 'var(--ifm-color-emphasis-200)';
          let border = '1px dashed var(--ifm-color-emphasis-400)';
          let label = '';
          let opacity = 1;
          if (phase === 'drafting' && i < revealedDraft) {
            background = 'var(--brand-chart-signal)';
            border = 'none';
            label = 'D';
          } else if (phase === 'verifying') {
            background = 'var(--brand-chart-signal)';
            border = 'none';
            label = 'D';
          } else if (phase === 'resolved') {
            border = 'none';
            if (i < accepted) {
              background = 'var(--brand-chart-positive-fill)';
              label = '✓';
            } else {
              background = 'var(--ifm-color-emphasis-300)';
              label = '✗';
              opacity = 0.5;
            }
          }
          return (
            <div
              key={i}
              style={{
                width: 28,
                height: 28,
                borderRadius: 5,
                background,
                border,
                opacity,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.7rem',
                color: 'var(--rehearse-ink)',
                transition: 'background 150ms, opacity 150ms',
              }}
            >
              {label}
            </div>
          );
        })}
        {phase === 'resolved' && (
          <div
            title="bonus token — supplied directly by the target model, guaranteed correct"
            style={{
              width: 28,
              height: 28,
              borderRadius: 5,
              background: 'var(--brand-chart-warning-fill)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.6rem',
              color: 'var(--rehearse-ink)',
              marginLeft: 6,
            }}
          >
            +1
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '1.4rem', fontSize: '0.85rem', marginTop: '0.9rem', flexWrap: 'wrap' }}>
        <span>
          expected tokens/round <strong>{expectedTokens.toFixed(2)}</strong>
        </span>
        <span>
          cost/round <strong>{costPerRound.toFixed(2)}×</strong> target passes
        </span>
        <span>
          speedup <strong>{speedup.toFixed(2)}×</strong>
        </span>
        <span>
          K* ≈ <strong>{kStar.toFixed(1)}</strong>
        </span>
        <span style={{ opacity: 0.75 }}>
          simulated average so far <strong>{runningAvg.toFixed(2)}</strong> tokens/round
        </span>
      </div>

      <p style={{ fontSize: '0.8rem', opacity: 0.75, marginTop: '0.75rem' }}>
        Watch the simulated average drift toward the closed-form expectation
        (1 − α<sup>K+1</sup>) / (1 − α) as rounds accumulate — that convergence
        is the point: nothing here is approximate. Modified rejection sampling
        makes the accepted output <strong>exactly</strong> the target
        distribution, never a cheaper approximation of it. What you're really
        buying is idle target-model FLOPs: while it verifies K drafted tokens
        in one pass it would otherwise spend generating one token at a time.
        Raise the batch size enough that the target model is already
        compute-bound rather than memory-bandwidth-bound, and that idle
        capacity disappears — at which point speculative decoding stops
        buying you anything, no matter how good α is.
      </p>
    </div>
  );
}
