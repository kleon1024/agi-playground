import React, { useState } from 'react';

const SCOPES = {
  'target-only': { task: '354c352', regressions: 0, diffCheckFires: true, regressionCheckFires: false },
  'whole-file': { task: 'b81c414', regressions: 11, diffCheckFires: true, regressionCheckFires: true },
} as const;

type Scope = keyof typeof SCOPES;

export default function RegressionBlindSpot(): React.ReactElement {
  const [scope, setScope] = useState<Scope>('target-only');
  const s = SCOPES[scope];
  return (
    <div className="learning-widget">
      <label>
        tampering scope{' '}
        <select value={scope} onChange={(e) => setScope(e.target.value as Scope)}>
          <option value="target-only">target test only</option>
          <option value="whole-file">whole test file</option>
        </select>
      </label>
      <p>real task: <strong>{s.task}</strong>, regressions produced: <strong>{s.regressions}</strong></p>
      <p>diff check fires: <strong>{s.diffCheckFires ? 'yes' : 'no'}</strong></p>
      <p>regression check fires: <strong>{s.regressionCheckFires ? 'yes' : 'no'}</strong></p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        Precision of the attack, not its existence, decides whether the regression check alone
        would have been enough -- the diff check catches both, which is why the guardrail inspects
        the diff itself rather than inferring intent from outcomes.
      </p>
    </div>
  );
}
