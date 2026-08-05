/**
 * Tiny MoE routing: the four statistics the expert line is about.
 *
 * MoE's promise is capacity without compute: keep many expert networks, route
 * each input to a subset. This widget replays the recorded toy experiment
 * (foundations/07-moe, 4 experts, 4 patterns, pattern 0 four times as
 * frequent) — the per-config routing counts, accuracy, entropy, and load
 * imbalance are the run's actual numbers, and only the top-k / shared
 * selection is live. The lesson that falls out: accuracy is 1.000 in every
 * cell, routing buys compute, and top-1 under skew produces a dead expert.
 */
import React, { useState } from 'react';

const CONFIGS: Record<string, { topK: number; shared: boolean }> = {
  '1-false': { topK: 1, shared: false },
  '1-true': { topK: 1, shared: true },
  '2-false': { topK: 2, shared: false },
  '2-true': { topK: 2, shared: true },
  '4-false': { topK: 4, shared: false },
  '4-true': { topK: 4, shared: true },
};

const DATA: Record<string, { counts: number[]; acc: number; entropy: number; imbalance: string }> = {
  '1-false': { counts: [45, 0, 6, 149], acc: 1.0, entropy: 1.327, imbalance: 'dead expert' },
  '1-true': { counts: [172, 8, 11, 9], acc: 1.0, entropy: 1.362, imbalance: '21.5x' },
  '2-false': { counts: [93, 144, 37, 126], acc: 1.0, entropy: 1.352, imbalance: '3.9x' },
  '2-true': { counts: [174, 56, 31, 139], acc: 1.0, entropy: 1.349, imbalance: '5.6x' },
  '4-false': { counts: [200, 200, 200, 200], acc: 1.0, entropy: 1.24, imbalance: '1.0x' },
  '4-true': { counts: [200, 200, 200, 200], acc: 1.0, entropy: 1.27, imbalance: '1.0x' },
};

export default function MoERouting(): React.ReactElement {
  const [topK, setTopK] = useState(1);
  const [shared, setShared] = useState(false);
  const key = `${topK}-${String(shared)}`;
  const d = DATA[key];
  const maxCount = Math.max(...d.counts, 1);

  return (
    <div className="learning-widget">
      <p style={{ marginTop: 0 }}>
        top-k{' '}
        <select value={topK} onChange={(e) => setTopK(Number(e.target.value))} aria-label="top k">
          {[1, 2, 4].map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>{' '}
        <label style={{ marginLeft: '0.5rem' }}>
          <input
            type="checkbox"
            checked={shared}
            onChange={(e) => setShared(e.target.checked)}
          />{' '}
          shared expert
        </label>
      </p>
      <div
        role="img"
        aria-label="routing counts per expert"
        style={{ display: 'flex', alignItems: 'flex-end', gap: '0.4rem', height: '6rem' }}
      >
        {d.counts.map((c, i) => (
          <div key={i} style={{ flex: 1, textAlign: 'center' }}>
            <div
              style={{
                height: `${(c / maxCount) * 100}%`,
                background: c === 0 ? 'var(--rehearse-caution)' : 'var(--rehearse-action)',
              }}
              title={`expert ${i}: ${c}/200 routed`}
            />
            <span style={{ fontSize: '0.7rem' }}>E{i}</span>
          </div>
        ))}
      </div>
      <p style={{ margin: '0.7rem 0 0', color: 'var(--rehearse-copy-muted)' }}>
        top-{topK} {shared ? 'with shared expert' : 'no shared expert'}: accuracy{' '}
        {d.acc.toFixed(3)}, routing entropy {d.entropy.toFixed(3)} (max{' '}
        {Math.log(4).toFixed(3)}), load imbalance {d.imbalance}. The recorded
        counts are per-expert routed test inputs out of 200.
      </p>
    </div>
  );
}
