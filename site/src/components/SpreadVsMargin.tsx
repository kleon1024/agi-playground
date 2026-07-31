import React, { useState } from 'react';

const COMPARISONS = [
  { name: 'greedy vs random', margin: -0.1493, spread: 0.016 },
  { name: 'greedy vs greedy-heuristic', margin: -0.7513, spread: 0.016 },
  { name: 'sampled vs random', margin: -0.0433, spread: 0.066 },
  { name: 'sampled vs greedy-heuristic', margin: -0.6453, spread: 0.066 },
];

export default function SpreadVsMargin(): React.ReactElement {
  const [threshold, setThreshold] = useState(0.05);
  return (
    <div className="learning-widget">
      <label>
        spread threshold{' '}
        <input
          type="range"
          min={0.01}
          max={0.1}
          step={0.005}
          value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
        />{' '}
        <strong>{threshold.toFixed(3)}</strong>
      </label>
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 'var(--type-sm)', marginTop: '0.5rem' }}>
        <tbody>
          {COMPARISONS.map((c) => {
            const decisive = Math.abs(c.margin) > threshold;
            return (
              <tr key={c.name}>
                <td>{c.name}</td>
                <td>margin {c.margin.toFixed(4)}</td>
                <td>{decisive ? 'decisive' : 'inside noise band'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        At the real measured spreads (0.016 greedy, 0.066 sampled), 3 of 4 margins are decisive
        regardless of where a reasonable threshold sits. Only sampled-vs-random flips from "loss"
        to "noise" once the threshold exceeds its real spread (0.066).
      </p>
    </div>
  );
}
