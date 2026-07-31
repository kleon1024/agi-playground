import React, { useState } from 'react';

const SEEDS = {
  0: { lmCompletion: 0.0804, oracle: 0.0779, exactMatch: 0.067 },
  1: { lmCompletion: 0.0865, oracle: 0.0865, exactMatch: 0.220 },
  2: { lmCompletion: 0.0882, oracle: 0.0882, exactMatch: 0.193 },
} as const;
const BASELINE = 0.1281;

type Seed = keyof typeof SEEDS;

export default function SeedSpreadBands(): React.ReactElement {
  const [seed, setSeed] = useState<Seed>(0);
  const s = SEEDS[seed];
  return (
    <div className="learning-widget">
      <label>
        seed{' '}
        <select value={seed} onChange={(e) => setSeed(Number(e.target.value) as Seed)}>
          <option value={0}>0</option>
          <option value={1}>1</option>
          <option value={2}>2</option>
        </select>
      </label>
      <p>frame-repeat baseline (fixed): <strong>{BASELINE.toFixed(4)}</strong></p>
      <p>oracle tokens (codec-only ceiling): <strong>{s.oracle.toFixed(4)}</strong></p>
      <p>LM completion: <strong>{s.lmCompletion.toFixed(4)}</strong>, exact-match rate: <strong>{(s.exactMatch * 100).toFixed(1)}%</strong></p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        All three seeds beat the fixed baseline decisively while landing near the oracle ceiling.
        Exact-match rate varies far more across seeds (6.7% to 22.0%) than pixel MSE does -- stage
        01's low-fidelity codec forgives many wrong token choices at the pixel level.
      </p>
    </div>
  );
}
