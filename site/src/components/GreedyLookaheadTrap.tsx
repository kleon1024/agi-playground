import React, { useState } from 'react';

// A 5x5 grid where a wall segment forces a detour: agent at (0,0), goal at
// (0,4), wall blocks the direct row. Greedy (pure Manhattan descent, no
// memory) oscillates against the wall instead of routing around it.
const GRID_SIZE = 5;
const START = { row: 0, col: 0 };
const GOAL = { row: 0, col: 4 };
const WALL: [number, number][] = [
  [0, 2], [1, 2], [2, 2],
];

function isWall(row: number, col: number): boolean {
  return WALL.some(([r, c]) => r === row && c === col);
}

const ACTIONS = ['U', 'D', 'L', 'R'] as const;
function step(pos: { row: number; col: number }): { row: number; col: number } {
  let best = pos;
  let bestDist = Infinity;
  for (const a of ACTIONS) {
    const cand = { ...pos };
    if (a === 'U') cand.row -= 1;
    if (a === 'D') cand.row += 1;
    if (a === 'L') cand.col -= 1;
    if (a === 'R') cand.col += 1;
    if (cand.row < 0 || cand.row >= GRID_SIZE || cand.col < 0 || cand.col >= GRID_SIZE) continue;
    if (isWall(cand.row, cand.col)) continue;
    const dist = Math.abs(cand.row - GOAL.row) + Math.abs(cand.col - GOAL.col);
    if (dist < bestDist) {
      bestDist = dist;
      best = cand;
    }
  }
  return best;
}

export default function GreedyLookaheadTrap(): React.ReactElement {
  const [history, setHistory] = useState([START]);
  const pos = history[history.length - 1];
  const atGoal = pos.row === GOAL.row && pos.col === GOAL.col;
  return (
    <div className="learning-widget">
      <button
        onClick={() => setHistory((h) => [...h, step(h[h.length - 1])])}
        disabled={atGoal || history.length > 12}
      >
        step
      </button>{' '}
      <button onClick={() => setHistory([START])}>reset</button>
      <p>steps taken: {history.length - 1}, position: ({pos.row}, {pos.col}){atGoal ? ' -- reached goal' : ''}</p>
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${GRID_SIZE}, 24px)`, gap: 2, marginTop: '0.5rem' }}>
        {Array.from({ length: GRID_SIZE }, (_, row) =>
          Array.from({ length: GRID_SIZE }, (_, col) => {
            const here = pos.row === row && pos.col === col;
            const wall = isWall(row, col);
            const goal = row === GOAL.row && col === GOAL.col;
            return (
              <div
                key={`${row}-${col}`}
                style={{
                  width: 24,
                  height: 24,
                  border: '1px solid var(--rehearse-rule)',
                  background: wall ? 'var(--rehearse-ink)' : here ? 'var(--brand-chart-positive-fill)' : goal ? 'var(--brand-chart-warning-fill)' : undefined,
                }}
              />
            );
          })
        )}
      </div>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.5rem' }}>
        Greedy has no memory and only ever picks the action that reduces distance right now.
        With a wall directly between agent and goal, no candidate action reduces distance, so it
        oscillates against the wall's near side instead of detouring around it.
      </p>
    </div>
  );
}
