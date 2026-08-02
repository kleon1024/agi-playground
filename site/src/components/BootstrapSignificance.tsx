import React, { useState } from 'react';

const CONDITIONS = {
  '300': {
    scoreA: 0.6933,
    scoreB: 0.5600,
    gap: 0.1333,
    ciLow: 0.0600,
    ciHigh: 0.2067,
    excludesZero: true,
  },
  '25': {
    scoreA: 0.6400,
    scoreB: 0.4400,
    gap: 0.2000,
    ciLow: -0.0400,
    ciHigh: 0.4400,
    excludesZero: false,
  },
} as const;

type Size = keyof typeof CONDITIONS;

export default function BootstrapSignificance(): React.ReactElement {
  const [size, setSize] = useState<Size>('300');
  const r = CONDITIONS[size];
  const other = CONDITIONS[size === '300' ? '25' : '300'];
  return (
    <div className="learning-widget">
      <label>
        <input type="radio" checked={size === '300'} onChange={() => setSize('300')} /> n = 300 items
      </label>{' '}
      <label>
        <input type="radio" checked={size === '25'} onChange={() => setSize('25')} /> n = 25 items
      </label>
      <p>score A: <strong>{r.scoreA.toFixed(4)}</strong>, score B: <strong>{r.scoreB.toFixed(4)}</strong></p>
      <p>observed gap (A &minus; B): <strong>{r.gap.toFixed(4)}</strong></p>
      <p>95% bootstrap CI: <strong>({r.ciLow.toFixed(4)}, {r.ciHigh.toFixed(4)})</strong> &mdash; excludes zero: <strong>{r.excludesZero ? 'yes' : 'no'}</strong></p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        {size === '25'
          ? `This condition's own observed gap (${r.gap.toFixed(4)}) is actually larger than the n=300 condition's (${other.gap.toFixed(4)}) -- same true effect, generated the same way, just fewer items. But the interval is wide enough to include zero: on 25 items alone you cannot rule out "no real difference," even though the point estimate looks bigger.`
          : `At 300 items the same +0.06 true effect produces a 95% interval that sits entirely above zero (${r.ciLow.toFixed(4)} to ${r.ciHigh.toFixed(4)}) -- enough evidence to call the gap real. Switch to 25 items to see the identical effect become statistically indistinguishable from noise.`}
      </p>
    </div>
  );
}
