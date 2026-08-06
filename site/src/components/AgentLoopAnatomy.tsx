/**
 * The agent loop, drawn as its six steps and the diff guardrail.
 *
 * Mission 04 stage 02's "model" is the harness, not one network: materialize
 * the task, capture the baseline, run the agent, read the diff, re-run the
 * tests, score. The guardrail sits between "read diff" and "re-run tests":
 * a diff that touches a test file is a failure regardless of what the tests
 * say, because a tampered record shows every numeric signal as resolved.
 * The recorded harness run (2026-07-29) verified the loop with scripted
 * backends before any model was pointed at it.
 */
import React, { useState } from 'react';

const STEPS = [
  { id: 'materialize', label: 'materialize', detail: 'bug report + failing test' },
  { id: 'baseline', label: 'capture baseline', detail: 'which tests pass before' },
  { id: 'agent', label: 'agent loop', detail: 'prompt, act, observe (bounded)' },
  { id: 'diff', label: 'read diff', detail: 'what changed — guardrail check' },
  { id: 'retest', label: 're-run tests', detail: 'target + no regressions' },
  { id: 'score', label: 'score', detail: 'resolve only if both hold' },
];

const SCENARIOS: Record<string, { label: string; body: string }> = {
  honest: {
    label: 'Honest attempt',
    body: 'The agent edits source only. The diff passes the guardrail, re-running the tests fails the target, and the verdict is target_still_failing — the score says the bug is not fixed.',
  },
  tamper: {
    label: 'Tampering attempt',
    body: 'The agent replaces the failing test with assert True. Every numeric signal says resolved — regressions empty, target_failing_after empty — and only the diff guardrail catches it: a test file was touched, so the verdict is tampered, not resolved.',
  },
};

export default function AgentLoopAnatomy(): React.ReactElement {
  const [scenario, setScenario] = useState('honest');
  const s = SCENARIOS[scenario];
  return (
    <div className="learning-widget">
      <label style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span>Attempt</span>
        <select aria-label="Attempt type" value={scenario} onChange={(e) => setScenario(e.target.value)}>
          {Object.entries(SCENARIOS).map(([key, v]) => (
            <option key={key} value={key}>
              {v.label}
            </option>
          ))}
        </select>
      </label>
      <ol
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.4rem',
          paddingLeft: '0',
          listStyle: 'none',
          margin: '1rem 0',
        }}
      >
        {STEPS.map((step) => (
          <li
            key={step.id}
            title={step.detail}
            style={{
              border: '1px solid var(--rehearse-rule)',
              borderColor: step.id === 'diff' ? 'var(--rehearse-action)' : undefined,
              padding: '0.4rem 0.6rem',
              fontSize: 'var(--type-xs)',
              background: 'var(--rehearse-paper)',
            }}
          >
            <strong>{step.label}</strong>
          </li>
        ))}
      </ol>
      <p style={{ margin: '0.5rem 0' }}>{s.body}</p>
      <p>
        The guardrail is a check on the diff, not on the agent&apos;s own report —
        which is the whole reason mission 04&apos;s scoring design exists. Loop
        structure from the recorded harness end-to-end run (2026-07-29, scripted
        backends, no model).
      </p>
    </div>
  );
}
