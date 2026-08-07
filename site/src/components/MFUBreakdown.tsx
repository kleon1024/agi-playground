/**
 * Where the wall-clock went, and what one flag was worth.
 *
 * Both configurations were measured on this repository's local lane during the
 * stage-02 run; the compiled figures are the ones the finished 4.98-hour run
 * sustained. Recorded in
 * 01-language-model/02-pretrain/runs/2026-07-28-pretrain-3b.md.
 *
 * The token-budget control is arithmetic on those measured rates, not a second
 * measurement: doubling the budget did not get run, it gets divided.
 */
import React, { useState } from 'react';

const CONFIGURATIONS = {
  eager: {
    label: 'eager (no torch.compile)',
    tokensPerSecond: 85_500,
    mfu: 33.3,
    note: 'Elementwise work between the matrix multiplies is memory-bound, and every small kernel pays its own launch overhead. The card spends a third of its time doing arithmetic and the rest moving numbers.',
  },
  compiled: {
    label: 'compiled (--compile)',
    tokensPerSecond: 165_600,
    mfu: 64.5,
    note: 'Fusion collapses those elementwise chains into the surrounding kernels, so far fewer launches move far less memory. Nothing about the model or the maths changed.',
  },
} as const;

const BUDGETS = [1e9, 3e9, 10e9];
const ACTUAL_HOURS = 4.98;

export default function MFUBreakdown(): React.ReactElement {
  const [mode, setMode] = useState<keyof typeof CONFIGURATIONS>('compiled');
  const [budget, setBudget] = useState(3e9);
  const config = CONFIGURATIONS[mode];

  const hours = budget / config.tokensPerSecond / 3600;
  const eagerHours = budget / CONFIGURATIONS.eager.tokensPerSecond / 3600;
  const compiledHours = budget / CONFIGURATIONS.compiled.tokensPerSecond / 3600;
  const isRecordedRun = mode === 'compiled' && budget === 3e9;

  return (
    <div className="learning-widget">
      <label>
        Configuration
        <select
          aria-label="Configuration"
          value={mode}
          onChange={(event) => setMode(event.target.value as keyof typeof CONFIGURATIONS)}
        >
          {Object.entries(CONFIGURATIONS).map(([key, entry]) => (
            <option key={key} value={key}>
              {entry.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        Token budget
        <select
          aria-label="Token budget"
          value={budget}
          onChange={(event) => setBudget(Number(event.target.value))}
        >
          {BUDGETS.map((value) => (
            <option key={value} value={value}>
              {(value / 1e9).toFixed(0)}B tokens
            </option>
          ))}
        </select>
      </label>

      <p>
        <strong>{(config.tokensPerSecond / 1000).toFixed(1)}k tokens/second</strong> at{' '}
        <strong>{config.mfu.toFixed(1)}% MFU</strong> — {config.note}
      </p>

      <p>
        {(budget / 1e9).toFixed(0)}B tokens at this rate: <strong>{hours.toFixed(2)} hours</strong>.
        The same budget in the other configuration: {(mode === 'compiled' ? eagerHours : compiledHours).toFixed(2)} hours.
        The gap is {(eagerHours / compiledHours).toFixed(2)}x, and it is the same ratio at every
        budget because both rates are constant.
      </p>

      <p>
        {isRecordedRun ? (
          <>
            This is the run that happened: 3.0B tokens, compiled, <strong>4.98 hours</strong>{' '}
            measured. The 5.03-hour figure above is the arithmetic; the 0.05-hour difference is
            startup, evaluation, and checkpointing that the token rate does not include.
          </>
        ) : (
          <>
            Projection from a measured rate, not a run. Only the compiled 3.0B configuration was
            executed end to end, in {ACTUAL_HOURS} hours.
          </>
        )}
      </p>

      <p>
        MFU is worth watching for the reason this comparison shows: a run can be entirely correct,
        converge exactly as expected, and still waste half the hardware. Nothing in the loss curve
        would have told you.
      </p>
    </div>
  );
}
