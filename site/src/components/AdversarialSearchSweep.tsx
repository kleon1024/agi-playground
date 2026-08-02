import React, { useState } from 'react';

const BUDGET_SWEEP = [
  { budget: 1, flipRate: 0.706, meanAttempts: 1.0 },
  { budget: 2, flipRate: 0.924, meanAttempts: 1.24 },
  { budget: 5, flipRate: 0.996, meanAttempts: 1.38 },
  { budget: 10, flipRate: 1.0, meanAttempts: 1.4 },
  { budget: 20, flipRate: 1.0, meanAttempts: 1.4 },
  { budget: 50, flipRate: 1.0, meanAttempts: 1.4 },
  { budget: 100, flipRate: 1.0, meanAttempts: 1.4 },
] as const;

// Fixed budget=20. Operator-space size 1 is case-flip only, which the toy
// filter is structurally invariant to (it lowercases before matching) --
// confirmed flat at 0.000 even at budget=1000 in the run record.
const OPERATOR_SWEEP = [
  { size: 1, flipRate: 0.0, label: 'case-flip only' },
  { size: 2, flipRate: 1.0, label: '+ homoglyph' },
  { size: 3, flipRate: 1.0, label: '+ separator insert' },
  { size: 4, flipRate: 1.0, label: '+ char duplicate' },
] as const;

function Bar({ value }: { value: number }): React.ReactElement {
  return (
    <div style={{ background: 'var(--widget-track, rgba(128,128,128,0.2))', borderRadius: '4px', height: '10px', margin: '0.3rem 0' }}>
      <div
        style={{
          width: `${Math.max(value * 100, value > 0 ? 2 : 0)}%`,
          background: value === 0 ? '#c0392b' : '#2e8b57',
          height: '100%',
          borderRadius: '4px',
          transition: 'width 120ms ease-out',
        }}
      />
    </div>
  );
}

export default function AdversarialSearchSweep(): React.ReactElement {
  const [budgetIndex, setBudgetIndex] = useState(3);
  const [opSize, setOpSize] = useState<1 | 2 | 3 | 4>(4);
  const budgetRow = BUDGET_SWEEP[budgetIndex];
  const opRow = OPERATOR_SWEEP[opSize - 1];

  return (
    <div className="learning-widget">
      <label>
        search budget (all 4 operators): <strong>{budgetRow.budget}</strong> attempt(s)
      </label>
      <input
        type="range"
        min={0}
        max={BUDGET_SWEEP.length - 1}
        step={1}
        value={budgetIndex}
        onChange={(e) => setBudgetIndex(Number(e.target.value))}
        style={{ width: '100%' }}
      />
      <p style={{ fontSize: 'var(--type-sm)', margin: '0.2rem 0' }}>
        flip rate: <strong>{(budgetRow.flipRate * 100).toFixed(1)}%</strong>
        {budgetRow.flipRate > 0 && <> (mean {budgetRow.meanAttempts.toFixed(2)} attempts when it flips)</>}
      </p>
      <Bar value={budgetRow.flipRate} />

      <label style={{ display: 'block', marginTop: '1rem' }}>
        perturbation-space size (fixed budget=20):{' '}
        <strong>{opSize} operator{opSize > 1 ? 's' : ''}</strong> ({opRow.label})
      </label>
      <input
        type="range"
        min={1}
        max={4}
        step={1}
        value={opSize}
        onChange={(e) => setOpSize(Number(e.target.value) as 1 | 2 | 3 | 4)}
        style={{ width: '100%' }}
      />
      <p style={{ fontSize: 'var(--type-sm)', margin: '0.2rem 0' }}>
        flip rate: <strong>{(opRow.flipRate * 100).toFixed(1)}%</strong>
      </p>
      <Bar value={opRow.flipRate} />

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.5rem' }}>
        {opSize === 1
          ? 'At operator-space size 1 (case-flip only), flip rate stays exactly 0% at every budget -- confirmed flat even at budget=1000 in the run record. The filter lowercases before matching, so this operator can never change its decision, no matter how many attempts it gets.'
          : 'Adding just one operator the filter is not invariant to (homoglyph substitution) jumps flip rate from 0% to 100% -- search budget cannot compensate for a perturbation space missing the one operator that actually works against this system.'}
      </p>
    </div>
  );
}
