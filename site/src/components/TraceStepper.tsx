import React, { useEffect, useState } from 'react';

/**
 * The real agent trace for private-354c352, captured 2026-08-14 from
 * `claude -p --model haiku` on the mission harness. Each step is one
 * decision the model made, the tool call that followed it, or the result
 * it observed -- the loop, shown as it actually ran. Run record:
 * 04-agentic-platform/agent-loop/runs/2026-08-14-trace-354c352.md
 */

type StepKind = 'decide' | 'act' | 'observe';

interface TraceStep {
  kind: StepKind;
  heading: string;
  model?: string;
  tool?: string;
  input?: string;
  observed?: string;
  note?: string;
}

const STEPS: TraceStep[] = [
  {
    kind: 'decide',
    heading: 'The model decides to read the tests first',
    model:
      "I'll start by examining the failing tests to understand what they expect.",
  },
  {
    kind: 'act',
    heading: 'Read the failing test file',
    tool: 'Read',
    input: '{"file_path": "tests/test_sync_docs.py"}',
    observed:
      'The file defines 13 tests. The two that matter assert that angle brackets inside inline code survive verbatim: "`<|im_start|>`" must stay literal, and "`<1,000 lines is prose`" must not become "&lt;".',
    note: '13 tests, two of them the task target; observation truncated from the run record.',
  },
  {
    kind: 'decide',
    heading: 'The model decides to read the implementation',
    model:
      'Now let me look at the sync_docs.py file to see the current implementation of the escape_mdx function.',
  },
  {
    kind: 'act',
    heading: 'Read site/sync-docs.py',
    tool: 'Read',
    input: '{"file_path": "site/sync-docs.py"}',
    observed:
      'escape_mdx escapes "<" outside fenced code blocks, stepping over ``` fences. The function has no concept of inline code (backticks).',
    note: 'The bug is in this function; observation truncated from the run record.',
  },
  {
    kind: 'decide',
    heading: 'The model decides to reproduce the failure',
    model:
      'Looking at the tests, I need to examine what escape_mdx currently does and what the tests expect. Let me run the failing tests first.',
  },
  {
    kind: 'act',
    heading: 'Run the two failing tests',
    tool: 'Bash',
    input:
      '{"command": "uv run pytest -xvs tests/test_sync_docs.py::test_angle_brackets_survive_inline_code_verbatim tests/test_sync_docs.py::test_fenced_and_inline_code_are_both_stepped_over"}',
    observed:
      "FAILED test_angle_brackets_survive_inline_code_verbatim -- AssertionError: inline code must be left alone. assert '`<|im_start|>`' in 'The bytes `&lt;|im_start|>` mark a turn, and &lt;1,000 lines is prose.'",
    note: 'The exact failure the task exists to fix, reproduced before any edit.',
  },
  {
    kind: 'decide',
    heading: 'The model identifies the mechanism',
    model:
      'Now I understand the issue. The escape_mdx function handles fenced code blocks but does not handle inline code (backtick-enclosed text). I need to modify it to skip escaping characters inside inline code spans.',
  },
  {
    kind: 'act',
    heading: 'Edit escape_mdx to step over inline code',
    tool: 'Edit',
    input:
      '{"file_path": "site/sync-docs.py", "old_string": "def escape_mdx(text: str) -> str: ...", "new_string": "def escape_mdx(text: str) -> str: ... split each line by backticks; escape only even (outside) segments ..."}',
    observed: 'The file has been updated successfully.',
  },
  {
    kind: 'decide',
    heading: 'The model decides to verify the fix',
    model: 'Now let me run the tests to verify the fix.',
  },
  {
    kind: 'act',
    heading: 'Run the full test file',
    tool: 'Bash',
    input: '{"command": "uv run pytest -q tests/test_sync_docs.py"}',
    observed: '............. [100%] 13 passed in 0.04s',
  },
  {
    kind: 'decide',
    heading: 'The model decides nothing regressed elsewhere',
    model:
      'Perfect! All tests now pass. Let me verify once more with the full test run to make sure nothing broke.',
  },
  {
    kind: 'act',
    heading: 'Re-run with full detail as a regression check',
    tool: 'Bash',
    input: '{"command": "uv run pytest tests/test_sync_docs.py -v"}',
    observed:
      '13 passed -- including test_angle_brackets_survive_inline_code_verbatim and test_fenced_and_inline_code_are_both_stepped_over.',
    note: 'The loop does not stop at a green target test; it re-checks the whole file.',
  },
];

const KIND_LABEL: Record<StepKind, string> = {
  decide: 'decides',
  act: 'acts',
  observe: 'observes',
};

export default function TraceStepper(): React.ReactElement {
  const [index, setIndex] = useState(0);
  const [showDetail, setShowDetail] = useState(false);
  const step = STEPS[index];

  const go = (delta: number) => {
    setIndex(Math.max(0, Math.min(STEPS.length - 1, index + delta)));
    setShowDetail(false);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') go(1);
      if (e.key === 'ArrowLeft') go(-1);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  return (
    <div className="learning-widget">
      <p>
        Step <strong>{index + 1}</strong> of {STEPS.length} — the model{' '}
        <strong>{KIND_LABEL[step.kind]}</strong>
      </p>
      <h3>{step.heading}</h3>
      {step.model ? <p>{step.model}</p> : null}
      {step.tool ? (
        <div style={{ fontSize: 'var(--type-sm)' }}>
          <p>
            Tool: <strong>{step.tool}</strong>
          </p>
          <pre
            style={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              maxHeight: showDetail ? 'none' : '8em',
              overflowY: 'auto',
              background: 'var(--surface-muted)',
              padding: '0.6em',
              borderRadius: '6px',
            }}
          >
            {step.input}
          </pre>
        </div>
      ) : null}
      {step.observed ? (
        <div style={{ fontSize: 'var(--type-sm)' }}>
          <p>
            <strong>Observed:</strong> {step.observed}
          </p>
          {step.note ? (
            <p style={{ opacity: 0.75 }}>
              <button
                type="button"
                onClick={() => setShowDetail(!showDetail)}
                aria-expanded={showDetail}
                style={{ minHeight: '44px', marginRight: '0.6em' }}
              >
                {showDetail ? 'hide' : 'show'} full tool input
              </button>
              {step.note}
            </p>
          ) : null}
        </div>
      ) : null}
      <div
        style={{
          display: 'flex',
          gap: '0.6em',
          alignItems: 'center',
          marginTop: '0.8em',
        }}
      >
        <button
          type="button"
          onClick={() => go(-1)}
          disabled={index === 0}
          style={{ minHeight: '44px' }}
        >
          previous step
        </button>
        <button
          type="button"
          onClick={() => go(1)}
          disabled={index === STEPS.length - 1}
          style={{ minHeight: '44px' }}
        >
          next step
        </button>
        <span style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
          arrow keys also step through
        </span>
      </div>
    </div>
  );
}
