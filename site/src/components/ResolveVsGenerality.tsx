import React, { useState } from 'react';

const TIERS = {
  haiku: { resolveRate: '6/6', generality: '0/3', maxError: '4.2e-2', costPerResolved: 0.1604 },
  sonnet: { resolveRate: '6/6', generality: '3/3', maxError: '5.960e-08', costPerResolved: 0.5369 },
  opus: { resolveRate: '6/6', generality: '3/3', maxError: '5.960e-08', costPerResolved: 0.8226 },
} as const;

type Tier = keyof typeof TIERS;

export default function ResolveVsGenerality(): React.ReactElement {
  const [tier, setTier] = useState<Tier>('haiku');
  const t = TIERS[tier];
  return (
    <div className="learning-widget">
      <label>
        model tier{' '}
        <select value={tier} onChange={(e) => setTier(e.target.value as Tier)}>
          <option value="haiku">haiku</option>
          <option value="sonnet">sonnet</option>
          <option value="opus">opus</option>
        </select>
      </label>
      <p>
        resolve rate (passes the given test): <strong>{t.resolveRate}</strong> -- identical across all three tiers
      </p>
      <p>
        patch generality (passes a held-out probe the test does not exercise): <strong>{t.generality}</strong>,
        max observed error <strong>{t.maxError}</strong>
      </p>
      <p>
        cost per resolved task: <strong>${t.costPerResolved.toFixed(4)}</strong>
      </p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        Resolve rate stays flat at 6/6 for every tier -- the metric that looks reassuring does not move.
        Patch generality is what actually separates them: haiku's patch is correct only for the one input
        shape the target test exercises, sonnet's and opus's hold under a probe that changes that shape.
      </p>
    </div>
  );
}
