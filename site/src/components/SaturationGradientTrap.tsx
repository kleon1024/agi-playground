import React, { useState } from 'react';

export default function SaturationGradientTrap(): React.ReactElement {
  const [z, setZ] = useState(0);
  const tanh = Math.tanh(z);
  const grad = 1 - tanh * tanh;
  const saturated = Math.abs(z) >= 2.5;
  return (
    <div className="learning-widget">
      <label>
        pre-activation z{' '}
        <input type="range" min={-4} max={4} step={0.1} value={z} onChange={(e) => setZ(Number(e.target.value))} />
        <strong> {z.toFixed(1)}</strong>
      </label>
      <p>tanh(z) = <strong>{tanh.toFixed(4)}</strong> (decoder output)</p>
      <p>tanh&apos;(z) = 1 - tanh(z)^2 = <strong>{grad.toFixed(4)}</strong> (gradient reaching the decoder)</p>
      {saturated && (
        <p style={{ color: 'var(--brand-chart-warning)' }}>
          saturated -- this is where this codec's real decoder pre-activations sat within the
          first ~20-50 training steps
        </p>
      )}
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        Measured, not illustrative: with Tanh, feeding two very different codebook vectors into
        the trained decoder produced a max output difference of 0.001 -- consistent with
        tanh&apos;(z) collapsing toward zero at the z the decoder was pushed to. Without Tanh (the
        fix applied), the codec reached 29% below the 8-clip overfit baseline.
      </p>
    </div>
  );
}
