import React, { useState } from 'react';

const SIZES = {
  '8': { epochs: 25, satNaive: 0.651, satBalanced: 0.706, dwellNaive: 0.658, dwellBalanced: 0.803 },
  '16': { epochs: 60, satNaive: 0.644, satBalanced: 0.664, dwellNaive: -0.080, dwellBalanced: 0.809 },
} as const;

type Hidden = keyof typeof SIZES;

export default function MultiTaskBalancing(): React.ReactElement {
  const [hidden, setHidden] = useState<Hidden>('16');
  const s = SIZES[hidden];
  return (
    <div className="learning-widget">
      <label>
        <input type="radio" checked={hidden === '8'} onChange={() => setHidden('8')} /> hidden=8, epochs=25
      </label>{' '}
      <label>
        <input type="radio" checked={hidden === '16'} onChange={() => setHidden('16')} /> hidden=16, epochs=60
      </label>
      <p>satisfaction: naive <strong>{s.satNaive.toFixed(3)}</strong> &rarr; balanced <strong>{s.satBalanced.toFixed(3)}</strong></p>
      <p>dwell: naive <strong>{s.dwellNaive.toFixed(3)}</strong> &rarr; balanced <strong>{s.dwellBalanced.toFixed(3)}</strong></p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        {hidden === '16'
          ? "The wider trunk makes naive weighting worse, not better: dwell's raw-seconds gradient dominates the shared trunk so completely that its naive correlation goes negative (-0.080). Balancing recovers 0.809 regardless of trunk size -- the fix, not the architecture, is what stabilizes this."
          : "At the smaller trunk, naive weighting is merely suboptimal rather than actively harmful -- dwell's raw-seconds gradient still crowds out the sparser satisfaction task, but it hasn't yet driven dwell's own correlation negative the way the wider trunk does."}
      </p>
    </div>
  );
}
