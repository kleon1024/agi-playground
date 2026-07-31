import React, { useState } from 'react';

const K_VALUES = [48, 400, 1200, 3600] as const;
const N_DRAWS = 700;

function collisionProbability(k: number, n: number): number {
  return 1 - Math.exp((-n * (n - 1)) / (2 * k));
}

export default function CollisionProbability(): React.ReactElement {
  const [k, setK] = useState<number>(48);
  const p = collisionProbability(k, N_DRAWS);
  return (
    <div className="learning-widget">
      <label>
        state-space size k{' '}
        <input
          type="range"
          min={0}
          max={K_VALUES.length - 1}
          step={1}
          value={K_VALUES.indexOf(k as (typeof K_VALUES)[number])}
          onChange={(e) => setK(K_VALUES[Number(e.target.value)])}
        />
        <strong> {k}</strong>
        {k === 48 && ' (before fix)'}
        {k === 3600 && ' (after fix)'}
      </label>
      <p>
        collision probability at {N_DRAWS} draws: <strong>{(p * 100).toFixed(1)}%</strong>
      </p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        1 - exp(-n(n-1) / 2k). At k=48 (single-shape state space, pre-fix) this is essentially
        certain. Widening to k=3,600 (size and position jitter) spreads collisions thinly enough
        that a train/eval collision specifically becomes rare -- the guardrail measured zero.
      </p>
    </div>
  );
}
