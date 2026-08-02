import React, { useState } from 'react';

const REGIMES = {
  before: {
    label: 'stage 01 (no warmup)',
    perSeed: [0.5128, 0.5153, 0.2844],
    mean: 0.4375,
    spread: 0.2309,
  },
  after: {
    label: 'this stage (10% linear warmup)',
    perSeed: [0.4707, 0.5242, 0.4962],
    mean: 0.497,
    spread: 0.0536,
  },
} as const;

const TEXT_ONLY_MEAN = 0.327;

type Regime = keyof typeof REGIMES;

export default function WarmupSeedStability(): React.ReactElement {
  const [regime, setRegime] = useState<Regime>('before');
  const r = REGIMES[regime];
  return (
    <div className="learning-widget">
      <label>
        <input type="radio" checked={regime === 'before'} onChange={() => setRegime('before')} /> no warmup
      </label>{' '}
      <label>
        <input type="radio" checked={regime === 'after'} onChange={() => setRegime('after')} /> with warmup
      </label>
      <p>
        per-seed eval exact-match:{' '}
        <strong>{r.perSeed.map((v) => v.toFixed(4)).join(', ')}</strong>
      </p>
      <p>
        mean: <strong>{r.mean.toFixed(4)}</strong>, spread: <strong>{r.spread.toFixed(4)}</strong>
      </p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        {regime === 'before'
          ? `Seed 2 (0.2844) falls below every text-only seed (mean ${TEXT_ONLY_MEAN.toFixed(3)}) -- that single collapse makes vision's own seed spread (0.2309) larger than its gap to text-only's mean (0.1105), which is why stage 01 could not call this a clean win.`
          : `All three seeds now land in a tight 0.47-0.52 band, each individually beating text-only's mean by several times text-only's own 0.0459 spread. Spread tightened more than 4x (0.2309 to 0.0536) by changing exactly one thing: a 10%-of-steps linear LR warmup.`}
      </p>
    </div>
  );
}
