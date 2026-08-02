import React, { useState } from 'react';

const WORKER_COUNTS = {
  w2: {
    label: '2 workers (20 lockstep batches)',
    lockstep: 0.0395,
    async: 0.0229,
    speedup: 1.73,
  },
  w4: {
    label: '4 workers (10 lockstep batches)',
    lockstep: 0.0307,
    async: 0.0207,
    speedup: 1.48,
  },
  w8: {
    label: '8 workers (5 lockstep batches)',
    lockstep: 0.0263,
    async: 0.0203,
    speedup: 1.30,
  },
} as const;

type WorkerCount = keyof typeof WORKER_COUNTS;

export default function RolloutSchedulingSpeedup(): React.ReactElement {
  const [count, setCount] = useState<WorkerCount>('w2');
  const w = WORKER_COUNTS[count];
  return (
    <div className="learning-widget">
      <label>
        <input type="radio" checked={count === 'w2'} onChange={() => setCount('w2')} /> 2 workers
      </label>{' '}
      <label>
        <input type="radio" checked={count === 'w4'} onChange={() => setCount('w4')} /> 4 workers
      </label>{' '}
      <label>
        <input type="radio" checked={count === 'w8'} onChange={() => setCount('w8')} /> 8 workers
      </label>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>{w.label}, same 40-trajectory heavy-tailed workload</p>
      <p>lockstep makespan: <strong>{w.lockstep.toFixed(4)}s</strong></p>
      <p>async makespan: <strong>{w.async.toFixed(4)}s</strong></p>
      <p>async speedup: <strong>{w.speedup.toFixed(2)}x</strong></p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        Fewer workers means more sequential lockstep batches over the same 40
        trajectories -- more batch boundaries, more chances for one long-tail
        trajectory to strand its batch-mates idle. Async has no batch
        boundary at all, so its speedup over lockstep is largest at the
        fewest workers and shrinks as worker count rises.
      </p>
    </div>
  );
}
