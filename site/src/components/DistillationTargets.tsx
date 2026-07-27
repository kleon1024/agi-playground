/**
 * Why the wrong answers are where a teacher's knowledge lives.
 *
 * A one-hot label says "Paris" and nothing else. A teacher model, asked the
 * same question, puts real mass on Lyon, Marseille, London -- near-misses
 * that encode which mistakes are plausible and which are absurd. Training
 * against the one-hot label throws that structure away; comparing
 * distributions keeps it. Temperature is the knob that decides how much of it
 * survives the comparison: low temperature collapses the teacher's call
 * toward the one-hot label it is meant to improve on, and high temperature
 * flattens it until every wrong answer looks equally plausible -- useful for
 * seeing the shape, useless as a final training target. This is also why the
 * loss gets rescaled by temperature squared: softening by T shrinks the
 * gradient by roughly 1/T, and the T^2 correction keeps the update size
 * comparable as the slider moves.
 *
 * The logits below are illustrative -- chosen to sit near the numbers the
 * chapter's prose describes, not a recorded run of any model. The storage
 * row is exact arithmetic from the chapter's stated top-k dtypes (uint16
 * ids, bfloat16 log-probabilities), computed live as k changes.
 */
import React, { useMemo, useState } from 'react';

const PROMPT = 'The capital of France is ___';

const CANDIDATES: { token: string; logit: number; label?: boolean }[] = [
  { token: 'Paris', logit: 3.0, label: true },
  { token: 'Lyon', logit: 1.9 },
  { token: 'Marseille', logit: 1.3 },
  { token: 'London', logit: 0.9 },
  { token: 'banana', logit: -5.0 },
];

function softmaxAtTemperature(logits: number[], temperature: number): number[] {
  const scaled = logits.map((z) => z / temperature);
  const max = Math.max(...scaled);
  const exps = scaled.map((z) => Math.exp(z - max));
  const sum = exps.reduce((a, b) => a + b, 0);
  return exps.map((e) => e / sum);
}

export default function DistillationTargets(): React.ReactElement {
  const [temperature, setTemperature] = useState(1);
  const [k, setK] = useState(16);

  const teacherProbs = useMemo(
    () => softmaxAtTemperature(CANDIDATES.map((c) => c.logit), temperature),
    [temperature],
  );

  const extraBytesPerToken = 4 * k; // topk_ids (uint16, 2B) + topk_logprobs (bf16, 2B), x k

  return (
    <div className="learning-widget">
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '0.9rem' }}>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          temperature <strong>{temperature.toFixed(1)}</strong>
          <input
            type="range" min={0.3} max={4} step={0.1} value={temperature}
            onChange={(e) => setTemperature(Number(e.target.value))}
            style={{ width: 150 }}
          />
        </label>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          top-k stored <strong>{k}</strong>
          <input
            type="range" min={1} max={64} step={1} value={k}
            onChange={(e) => setK(Number(e.target.value))}
            style={{ width: 150 }}
          />
        </label>
      </div>

      <p style={{ fontSize: 'var(--type-xs)', opacity: 0.75, marginBottom: '0.5rem' }}>
        Illustrative logits for the prompt &quot;{PROMPT}&quot; -- not a recorded run.
        One-hot label: <strong>Paris</strong>, 100%; every other candidate, 0%.
      </p>

      <div style={{ display: 'grid', gap: '0.45rem' }}>
        {CANDIDATES.map((c, i) => {
          const pct = teacherProbs[i] * 100;
          return (
            <div key={c.token} style={{ display: 'grid', gap: '0.2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--type-xs)' }}>
                <span>{c.token}{c.label ? ' (the label)' : ''}</span>
                <span>{pct >= 10 ? pct.toFixed(1) : pct.toFixed(2)}%</span>
              </div>
              <div style={{ height: 12, background: 'var(--rehearse-paper)', border: '1px solid var(--rehearse-rule)' }}>
                <div
                  style={{
                    width: `${Math.max(pct, 0.5)}%`,
                    height: '100%',
                    background: c.label ? 'var(--brand-chart-action-fill)' : 'var(--brand-chart-positive-fill)',
                    transition: 'width 220ms ease-out',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ fontSize: 'var(--type-sm)', marginTop: '0.9rem' }}>
        top-{k} storage: 2 bytes (<code>topk_ids</code>, uint16) + 2 bytes
        (<code>topk_logprobs</code>, bfloat16) per kept entry, x {k} ={' '}
        <strong>{extraBytesPerToken} extra bytes/token</strong> beyond the
        input ids any fine-tune already stores.
      </div>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.7rem' }}>
        Push temperature down and the teacher&apos;s bars collapse toward the
        one-hot label -- there is nothing left to transfer. Push it up and
        Lyon, Marseille, even banana rise together, flattened until they stop
        discriminating between plausible and absurd. The distillation target
        lives in between: temperature near 1 keeps the teacher&apos;s actual
        ranking of wrong answers legible to the student.
      </p>
    </div>
  );
}
