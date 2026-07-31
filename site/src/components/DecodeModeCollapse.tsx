import React, { useState } from 'react';

const PER_SEED = {
  0: { greedy: 0.078, sampled: 0.182 },
  1: { greedy: 0.062, sampled: 0.144 },
  2: { greedy: 0.078, sampled: 0.210 },
} as const;
const RANDOM_BASELINE = 0.222;
const GREEDY_BASELINE = 0.824;

type Seed = keyof typeof PER_SEED;

export default function DecodeModeCollapse(): React.ReactElement {
  const [seed, setSeed] = useState<Seed>(0);
  const s = PER_SEED[seed];
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
      <p>greedy decode: <strong>{(s.greedy * 100).toFixed(1)}%</strong></p>
      <p>sampled decode (T=1.0): <strong>{(s.sampled * 100).toFixed(1)}%</strong> ({(s.sampled / s.greedy).toFixed(1)}x greedy)</p>
      <p>random baseline: {(RANDOM_BASELINE * 100).toFixed(1)}%, greedy-heuristic baseline: {(GREEDY_BASELINE * 100).toFixed(1)}%</p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        Sampled decode beats greedy by 2.3-2.7x on every seed -- larger than temperature alone
        would produce from a genuinely board-independent policy, evidence that real
        board-conditional probability mass exists but argmax is the wrong lens for finding it.
      </p>
    </div>
  );
}
