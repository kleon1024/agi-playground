/**
 * Codebook usage over training — the collapse-to-partition arc, replayed.
 *
 * A VQ codebook starts dead: with random codes and a straight-through
 * gradient, the whole batch collapses onto one or two codes at step 0, and
 * unused codes receive no gradient to escape. Whether the codebook
 * partitions later is seed-dependent and non-monotonic — this run (recorded
 * 2026-08-06, seed 7, 64-entry codebook, 600 steps) goes 1 -> 2 -> 13 -> 14
 * -> 12 -> 15 unique codes, ending at entropy 0.475 of maximum, while the
 * recorded seed-0 run ended healthy at 34/64.
 *
 * Data is the actual run's per-step bincounts
 * (runs/codec-seed7-usage.json), not a schematic. The step slider moves
 * through six snapshots; bar height is sqrt(count) so the few live codes
 * stay visible next to the 2048-count winner.
 */
import React, { useState } from 'react';

const SNAPSHOTS = [
  {
    step: 0,
    unique: 1,
    entropy: 0.0,
    counts: [0,0,0,0,0,0,0,0,0,0,0,2048,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  },
  {
    step: 100,
    unique: 2,
    entropy: 0.033,
    counts: [0,0,0,0,0,0,0,0,0,0,0,64,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1984,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  },
  {
    step: 200,
    unique: 2,
    entropy: 0.033,
    counts: [0,0,0,0,0,0,0,0,0,0,0,64,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1984,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  },
  {
    step: 300,
    unique: 13,
    entropy: 0.187,
    counts: [0,1,0,0,0,0,0,0,8,1,0,0,0,0,1496,0,0,10,2,0,2,0,0,0,0,0,9,0,0,0,0,0,0,0,0,0,0,470,0,0,0,0,0,14,0,0,0,0,0,0,0,0,0,0,0,19,2,0,0,0,0,14,0,0],
  },
  {
    step: 400,
    unique: 14,
    entropy: 0.52,
    counts: [0,0,0,0,0,0,0,0,0,0,0,0,0,0,300,0,0,333,0,0,0,0,0,0,0,0,8,65,0,9,0,0,0,0,0,0,59,310,0,0,0,0,0,86,0,290,0,0,0,0,0,0,0,0,45,239,0,1,0,0,0,5,298,0],
  },
  {
    step: 500,
    unique: 12,
    entropy: 0.409,
    counts: [0,0,0,2,0,0,4,2,0,0,0,0,0,0,448,0,0,361,0,0,0,0,0,0,0,0,2,4,0,0,0,0,0,0,0,0,0,552,0,0,0,0,0,36,6,0,0,0,0,0,0,0,0,0,0,351,0,0,0,0,0,0,280,0],
  },
];

const TRAJECTORY = [
  { step: 0, unique: 1, entropy: 0.0 },
  { step: 100, unique: 2, entropy: 0.033 },
  { step: 200, unique: 2, entropy: 0.033 },
  { step: 300, unique: 13, entropy: 0.187 },
  { step: 400, unique: 14, entropy: 0.52 },
  { step: 500, unique: 12, entropy: 0.409 },
  { step: 600, unique: 15, entropy: 0.475 },
];

export default function CodebookUsageTimeline(): React.ReactElement {
  const [index, setIndex] = useState(0);
  const snap = SNAPSHOTS[index];
  const maxSqrt = Math.sqrt(Math.max(...snap.counts));

  return (
    <div className="learning-widget">
      <p style={{ marginTop: 0 }}>
        Step{' '}
        <select
          value={index}
          onChange={(e) => setIndex(Number(e.target.value))}
          aria-label="training step"
        >
          {SNAPSHOTS.map((s, i) => (
            <option key={s.step} value={i}>
              {s.step}
            </option>
          ))}
        </select>{' '}
        — <strong>{snap.unique}/64</strong> codes in use, entropy ratio{' '}
        <strong>{snap.entropy.toFixed(3)}</strong>.
      </p>
      <div
        role="img"
        aria-label="codebook usage histogram at the selected step"
        style={{ display: 'flex', alignItems: 'flex-end', gap: '1px', height: '6rem' }}
      >
        {snap.counts.map((c, i) => (
          <div
            key={i}
            title={`code ${i}: ${c}`}
            style={{
              flex: 1,
              height: `${c > 0 ? (Math.sqrt(c) / maxSqrt) * 100 : 2}%`,
              background: c > 0 ? 'var(--rehearse-action)' : 'var(--rehearse-rule)',
            }}
          />
        ))}
      </div>
      <p style={{ margin: '0.7rem 0 0.3rem', color: 'var(--rehearse-copy-muted)' }}>
        Unique codes over training (recorded run, seed 7):
      </p>
      <div
        role="img"
        aria-label="unique codes trajectory across training"
        style={{ display: 'flex', alignItems: 'flex-end', gap: '0.35rem', height: '3rem' }}
      >
        {TRAJECTORY.map((t, i) => (
          <div key={t.step} style={{ flex: 1, textAlign: 'center' }}>
            <div
              style={{
                height: `${(t.unique / 64) * 100}%`,
                background: i === index ? 'var(--rehearse-emphasis)' : 'var(--rehearse-action)',
              }}
              title={`step ${t.step}: ${t.unique}/64`}
            />
            <span style={{ fontSize: '0.7rem' }}>{t.step}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
