import React, { useState } from 'react';

const VIEWS = {
  aggregate: { hosted: 0.8329, vision: 0.4375, textOnly: 0.3270 },
  shape_color: { hosted: 0.969, vision: 0.501, textOnly: 0.272 },
} as const;

type View = keyof typeof VIEWS;

export default function BuildVsBuyTradeoff(): React.ReactElement {
  const [view, setView] = useState<View>('aggregate');
  const v = VIEWS[view];
  return (
    <div className="learning-widget">
      <label>
        view{' '}
        <select value={view} onChange={(e) => setView(e.target.value as View)}>
          <option value="aggregate">aggregate accuracy (all categories)</option>
          <option value="shape_color">shape_color only</option>
        </select>
      </label>
      <p>hosted API: <strong>{v.hosted.toFixed(3)}</strong> ($0.00128/question)</p>
      <p>vision pathway: <strong>{v.vision.toFixed(3)}</strong> ($0 marginal)</p>
      <p>text-only baseline: <strong>{v.textOnly.toFixed(3)}</strong> ($0 marginal)</p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        Hosted still leads on both views. shape_color is the category vision separates furthest
        from text-only (an 84% relative lift) -- the strongest evidence the pathway conditions
        on pixels, not question phrasing -- but it does not close the gap to hosted.
      </p>
    </div>
  );
}
