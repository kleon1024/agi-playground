/**
 * More agents is not free -- and the honest comparison holds total cost equal.
 *
 * Every topology below is judged against the same reference: one agent doing
 * the identical bounded work directly, with no delegation at all. Switching
 * the topology changes four things at once -- total token cost, wall-clock
 * steps, how much of the *parent's* context fills up, and how many lossy
 * handoffs the result crosses -- and they do not all move the same direction.
 * Supervisor-with-workers can cut wall-clock while raising token cost. A
 * debate panel spends parent context on purpose, to buy an independent
 * perspective, rather than saving it the way delegation usually does.
 *
 * All numbers here are illustrative: derived from a small set of stated
 * constants (a per-unit cost, a per-handoff tax, a per-dispatch overhead),
 * not measured from a run. Nothing here is randomized, so the same inputs
 * always render the same output.
 */
import React, { useState } from 'react';

type Topology = 'single' | 'supervisor' | 'pipeline' | 'panel';

// Illustrative constants only -- see the module docstring. Chosen to be
// legible round numbers, not fit to any observed system.
const BASE_UNIT_TOKENS = 400; // one agent doing one bounded unit of work
const HANDOFF_TAX_TOKENS = 150; // one parent<->child serialization boundary
const DISPATCH_OVERHEAD_TOKENS = 80; // per-task bookkeeping a supervisor writes
const MAX_CONCURRENCY = 4; // illustrative ceiling on simultaneous workers

interface Metrics {
  totalTokens: number;
  wallClockSteps: number;
  parentContextTokens: number;
  handoffs: number;
}

function singleAgent(units: number): Metrics {
  return {
    totalTokens: units * BASE_UNIT_TOKENS,
    wallClockSteps: units,
    parentContextTokens: units * BASE_UNIT_TOKENS,
    handoffs: 0,
  };
}

function metricsFor(topology: Topology, n: number): Metrics {
  if (topology === 'single') return singleAgent(n);

  if (topology === 'supervisor') {
    const handoffs = 2 * n; // dispatch to worker, structured result back
    return {
      totalTokens: n * BASE_UNIT_TOKENS + n * DISPATCH_OVERHEAD_TOKENS + handoffs * HANDOFF_TAX_TOKENS,
      wallClockSteps: Math.ceil(n / MAX_CONCURRENCY) + 1, // parallel batches + one integration step
      parentContextTokens: n * DISPATCH_OVERHEAD_TOKENS + n * HANDOFF_TAX_TOKENS,
      handoffs,
    };
  }

  if (topology === 'pipeline') {
    const handoffs = Math.max(0, n - 1);
    return {
      totalTokens: n * BASE_UNIT_TOKENS + handoffs * HANDOFF_TAX_TOKENS,
      wallClockSteps: n, // strictly sequential, no parallelism to exploit
      parentContextTokens: BASE_UNIT_TOKENS + HANDOFF_TAX_TOKENS, // only the final stage's live handoff
      handoffs,
    };
  }

  // panel: n independent full attempts at the *same* one unit of work, then
  // a judge compares them -- this is why it doesn't reuse singleAgent(n).
  const handoffs = n;
  return {
    totalTokens: n * BASE_UNIT_TOKENS + handoffs * HANDOFF_TAX_TOKENS + DISPATCH_OVERHEAD_TOKENS,
    wallClockSteps: 2, // every panelist concurrently, then one judge pass
    parentContextTokens: n * BASE_UNIT_TOKENS, // the judge must read every full attempt
    handoffs,
  };
}

const TOPOLOGIES: { id: Topology; label: string; caption: string }[] = [
  { id: 'single', label: 'Single agent', caption: 'n = bounded units of work, done in sequence' },
  { id: 'supervisor', label: 'Supervisor + workers', caption: 'n = independent subtasks dispatched to workers' },
  { id: 'pipeline', label: 'Pipeline', caption: 'n = sequential stages, each feeding the next' },
  { id: 'panel', label: 'Debate / panel', caption: 'n = independent agents attempting the same one task' },
];

function fmt(n: number): string {
  return n.toLocaleString();
}

