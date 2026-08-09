/**
 * Why the cold-start GRPO run never produced a single usable rollout.
 *
 * The recorded run (runs/2026-07-30-base-grpo-run.md) sampled 6,400
 * completions over 200 steps and every one of the 200 groups came back
 * degenerate: a randomly initialized policy emitting the literal `<think>`
 * or `<answer>...</answer>` tags over a 78-symbol character vocabulary has
 * probability around 3e-12 per completion, so the expected number of
 * format-bearing completions across the whole run was about 2e-8 —
 * indistinguishable from never.
 *
 * This widget is arithmetic on that recorded estimate: pick how many
 * completions a run samples and read the expected number of times the format
 * appears. It is not a new measurement; it multiplies the run's own
 * per-completion probability by the count you choose.
 */
import React, { useMemo, useState } from 'react';

const P_PER_COMPLETION = 3e-12;
const PRESETS = [100, 1000, 6400, 10000, 100000, 1000000];

function format(expected: number): string {
  if (expected === 0) return '0';
  if (expected >= 1) return expected.toLocaleString(undefined, { maximumFractionDigits: 1 });
  return expected.toExponential(1);
}

export default function FormatStrikeChance(): React.ReactElement {
  const [index, setIndex] = useState(2);
  const completions = PRESETS[index];

  const expected = useMemo(() => completions * P_PER_COMPLETION, [completions]);
  const hits = Math.min(1, expected);
  const toOne = Math.ceil(1 / P_PER_COMPLETION);

  return (
    <div className="learning-widget">
      <p>
        Each completion is a random draw over a 78-symbol vocabulary, and the
        format needs the literal tag sequence to appear somewhere in it — the
        run estimates that chance at roughly 3e-12 per completion. Slide the
        number of completions a run samples and read what it can expect to
        see.
      </p>

      <label style={{ display: 'flex', gap: '0.8rem', alignItems: 'center', margin: '0.9rem 0' }}>
        <span style={{ minWidth: '11rem' }}>
          completions sampled = <strong>{completions.toLocaleString()}</strong>
        </span>
        <input
          type="range"
          min={0}
          max={PRESETS.length - 1}
          step={1}
          value={index}
          onChange={(e) => setIndex(Number(e.target.value))}
          style={{ width: '100%', maxWidth: 260 }}
        />
      </label>

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 'var(--type-xs)',
          opacity: 0.7,
          maxWidth: 340,
          margin: '0 0 0.9rem auto',
        }}
      >
        {PRESETS.map((p) => (
          <span key={p}>{p >= 10000 ? `${p / 1000}k` : p.toLocaleString()}</span>
        ))}
      </div>

      <div
        style={{
          border: '1px solid var(--rehearse-rule)',
          padding: '0.75rem',
          marginBottom: '0.9rem',
        }}
      >
        <div style={{ fontSize: 'var(--type-xs)', opacity: 0.65 }}>
          expected format-bearing completions
        </div>
        <div style={{ fontSize: 'var(--type-lg)', fontWeight: 700 }}>
          {format(expected)}
        </div>
        {index === 2 && (
          <div style={{ fontSize: 'var(--type-sm)', marginTop: '0.3rem' }}>
            This is the recorded run: 6,400 completions, expected count about
            2e-8 — and 200 of 200 groups came back degenerate.
          </div>
        )}
      </div>

      <div
        role="img"
        aria-label="Expected format strikes relative to one"
        style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 40, marginBottom: '0.9rem' }}
      >
        {Array.from({ length: 24 }).map((_, i) => {
          const lit = hits > 0 && i === 0;
          return (
            <div
              key={i}
              style={{
                flex: 1,
                height: lit ? '100%' : 3,
                background: lit
                  ? 'var(--brand-chart-warning)'
                  : 'var(--rehearse-rule)',
                borderRadius: 1,
              }}
            />
          );
        })}
      </div>

      <p>
        Even a run that samples a million completions can expect about
        3e-6 format-bearing draws — you would need on the order of{' '}
        {toOne.toLocaleString()} completions before an expected count of one.
        That is the honest shape of the cold-start failure: it is not that the
        policy is unlucky, it is that the format has essentially zero
        probability under a random policy over a character vocabulary, so RL
        reweighting has nothing to reweight — which is why the fix is the
        warm start, a few supervised steps on well-formed examples first, the
        same prior DeepSeek-R1-Zero's base model already had from pretraining.
      </p>
    </div>
  );
}
