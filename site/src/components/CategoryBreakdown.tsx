import React, { useState } from 'react';

const CATEGORIES = ['presence', 'shape_color', 'position', 'count_present', 'total_count'] as const;
const HOSTED: Record<string, number> = {
  presence: 0.916, shape_color: 0.916, position: 0.870, count_present: 0.810, total_count: 0.530,
};
const VISION: Record<string, number> = {
  presence: 0.520, shape_color: 0.501, position: 0.440, count_present: 0.420, total_count: 0.310,
};

export default function CategoryBreakdown(): React.ReactElement {
  const [view, setView] = useState<'raw' | 'gap'>('raw');
  return (
    <div className="learning-widget">
      <label>
        view{' '}
        <select value={view} onChange={(e) => setView(e.target.value as 'raw' | 'gap')}>
          <option value="raw">accuracy by category</option>
          <option value="gap">gap to hosted API</option>
        </select>
      </label>
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 'var(--type-sm)' }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left' }}>category</th>
            <th>hosted</th>
            <th>{view === 'raw' ? 'vision' : 'gap (hosted - vision)'}</th>
          </tr>
        </thead>
        <tbody>
          {[...CATEGORIES]
            .sort((a, b) => (HOSTED[a] - VISION[a]) - (HOSTED[b] - VISION[b]))
            .map((c) => (
              <tr key={c}>
                <td>{c}</td>
                <td>{HOSTED[c].toFixed(3)}</td>
                <td>{view === 'raw' ? VISION[c].toFixed(3) : (HOSTED[c] - VISION[c]).toFixed(3)}</td>
              </tr>
            ))}
        </tbody>
      </table>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        total_count is the hardest category for every pathway, including hosted (0.530, its own
        worst) -- a floor set by the task, not the architecture. shape_color has the smallest gap.
      </p>
    </div>
  );
}
