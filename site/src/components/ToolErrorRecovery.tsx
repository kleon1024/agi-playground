/**
 * When the tool errors, who teaches the recovery turn?
 *
 * The audit (runs/2026-08-07-recovery-audit.md) injects every way the three
 * real stage-06 tools can fail and plays two policies over the seven
 * resulting classes: a blind-retry policy (re-issue the exact same call) and
 * a recovery-planner policy (a fixed per-class action, executed for real).
 * Blind retry resolves 0/7 — every retry returns the identical failing
 * observation. The planner resolves 7/7, and its seven actions fall into
 * three families: inspect, re-scope, and make it safe to redo.
 *
 * Two of the seven failures are returned, not raised — the model has to
 * notice them on its own, because nothing points at them.
 */
import React, { useState } from 'react';

interface FailureClass {
  name: string;
  kind: 'raised' | 'returned';
  firstLine: string;
  family: 'inspect' | 're-scope' | 'make it safe to redo';
  recovery: string;
  note: string;
}

const CLASSES: FailureClass[] = [
  {
    name: 'missing file',
    kind: 'raised',
    firstLine: "ToolError: not a file: 'no-such-file.md'",
    family: 'inspect',
    recovery: 'list_dir — find what actually exists before choosing the next action',
    note: 'The error names what is not where you thought. The recovery is information gathering, not another attempt at the same guess.',
  },
  {
    name: 'wrong directory',
    kind: 'raised',
    firstLine: "ToolError: not a directory: 'no-such-dir/'",
    family: 'inspect',
    recovery: 'list_dir — locate the real path',
    note: 'Same family as missing file: something is not where you thought, so the next turn reads the filesystem.',
  },
  {
    name: 'metacharacter refused',
    kind: 'raised',
    firstLine: "ToolError: command contains a shell metacharacter, refused: 'ec…'",
    family: 're-scope',
    recovery: 'run_command with a single allowlisted command instead of a shell chain',
    note: 'The call was wrong-sized, not the world. Express the command differently.',
  },
  {
    name: 'command not allowlisted',
    kind: 'raised',
    firstLine: "ToolError: 'rm' is not in the command allowlist ['cat', 'echo', …]",
    family: 'inspect',
    recovery: 'list_dir — the refusal itself names what is allowed',
    note: 'The observation carries the contract the model should have read before calling: inspect what is permitted, then re-scope the request.',
  },
  {
    name: 'timeout',
    kind: 'raised',
    firstLine: "ToolError: command timed out after 1.0s: 'python3 slow.py'",
    family: 're-scope',
    recovery: 'a shorter command; check state before re-running anything',
    note: 'Also the already-executed trap: the audit ran a command that writes a marker file and then sleeps — the timeout killed it after the write landed, and the observation cannot tell you that.',
  },
  {
    name: 'non-zero exit',
    kind: 'returned',
    firstLine: 'exit=1 plus a traceback, as an ordinary observation',
    family: 'inspect',
    recovery: 'read_file — read the failing source before re-running',
    note: 'Returned, not raised: the harness does not throw, so the model has to notice the failure itself — nothing points at it.',
  },
  {
    name: 'output truncated',
    kind: 'returned',
    firstLine: 'first 8,000 bytes plus a truncation marker',
    family: 're-scope',
    recovery: 'grep or head a slice instead of a full read',
    note: 'Returned, not raised: the observation is an ordinary successful-looking one with a marker embedded in it.',
  },
];

export default function ToolErrorRecovery(): React.ReactElement {
  const [selected, setSelected] = useState(0);
  const at = CLASSES[selected];

  return (
    <div className="learning-widget">
      <p>
        Seven failure classes the three real tools return. Blind retry resolves
        none of them — every retry pays the same failed turn again. The
        recovery planner resolves all seven, and the seven actions are three
        families. Select a class and read its actual observation.
      </p>

      <div
        role="group"
        aria-label="Failure class"
        style={{ display: 'flex', gap: '0.45rem', flexWrap: 'wrap', margin: '0.9rem 0' }}
      >
        {CLASSES.map((c, index) => (
          <button
            key={c.name}
            type="button"
            aria-pressed={selected === index}
            onClick={() => setSelected(index)}
            style={{
              padding: '0.4rem 0.6rem',
              background: selected === index ? 'var(--rehearse-action-soft)' : undefined,
              borderColor: selected === index ? 'var(--rehearse-action)' : undefined,
            }}
          >
            {c.name}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gap: '0.6rem' }}>
        {[
          ['Kind', at.kind === 'raised' ? 'raised (ToolError fed back as an observation)' : 'returned (ordinary observation — the model must notice on its own)'],
          ['First line of the observation', at.firstLine],
          ['Blind retry', 'no — the identical failing observation, every time'],
          ['Recovery family', at.family],
          ['Recovery action', at.recovery],
        ].map(([label, value]) => (
          <div key={label} style={{ border: '1px solid var(--rehearse-rule)', padding: '0.55rem 0.7rem' }}>
            <div style={{ fontSize: 'var(--type-xs)', opacity: 0.65 }}>{label}</div>
            <div style={{ fontSize: 'var(--type-sm)' }}>{value}</div>
          </div>
        ))}
      </div>

      <p style={{ marginTop: '0.75rem' }}>{at.note}</p>

      <p>
        The three families transfer to any tool set: inspect when the failure
        says something is not where you thought (list or read before acting
        again), re-scope when the call was wrong-sized (express it
        differently), and make it safe to redo when something may already have
        happened — the class blind retry is actively dangerous on, which is
        why the timeout gets idempotency or a state inspection before
        re-running. A corpus filtered to clean successes contains zero of
        these turns, which is why recovery has to be in the imitation data:
        PALADIN (arXiv:2509.25238, 2025) lifted LLaMA-8B tool success from
        17.5% to 78.7% by injecting failures into recovery-annotated
        trajectories against a model trained on success-only ones.
      </p>
    </div>
  );
}
