import React, { useMemo, useState } from 'react';

const MEASURED = {
  0: { coldCoverage: 100, unionCoverage: 100, retainedAccuracy: 96 },
  65: { coldCoverage: 25, unionCoverage: 72, retainedAccuracy: 100 },
} as const;

type Threshold = keyof typeof MEASURED;

export default function ColdStartCoverage(): React.ReactElement {
  const [threshold, setThreshold] = useState<Threshold>(65);
  const [contentEnabled, setContentEnabled] = useState(true);

  const values = useMemo(() => {
    if (!contentEnabled) {
      return { coldCoverage: 0, unionCoverage: 63, retainedAccuracy: null };
    }
    return MEASURED[threshold];
  }, [contentEnabled, threshold]);

  return (
    <div className="learning-widget">
      <p>
        Predict what happens to cold-item reach before changing the confidence
        threshold. Both threshold choices are measured points from the recorded
        300-item synthetic run; disabling the content queue is the structural
        counterfactual.
      </p>
      <label>
        labeller confidence threshold
        <select
          aria-label="Content labeller confidence threshold"
          value={threshold}
          onChange={(event) => setThreshold(Number(event.target.value) as Threshold)}
        >
          <option value={0}>0.00</option>
          <option value={65}>0.65</option>
        </select>
      </label>
      <label>
        <input
          type="checkbox"
          checked={contentEnabled}
          onChange={() => setContentEnabled((enabled) => !enabled)}
        />
        content queue enabled
      </label>
      <p>
        Cold-item coverage: <strong>{values.coldCoverage}%</strong>. Catalogue
        coverage from the queue union: <strong>{values.unionCoverage}%</strong>.
        Retained-label accuracy:{' '}
        <strong>
          {values.retainedAccuracy === null ? 'not applicable' : `${values.retainedAccuracy}%`}
        </strong>.
      </p>
      <p>
        Behavioural coverage remains 63% because its interaction evidence never
        changes. Raising the threshold discards uncertain tail labels; it does
        not improve the labeller.
      </p>
    </div>
  );
}
