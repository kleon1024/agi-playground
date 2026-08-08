import React, { useState } from 'react';

const SEEDS = {
  '0': { codes: 18, entropy: 0.405, margin: 4.3 },
  '1': { codes: 63, entropy: 0.76, margin: 38.2 },
  '2': { codes: 32, entropy: 0.644, margin: 22.7 },
} as const;

type Seed = keyof typeof SEEDS;

export default function SpeakerDiversityVariance(): React.ReactElement {
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
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>10 speakers, same fix (2000 steps, lr=1e-3) that reliably escaped collapse on stage 03's narrow baseline</p>
      <p>codebook used: <strong>{s.codes}/64</strong> codes (entropy_ratio {s.entropy.toFixed(3)})</p>
      <p>margin vs silence baseline: <strong>{s.margin.toFixed(1)}%</strong></p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        Reference, stage 03's narrow baseline (2 requested, 1 served; all three of its own seeds): 51-63/64 codes, entropy_ratio 0.787-0.870,
        margin ~52-54%. Same step count and learning rate, but at 10 speakers the outcome is no longer reliable --
        seed 0 barely escapes (18/64, 4.3%) while seed 1 escapes as fully as any stage-03 run (63/64, 38.2%).
      </p>
    </div>
  );
}
