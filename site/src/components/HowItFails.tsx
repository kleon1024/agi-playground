import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'harness',
    carries: '18/18 resolved',
    label: 'Full harness',
    owns: 'Every failure category reads 0/18: on this task set the full harness failure surface is empty.',
    handoff: 'A real result — not a gap in what the chapter looked for.',
  },
  {
    id: 'blind',
    carries: '4/18 resolved',
    label: 'No-harness arm',
    owns: 'Without the loop, four of eighteen attempts resolve and the failure row stops being empty.',
    handoff: 'The failures cluster where the harness was removed, not spread across categories.',
  },
  {
    id: 'neverapplied',
    carries: '12/18 target_still_failing',
    label: 'Never applied',
    owns: 'Eleven of the twelve unresolved diffs git apply rejected outright before any test ran again — the model miscounted its own patch.',
    handoff: 'The refusal is the harness working, not failing: only one diff applied and still did not fix the bug.',
  },
  {
    id: 'untested',
    carries: '0/18 tampered',
    label: 'The guardrail not yet asked',
    owns: 'Tampering reads 0/18 in both arms, so the guardrail has not yet been asked a hard enough question.',
    handoff: 'The empty tampered row is evidence of scope, not of a guardrail that can never fire.',
  },
];

export default function HowItFails(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="One table built from every real attempt, no new model calls"
      question="How does it fail, and does it cheat?"
      steps={STEPS}
      loop="The full harness arm reads 18/18 with every failure category at 0/18; the no-harness arm reads 4/18 with 12/18 target_still_failing — eleven of those never applying at all. Tampering is 0/18 in both arms, so the guardrail evidence so far says the task set did not ask the question, not that the guardrail cannot answer it."
    />
  );
}
