import React, { useState } from 'react';

const GATES = [
  { key: 'latency', label: 'latency reported at two scales' },
  { key: 'quality', label: 'codec and LM beat both naive baselines' },
  { key: 'gap', label: 'offline-vs-streaming gap reported explicitly' },
  { key: 'runs', label: 'every stage has a runs/ entry' },
  { key: 'reuse', label: 'any change to reused serving code is named' },
] as const;

export default function AcceptanceGatePanel(): React.ReactElement {
  const [checked, setChecked] = useState(GATES.map(() => true));
  const failedIdx = checked.findIndex((c) => !c);
  const verdict = failedIdx === -1 ? 'MET' : `NOT MET: gate '${GATES[failedIdx].label}' failed`;
  return (
    <div className="learning-widget">
      {GATES.map((g, i) => (
        <div key={g.key}>
          <label>
            <input
              type="checkbox"
              checked={checked[i]}
              onChange={() => setChecked((prev) => prev.map((c, j) => (j === i ? !c : c)))}
            />{' '}
            {g.label}
          </label>
        </div>
      ))}
      <p style={{ marginTop: '0.5rem' }}>
        <strong>{verdict}</strong>
      </p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        All 5 gates are real and independently true for mission 07's actual run. Uncheck any one
        to see the verdict flip -- it does not average, it requires all five.
      </p>
    </div>
  );
}
