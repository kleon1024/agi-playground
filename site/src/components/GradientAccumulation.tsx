/**
 * Gradient accumulation, and the one-line bug that silently changes your LR.
 *
 * Accumulation lets a small micro-batch simulate a large one: run several
 * forward/backward passes without an optimizer step, letting gradients pile
 * up in `.grad`, then step once and clear. That is only equivalent to a
 * single large batch if each micro-batch's contribution is scaled by
 * 1 / accumulation_steps before it's added in — usually by dividing the loss
 * before calling backward().
 *
 * Forget that division and the accumulated gradient is the *sum* of
 * accumulation_steps gradients instead of their *mean* — a vector
 * accumulation_steps times too large. The optimizer still applies its
 * configured learning rate to that oversized gradient, which is
 * indistinguishable from having silently multiplied the learning rate by
 * accumulation_steps. Nothing crashes. Loss curves just look wrong, or
 * training destabilizes, in a way that is easy to blame on the wrong
 * hyperparameter.
 */
import React, { useEffect, useMemo, useState } from 'react';

const SEQ_LEN = 2048; // fixed context length, just to make token counts concrete
const BASE_LR = 3e-4; // a typical configured peak LR, for the "effective LR" illustration
const TICK_MS = 500;

function fmtTokens(n: number): string {
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return `${n}`;
}

