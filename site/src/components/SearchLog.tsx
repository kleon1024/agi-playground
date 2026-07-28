/**
 * Why a winning backtest needs its search denominator.
 *
 * The stage 01 run recorded 32 variants and 300 seeded null searches. Change
 * only the number of variants in a deterministic simulated-noise draw: the
 * rising maximum is a selection effect, not market evidence. Defaults are
 * measured stage-01 values; the counterfactual simulation is labelled.
 */
import React, { useMemo, useState } from 'react';

function simulatedBest(variants: number): number {
  let state = 20260727;
  let best = -1;
  for (let index = 0; index < variants; index += 1) {
    state = (state * 1664525 + 1013904223) >>> 0;
    const draw = (state / 0x1_0000_0000 - 0.5) * 0.24;
    best = Math.max(best, draw);
  }
  return best;
}

export default function SearchLog(): React.ReactElement {
  const [variants, setVariants] = useState(32);
  const result = useMemo(() => {
    return simulatedBest(variants);
  }, [variants]);

  return (
    <div className="learning-widget">
      <label style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span>Variants recorded in the search log: <strong>{variants}</strong></span>
        <select
          aria-label="Variants recorded in the search log"
          value={variants}
          onChange={(event) => setVariants(Number(event.target.value))}
        >
          {[1, 8, 16, 32, 64].map((count) => <option key={count} value={count}>{count}</option>)}
        </select>
      </label>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '0.9rem' }}>
        <span>Recorded real-data winner (32 variants): <strong>0.0947 IC</strong></span>
        <span>Simulated-noise best for this variant count: <strong>{result.toFixed(4)} IC</strong></span>
      </div>
      <div style={{ height: '1rem', marginTop: '0.85rem', border: '1px solid var(--rehearse-rule)', background: 'var(--rehearse-paper)' }}>
        <div style={{ width: `${Math.min(100, result / 0.2369 * 100)}%`, height: '100%', background: 'var(--brand-chart-action-fill)', transition: 'width 180ms ease-out' }} />
      </div>
      <p>Measured defaults: 32 logged variants, 300 seeded return permutations, and a real-data best IC of 0.0947. The control is a deterministic simulated-noise illustration, not market data, a recorded null draw, or a new backtest. More opportunities make an attractive maximum easier to find; the JSONL log is the denominator stage 03 needs.</p>
    </div>
  );
}
