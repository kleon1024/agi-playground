import React, { useState } from 'react';

// Three configurations were run, at 5,000 trials each. The cached run used
// parallel recall, so there is no measured serial-plus-cache pair; selecting
// that combination reports the gap rather than borrowing the parallel number.
// Recorded in missions/02-personalized-discovery/08-serving/runs/.
const RUNS = {
  'parallel-0': { mean: 31.22, p95: 49.31, p95Sum: 54.74 },
  'serial-0': { mean: 52.73, p95: 72.71, p95Sum: null as number | null },
  'parallel-80': { mean: 7.0, p95: 34.52, p95Sum: null as number | null },
};

const BUDGET_MS = 300;

export default function LatencyBudget(): React.ReactElement {
  const [recall, setRecall] = useState<'parallel' | 'serial'>('parallel');
  const [cache, setCache] = useState(0);
  const key = `${recall}-${cache}` as keyof typeof RUNS;
  const run = RUNS[key];

  return (
    <div className="learning-widget">
      <label>
        Recall composition
        <select
          aria-label="Recall composition"
          value={recall}
          onChange={(event) => setRecall(event.target.value as 'parallel' | 'serial')}
        >
          <option value="parallel">parallel queues</option>
          <option value="serial">serial queues</option>
        </select>
      </label>

      <label>
        Cache hit rate
        <select
          aria-label="Cache hit rate"
          value={cache}
          onChange={(event) => setCache(Number(event.target.value))}
        >
          <option value={0}>0%</option>
          <option value={80}>80%</option>
        </select>
      </label>

      {run ? (
        <>
          <p>
            Mean <strong>{run.mean.toFixed(2)}ms</strong>, end-to-end p95{' '}
            <strong>{run.p95.toFixed(2)}ms</strong>, against a {BUDGET_MS}ms mission budget. Sampled
            from the harness&rsquo;s per-stage distributions over 5,000 trials.
          </p>
          {run.p95Sum !== null && (
            <p>
              Adding the per-stage p95s gives <strong>{run.p95Sum.toFixed(2)}ms</strong> —{' '}
              {(run.p95Sum - run.p95).toFixed(2)}ms above the actual end-to-end p95. A request is
              slow only when its own draws align in the tail, and separate stages rarely have their
              worst moments on the same request. Means add exactly; tail percentiles do not.
            </p>
          )}
        </>
      ) : (
        <p>
          <strong>Not run.</strong> The cached configuration was executed with parallel recall only,
          so there is no serial-plus-cache measurement to show. Reusing the parallel number here
          would report a cache effect measured under a different critical path.
        </p>
      )}

      <p>
        These are draws from a synthetic per-stage latency model, not timings of a deployed service.
        They establish how stage distributions compose, and nothing about production hardware.
      </p>
    </div>
  );
}