export default function AgentTopology(): React.ReactElement {
  const [topology, setTopology] = useState<Topology>('supervisor');
  const [n, setN] = useState(5);

  const selected = metricsFor(topology, n);
  const baselineUnits = topology === 'panel' ? 1 : n;
  const baseline = singleAgent(baselineUnits);
  const equivalentUnits = (selected.totalTokens / BASE_UNIT_TOKENS).toFixed(1);
  const costMultiple = selected.totalTokens / baseline.totalTokens;
  const maxTokens = Math.max(selected.totalTokens, baseline.totalTokens);
  const current = TOPOLOGIES.find((t) => t.id === topology)!;

  return (
    <div className="learning-widget">
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.9rem' }} role="group" aria-label="Topology">
        {TOPOLOGIES.map((t) => (
          <button
            key={t.id}
            type="button"
            aria-pressed={t.id === topology}
            onClick={() => setTopology(t.id)}
            style={{
              background: t.id === topology ? 'var(--brand-chart-action-fill)' : undefined,
              borderColor: t.id === topology ? 'var(--brand-chart-action)' : undefined,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      <label style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', marginBottom: '0.4rem' }}>
        <span>n = <strong>{n}</strong></span>
        <input
          type="range"
          min={2}
          max={8}
          step={1}
          value={n}
          onChange={(e) => setN(Number(e.target.value))}
          aria-label="Number of independent units"
        />
      </label>
      <p style={{ fontSize: 'var(--type-xs)', color: 'var(--rehearse-copy-muted)', marginTop: 0, marginBottom: '0.9rem' }}>
        {current.caption}
      </p>

      <div style={{ display: 'flex', height: 30, borderRadius: 4, overflow: 'hidden', fontSize: 'var(--type-xs)', marginBottom: '0.3rem' }}
           aria-hidden="true">
        <div style={{ width: `${(baseline.totalTokens / maxTokens) * 100}%`, background: 'var(--brand-chart-action-fill)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--rehearse-ink)',
                      transition: 'width 220ms ease-out' }}>
          {baseline.totalTokens / maxTokens > 0.18 ? `baseline ${fmt(baseline.totalTokens)}` : ''}
        </div>
      </div>
      <div style={{ display: 'flex', height: 30, borderRadius: 4, overflow: 'hidden', fontSize: 'var(--type-xs)', marginBottom: '0.9rem' }}
           aria-hidden="true">
        <div style={{ width: `${(selected.totalTokens / maxTokens) * 100}%`,
                      background: selected.totalTokens > baseline.totalTokens ? 'var(--brand-chart-danger-fill)' : 'var(--brand-chart-positive-fill)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--rehearse-ink)',
                      transition: 'width 220ms ease-out, background 220ms' }}>
          {selected.totalTokens / maxTokens > 0.18 ? `${current.label} ${fmt(selected.totalTokens)}` : ''}
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Metric (illustrative)</th>
              <th style={{ textAlign: 'right' }}>Single agent (baseline)</th>
              <th style={{ textAlign: 'right' }}>{current.label}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Total tokens</td>
              <td style={{ textAlign: 'right' }}>{fmt(baseline.totalTokens)}</td>
              <td style={{ textAlign: 'right' }}>{fmt(selected.totalTokens)}</td>
            </tr>
            <tr>
              <td>Wall-clock steps</td>
              <td style={{ textAlign: 'right' }}>{baseline.wallClockSteps}</td>
              <td style={{ textAlign: 'right' }}>{selected.wallClockSteps}</td>
            </tr>
            <tr>
              <td>Context filled in the parent</td>
              <td style={{ textAlign: 'right' }}>{fmt(baseline.parentContextTokens)}</td>
              <td style={{ textAlign: 'right' }}>{fmt(selected.parentContextTokens)}</td>
            </tr>
            <tr>
              <td>Lossy handoffs</td>
              <td style={{ textAlign: 'right' }}>{baseline.handoffs}</td>
              <td style={{ textAlign: 'right' }}>{selected.handoffs}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p>
        {current.label} spends <strong>{costMultiple.toFixed(2)}x</strong> the
        baseline's tokens on {topology === 'panel' ? 'this one task' : `these ${n} units`}. At
        that same total spend, a single agent with no delegation at all could
        instead complete <strong>{equivalentUnits}</strong> bounded units of
        work directly. Wall-clock and token cost are different axes -- a
        topology can win one and lose the other -- which is why the
        comparison that matters holds total spend equal rather than counting
        agents.
      </p>
    </div>
  );
}
