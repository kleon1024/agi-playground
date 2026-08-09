import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'harness',
    carries: '18/18 resolved',
    label: 'Full harness',
    owns: 'Stage 03 with tools, a real test command, and up to 25 steps of feedback.',
    handoff: 'Every tier resolves everything it attempts.',
  },
  {
    id: 'blind',
    carries: '4/18 resolved',
    label: 'One blind call',
    owns: 'One claude -p per attempt, every tool denied by name, no retry and no way to check its own work.',
    handoff: 'A lower-resolving arm that still has to pay for every attempt.',
  },
  {
    id: 'oracle',
    carries: 'haiku 0/6, sonnet 1/6, opus 3/6',
    label: 'Oracle file location',
    owns: 'The prompt names exactly the files the gold patch touches, so this measures fixing, not finding.',
    handoff: 'Even told where the bug is, the blind arm resolves less than a third of attempts.',
  },
  {
    id: 'cost',
    carries: '$1.3744 vs $0.5369',
    label: 'Cost per resolved',
    owns: 'A lower resolve rate is not a cheaper one: sonnet blind resolves 1/6 at $1.3744 per resolved task, above its own harness rate.',
    handoff: 'The five unresolved attempts still spent real dollars, so cost-per-resolved punishes the blind arm harder than resolve rate alone.',
  },
];

export default function NoHarness(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="One loop, one blind call, four resolved"
      question="Is the loop worth anything over one blind model call?"
      steps={STEPS}
      loop="The harness resolves 18/18; the blind arm 4/18, and the comparison flatters neither arm — at haiku and sonnet the gap is decisive, while at opus the margin sits inside the arm's own run-to-run spread at N=2 tasks, a genuine no result. Sonnet's blind arm then pays more per resolved task than its own harness arm, because the five unresolved attempts still spent real money."
    />
  );
}
