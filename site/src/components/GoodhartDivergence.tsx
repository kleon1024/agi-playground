import React, { useState } from 'react';

const WINDOWS = [
  { start: 0, end: 199, correlation: 0.807, mean_i: 23.22, mean_p: 42.8 },
  { start: 200, end: 399, correlation: -0.998, mean_i: 49.95, mean_p: 105.54 },
  { start: 400, end: 599, correlation: -1.0, mean_i: 50.0, mean_p: 163.71 },
  { start: 600, end: 799, correlation: -1.0, mean_i: 50.0, mean_p: 236.25 },
  { start: 800, end: 999, correlation: -1.0, mean_i: 50.0, mean_p: 317.83 },
  { start: 1000, end: 1199, correlation: -1.0, mean_i: 50.0, mean_p: 396.78 },
  { start: 1200, end: 1399, correlation: -1.0, mean_i: 50.0, mean_p: 469.11 },
  { start: 1400, end: 1599, correlation: -1.0, mean_i: 50.0, mean_p: 554.71 },
  { start: 1600, end: 1799, correlation: -1.0, mean_i: 50.0, mean_p: 633.78 },
  { start: 1800, end: 1999, correlation: -1.0, mean_i: 50.0, mean_p: 715.68 },
];

function phase(idx: number): string {
  if (idx === 0) return 'informativeness (i) still climbing -- proxy and true both rise together';
  if (idx === 1) return 'i has hit its cap of 50 -- padding (p) becomes the only lever left';
  return 'i pinned at cap; every further proxy gain comes only from padding, at true objective\'s expense';
}

export default function GoodhartDivergence(): React.ReactElement {
  const [idx, setIdx] = useState(0);
  const w = WINDOWS[idx];
  return (
    <div className="learning-widget">
      <label>
        window (steps {w.start}-{w.end}) of the proxy-only optimizer{' '}
        <input
          type="range"
          min={0}
          max={WINDOWS.length - 1}
          step={1}
          value={idx}
          onChange={(e) => setIdx(Number(e.target.value))}
        />
      </label>
      <p>
        proxy&ndash;true correlation this window: <strong>{w.correlation.toFixed(3)}</strong>
      </p>
      <p>
        mean informativeness i: <strong>{w.mean_i.toFixed(1)}</strong> / 50 cap &nbsp;|&nbsp; mean padding p:{' '}
        <strong>{w.mean_p.toFixed(1)}</strong>
      </p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>{phase(idx)}</p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        By step 1999 this proxy-only optimizer reaches proxy = 371.85 (up from 0) while the true objective it was
        never shown has fallen to -381.00 (down from 0). A control optimizer given the true objective directly stops
        at true = 70.71 and never touches padding &mdash; same starting point, same step budget, same functions, only
        which one the optimizer can see differs.
      </p>
    </div>
  );
}