export default function GradientAccumulation(): React.ReactElement {
  const [microBatchSize, setMicroBatchSize] = useState(4);
  const [accumSteps, setAccumSteps] = useState(4);
  const [bugOn, setBugOn] = useState(false);
  const [playing, setPlaying] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setTick((t) => t + 1), TICK_MS);
    return () => clearInterval(id);
  }, [playing]);

  // Reset the animation phase whenever accumSteps changes, so the fill
  // sequence always starts from an empty accumulator instead of a stale one.
  useEffect(() => {
    setTick(0);
  }, [accumSteps]);

  const phase = tick % (accumSteps + 1); // 0..accumSteps-1 fills a square, === accumSteps is the fire pulse
  const filledCount = Math.min(phase, accumSteps);
  const isFiring = phase === accumSteps;
  const optimizerStepsFired = Math.floor(tick / (accumSteps + 1));

  const { tokensPerMicroBatch, tokensPerOptimizerStep, effectiveBatchSize, lrMultiplier, effectiveLR } = useMemo(() => {
    const tpm = microBatchSize * SEQ_LEN;
    const multiplier = bugOn ? accumSteps : 1;
    return {
      tokensPerMicroBatch: tpm,
      tokensPerOptimizerStep: tpm * accumSteps,
      effectiveBatchSize: microBatchSize * accumSteps,
      lrMultiplier: multiplier,
      effectiveLR: BASE_LR * multiplier,
    };
  }, [microBatchSize, accumSteps, bugOn]);

  return (
    <div style={{ margin: '1.5rem 0' }}>
      <div style={{ display: 'grid', gap: '0.6rem', marginBottom: '1rem' }}>
        <label style={{ display: 'flex', gap: '0.7rem', alignItems: 'center' }}>
          <span style={{ minWidth: '10rem' }}>micro-batch size <strong>{microBatchSize}</strong></span>
          <input type="range" min={1} max={32} step={1} value={microBatchSize}
                 onChange={(e) => setMicroBatchSize(Number(e.target.value))}
                 style={{ flex: 1, maxWidth: 260 }} />
        </label>
        <label style={{ display: 'flex', gap: '0.7rem', alignItems: 'center' }}>
          <span style={{ minWidth: '10rem' }}>accumulation steps <strong>{accumSteps}</strong></span>
          <input type="range" min={1} max={16} step={1} value={accumSteps}
                 onChange={(e) => setAccumSteps(Number(e.target.value))}
                 style={{ flex: 1, maxWidth: 260 }} />
        </label>
        <div style={{ display: 'flex', gap: '1.2rem', flexWrap: 'wrap' }}>
          <label style={{ cursor: 'pointer', userSelect: 'none' }}>
            <input type="checkbox" checked={bugOn} onChange={(e) => setBugOn(e.target.checked)} />{' '}
            bug: forget to divide loss by accumulation steps
          </label>
          <button
            onClick={() => setPlaying((p) => !p)}
            style={{ padding: '0.2rem 0.6rem', borderRadius: 6, cursor: 'pointer' }}
          >
            {playing ? '⏸ pause' : '▶ play'}
          </button>
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          gap: 6,
          flexWrap: 'wrap',
          padding: '0.8rem',
          borderRadius: 8,
          background: isFiring ? (bugOn ? 'rgba(252, 165, 165, 0.15)' : 'rgba(94, 234, 212, 0.12)') : 'transparent',
          transition: 'background 150ms',
          minHeight: 46,
          alignItems: 'center',
        }}
      >
        {Array.from({ length: accumSteps }).map((_, i) => (
          <div
            key={i}
            title={`micro-batch ${i + 1}: ${fmtTokens(tokensPerMicroBatch)} tokens`}
            style={{
              width: 28,
              height: 28,
              borderRadius: 5,
              background: i < filledCount || isFiring ? 'var(--brand-chart-positive-fill)' : 'var(--ifm-color-emphasis-200)',
              transition: 'background 150ms',
            }}
          />
        ))}
        <span style={{ marginLeft: '0.6rem', fontSize: '1.3rem' }}>→</span>
        <div
          title="optimizer step"
          style={{
            width: 40,
            height: 40,
            borderRadius: 8,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.1rem',
            background: isFiring ? (bugOn ? 'var(--brand-chart-danger-fill)' : 'var(--brand-chart-action-fill)') : 'var(--ifm-color-emphasis-200)',
            color: isFiring ? 'var(--rehearse-ink)' : 'inherit',
            transform: isFiring ? 'scale(1.12)' : 'scale(1)',
            transition: 'background 150ms, transform 150ms',
          }}
        >
          {isFiring ? '⚡' : ''}
        </div>
        <span style={{ fontSize: '0.8rem', opacity: 0.7, marginLeft: '0.4rem' }}>
          optimizer steps fired: <strong>{optimizerStepsFired}</strong>
        </span>
      </div>

      <div style={{ display: 'flex', gap: '1.4rem', fontSize: '0.85rem', marginTop: '0.8rem', flexWrap: 'wrap' }}>
        <span>tokens / micro-batch <strong>{fmtTokens(tokensPerMicroBatch)}</strong></span>
        <span>tokens / optimizer step <strong>{fmtTokens(tokensPerOptimizerStep)}</strong></span>
        <span>effective batch size <strong>{effectiveBatchSize}</strong> sequences</span>
      </div>

      <div style={{ marginTop: '0.6rem', fontSize: '0.85rem' }}>
        {bugOn ? (
          <span style={{ color: 'var(--brand-chart-danger)' }}>
            loss summed, not averaged, over {accumSteps} micro-batches → gradient is{' '}
            <strong>{accumSteps}×</strong> too large → as if LR were{' '}
            <strong>{effectiveLR.toExponential(2)}</strong> instead of the configured{' '}
            <strong>{BASE_LR.toExponential(2)}</strong>
          </span>
        ) : (
          <span style={{ opacity: 0.75 }}>
            loss divided by {accumSteps} before backward → accumulated gradient matches a true{' '}
            {effectiveBatchSize}-sequence batch, LR stays at the configured{' '}
            <strong>{BASE_LR.toExponential(2)}</strong>
          </span>
        )}
      </div>

      <p style={{ fontSize: '0.8rem', opacity: 0.75, marginTop: '0.75rem' }}>
        Every micro-batch above fills one slot in the accumulator; when it's
        full the optimizer fires once and clears. That's transparent to the
        model — <em>if</em> each micro-batch's loss was scaled down first. Flip
        the bug toggle on and the squares fill identically, the optimizer
        still fires on schedule, and nothing looks broken — but the gradient
        behind that step is {accumSteps}× too large, which is exactly as if
        someone had quietly turned the learning rate up by {accumSteps}×.
      </p>
    </div>
  );
}
