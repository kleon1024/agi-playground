import React, { useState } from 'react';

const CATEGORIES = ['presence', 'shape_color', 'column_shape', 'shape_count', 'total_count'] as const;
const HOSTED: Record<string, number> = {
  presence: 0.916, shape_color: 0.969, column_shape: 0.812, shape_count: 0.762, total_count: 0.530,
};
const VISION: Record<string, number> = {
  presence: 0.574, shape_color: 0.501, column_shape: 0.350, shape_count: 0.432, total_count: 0.373,
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
        worst) -- a floor set by the task, not the architecture. It also has the smallest gap to
        hosted (15.7pp); shape_color has the largest (46.8pp), despite being where vision most
        clearly separates from text-only in absolute terms.
      </p>
    </div>
  );
}
