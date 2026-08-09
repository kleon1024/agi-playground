import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'decision',
    carries: 'tool reward 0.70',
    label: 'Two actions',
    owns: 'Answer directly with accuracy 0.97 down to 0.37 by digit level, or invoke the calculator that is always right and costs 0.30.',
    handoff: 'A well-calibrated policy pays the cost only when it is worth paying.',
  },
  {
    id: 'crossing',
    carries: 'cross between level 2 and 3',
    label: 'The crossing',
    owns: 'Simulated accuracy crosses the tool flat 0.70 reward between level 2 and level 3.',
    handoff: 'The task: answer directly below the crossing, invoke the tool above it.',
  },
  {
    id: 'runs',
    carries: 'seed 0 matches oracle',
    label: 'Three runs',
    owns: 'Seed 0 greedy decision matches the calibrated oracle at every one of the 5 levels; seeds 1 and 2 collapse to always-answer.',
    handoff: 'One seed learned when to pay; two did not, at a 3-seed mean 0.7953 with spread 0.1408.',
  },
  {
    id: 'recurrence',
    carries: '1/3 calibrated',
    label: 'Recurring collapse',
    owns: 'The same context-independent collapse stage 01 and 04 documented, now recurring in a two-action decision space.',
    handoff: 'A materially different outcome from the zero-gradient nulls, and not yet a reliable result.',
  },
];

export default function ToolUseDecision(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A calculator that is always right and costs 0.30"
      question="Does GRPO learn when to pay for a tool, not just what to say?"
      steps={STEPS}
      loop="The task is a single crossing: simulated accuracy falls from 0.97 to 0.37 across the five difficulty levels and crosses the tool flat 0.70 reward between level 2 and level 3. Seed 0 greedy policy separates cleanly at exactly that crossing, while seeds 1 and 2 collapse to one fixed decision regardless of difficulty — the same context-independent collapse this mission has now documented in three different environments."
    />
  );
}
