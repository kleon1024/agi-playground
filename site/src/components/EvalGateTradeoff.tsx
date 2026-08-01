import React, { useState } from 'react';

const SWEEP = [
  { delta: 0.05, falseBlock: 0.423, falsePass: 0.000 },
  { delta: 0.10, falseBlock: 0.346, falsePass: 0.000 },
  { delta: 0.15, falseBlock: 0.275, falsePass: 0.000 },
  { delta: 0.20, falseBlock: 0.207, falsePass: 0.000 },
  { delta: 0.25, falseBlock: 0.141, falsePass: 0.000 },
  { delta: 0.30, falseBlock: 0.075, falsePass: 0.003 },
  { delta: 0.35, falseBlock: 0.026, falsePass: 0.044 },
  { delta: 0.40, falseBlock: 0.003, falsePass: 0.140 },
  { delta: 0.45, falseBlock: 0.000, falsePass: 0.306 },
  { delta: 0.50, falseBlock: 0.000, falsePass: 0.488 },
  { delta: 0.55, falseBlock: 0.000, falsePass: 0.669 },
  { delta: 0.60, falseBlock: 0.000, falsePass: 0.872 },
  { delta: 0.65, falseBlock: 0.000, falsePass: 1.000 },
];

function Bar({ label, value, color }: { label: string; value: number; color: string }): React.ReactElement {
  return (
    <div style={{ marginBottom: '0.4rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--type-sm)' }}>
        <span>{label}</span>
        <strong>{(value * 100).toFixed(1)}%</strong>
      </div>
      <div style={{ background: 'var(--widget-track, rgba(128,128,128,0.2))', borderRadius: '4px', height: '10px' }}>
        <div
          style={{
            width: `${Math.max(value * 100, value > 0 ? 2 : 0)}%`,
            background: color,
            height: '100%',
            borderRadius: '4px',
            transition: 'width 120ms ease-out',
          }}
        />
      </div>
    </div>
  );
}

export default function EvalGateTradeoff(): React.ReactElement {
  const [index, setIndex] = useState(2);
  const row = SWEEP[index];
  return (
    <div className="learning-widget">
      <label>
        aggregate-delta-over-baseline threshold: <strong>{row.delta.toFixed(2)}</strong>
      </label>
      <input
        type="range"
        min={0}
        max={SWEEP.length - 1}
        step={1}
        value={index}
        onChange={(e) => setIndex(Number(e.target.value))}
        style={{ width: '100%' }}
      />
      <Bar label="false-block rate (safe candidates wrongly blocked)" value={row.falseBlock} color="#c0392b" />
      <Bar label="false-pass rate (unsafe candidates wrongly passed)" value={row.falsePass} color="#e0a800" />
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        n=2000 synthetic candidates, 635 labeled unsafe, category ceiling disabled (1.10) so this
        isolates the one threshold. Tightening it (drag left) drives false blocks toward 0.42 and
        false passes to 0; loosening it (drag right) does the reverse, crossing near 0.35-0.40 --
        the same distance the synthetic ground truth actually used. No setting reaches zero on
        both axes at once; the choice of where to sit on this curve is a policy decision the gate
        mechanism itself cannot make for you.
      </p>
    </div>
  );
}
