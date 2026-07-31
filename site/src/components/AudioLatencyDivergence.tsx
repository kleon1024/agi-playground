import React, { useState } from 'react';

const REGIMES = {
  native: { naiveEarly: 1.46, naiveLate: 1.57, cachedEarly: 1.15, cachedLate: 1.04 },
  stress: { naiveEarly: 1.43, naiveLate: 9.81, cachedEarly: 1.15, cachedLate: 1.50 },
} as const;

type Regime = keyof typeof REGIMES;

export default function AudioLatencyDivergence(): React.ReactElement {
  const [regime, setRegime] = useState<Regime>('native');
  const r = REGIMES[regime];
  const naiveRatio = r.naiveLate / r.naiveEarly;
  const cachedRatio = r.cachedLate / r.cachedEarly;
  return (
    <div className="learning-widget">
      <label>
        <input type="radio" checked={regime === 'native'} onChange={() => setRegime('native')} /> native (48 tokens)
      </label>{' '}
      <label>
        <input type="radio" checked={regime === 'stress'} onChange={() => setRegime('stress')} /> stress test (500 tokens)
      </label>
      <p>naive: {r.naiveEarly.toFixed(2)}ms early -&gt; {r.naiveLate.toFixed(2)}ms late (<strong>{naiveRatio.toFixed(1)}x</strong>)</p>
      <p>cached: {r.cachedEarly.toFixed(2)}ms early -&gt; {r.cachedLate.toFixed(2)}ms late (<strong>{cachedRatio.toFixed(1)}x</strong>)</p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        The O(t) vs O(1) mechanism is real at both scales, but at native clip length fixed
        per-step overhead dominates -- it only becomes visible once the sequence is long
        enough for the linear term to matter.
      </p>
    </div>
  );
}
