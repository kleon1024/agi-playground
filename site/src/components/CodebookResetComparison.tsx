import React, { useState } from 'react';

const SEEDS = {
  '0': { noReset: { codes: 18, entropy: 0.405, margin: 4.3 }, reset: { codes: 64, entropy: 0.826, margin: 33.8 } },
  '1': { noReset: { codes: 63, entropy: 0.76, margin: 38.2 }, reset: { codes: 64, entropy: 0.814, margin: 37.6 } },
  '2': { noReset: { codes: 32, entropy: 0.644, margin: 22.7 }, reset: { codes: 64, entropy: 0.791, margin: 36.9 } },
} as const;

type Seed = keyof typeof SEEDS;

export default function CodebookResetComparison(): React.ReactElement {
  const [seed, setSeed] = useState<Seed>('0');
  const s = SEEDS[seed];
  return (
    <div className="learning-widget">
      <label>
        <input type="radio" checked={seed === '0'} onChange={() => setSeed('0')} /> seed 0
      </label>{' '}
      <label>
        <input type="radio" checked={seed === '1'} onChange={() => setSeed('1')} /> seed 1
      </label>{' '}
      <label>
        <input type="radio" checked={seed === '2'} onChange={() => setSeed('2')} /> seed 2
      </label>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        Same 10-speaker mix, same step count (2000) and learning rate (1e-3) as stage 04 -- only the vector
        quantizer differs.
      </p>
      <p>
        stage 04, no reset: <strong>{s.noReset.codes}/64</strong> codes (entropy_ratio {s.noReset.entropy.toFixed(3)}),{' '}
        margin <strong>{s.noReset.margin.toFixed(1)}%</strong>
      </p>
      <p>
        this stage, dead-code reset: <strong>{s.reset.codes}/64</strong> codes (entropy_ratio {s.reset.entropy.toFixed(3)}),{' '}
        margin <strong>{s.reset.margin.toFixed(1)}%</strong>
      </p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        Without reset, codebook coverage and margin both swing widely by seed (18-63/64 codes, 4.3%-38.2% margin).
        With dead-code reset, every seed reaches full 64/64 coverage and the margin tightens to a 33.8%-37.6% band --
        the same fix (Razavi, van den Oord &amp; Vinyals, VQ-VAE-2, 2019) applied to only this mission's straight-through
        VQ, not its full EMA-updated codebook.
      </p>
    </div>
  );
}
