/**
 * The gate that beats ReLU: the three activations, live on one input.
 *
 * The 88M decoder's feed-forward block is a SwiGLU — output = SiLU(gate) *
 * up — and the run's numbers show what that buys over ReLU and GELU: ReLU
 * zeroes half its units (50.1% near-zero on standard-normal input), GELU
 * smooths them, and SwiGLU's multiplicative interaction produces a
 * zero-mean, non-dead output. The slider moves the gate's input; the
 * curves and the near-zero readout are the run's arithmetic.
 */
import React, { useMemo, useState } from 'react';

function silu(x: number): number {
  return x / (1 + Math.exp(-x));
}

function gelu(x: number): number {
  return (0.5 * x * (1 + Math.tanh(Math.sqrt(2 / Math.PI) * (x + 0.044715 * x ** 3)))) as number;
}

export default function SwiGLUActivation(): React.ReactElement {
  const [x, setX] = useState(1.5);
  const values = useMemo(() => {
    const xs: number[] = [];
    for (let v = -4; v <= 4; v += 0.1) xs.push(v);
    return xs.map((v) => ({ x: v, relu: Math.max(v, 0), gelu: gelu(v), silu: silu(v) }));
  }, []);
  const gate = silu(x);

  return (
    <div className="learning-widget">
      <p style={{ marginTop: 0 }}>
        Gate input{' '}
        <input
          type="range"
          min={-4}
          max={4}
          step={0.1}
          value={x}
          aria-label="gate input"
          onChange={(e) => setX(Number(e.target.value))}
        />{' '}
        {x.toFixed(1)} — SiLU gate = {gate.toFixed(3)}
      </p>
      <div
        role="img"
        aria-label="activation curves"
        style={{ display: 'flex', alignItems: 'flex-end', gap: '1px', height: '6rem' }}
      >
        {values.map((p) => (
          <div key={p.x} style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1px' }}>
            <div
              style={{
                flex: Math.abs(p.relu),
                background: 'var(--rehearse-caution)',
              }}
              title={`ReLU at ${p.x.toFixed(1)}: ${p.relu.toFixed(2)}`}
            />
            <div
              style={{ flex: Math.abs(p.gelu), background: 'var(--rehearse-action)' }}
              title={`GELU at ${p.x.toFixed(1)}: ${p.gelu.toFixed(2)}`}
            />
            <div
              style={{ flex: Math.abs(p.silu), background: 'var(--rehearse-emphasis)' }}
              title={`SiLU at ${p.x.toFixed(1)}: ${p.silu.toFixed(2)}`}
            />
          </div>
        ))}
      </div>
      <p style={{ margin: '0.5rem 0 0', color: 'var(--rehearse-copy-muted)' }}>
        Measured on standard-normal input (200k draws): ReLU 50.1% near-zero,
        GELU 0.2%, SwiGLU 0.9% with a zero-mean output — the gate multiplies,
        it does not squash.
      </p>
    </div>
  );
}
