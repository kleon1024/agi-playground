import React, { useState } from 'react';

const regimes = [{name: 'Uptrend', value: 1.4}, {name: 'Range-bound', value: 0.5}, {name: 'Volatility shock', value: -0.8}];
export default function RegimeBreakdown(): React.ReactElement {
  const [selected, setSelected] = useState(0);
  const aggregate = regimes.reduce((sum, r) => sum + r.value, 0) / regimes.length;
  const regime = regimes[selected];
  return <div className="learning-widget">
    <p>Illustrative regime split, not an outcome report. A respectable aggregate can conceal its failing period.</p>
    <label>Inspect regime<select aria-label="Inspect regime" value={selected} onChange={e => setSelected(Number(e.target.value))}>{regimes.map((r, i) => <option key={r.name} value={i}>{r.name}</option>)}</select></label>
    <p>Aggregate Sharpe: <strong>{aggregate.toFixed(2)}</strong>. {regime.name} Sharpe: <strong>{regime.value.toFixed(2)}</strong>.</p>
    <p>The report must name the worst regime and drawdown dates; an aggregate alone cannot decide whether a strategy is acceptable.</p>
  </div>;
}
