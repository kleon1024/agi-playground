import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'solvable',
    carries: '500/500 heuristic',
    label: 'Solvability check',
    owns: 'The room is proven learnable before training: a hand-scripted 9-action sequence reaches the goal across 5 layout seeds, and wall-following reaches it on 500/500 trials.',
    handoff: 'The check buys attribution: the null can be traced to the cold start, not to an unsolvable room.',
  },
  {
    id: 'random',
    carries: '2/500 (0.4%)',
    label: 'Random baseline',
    owns: 'A uniformly random policy reaches the goal on 2/500 trials in the same 10-step budget.',
    handoff: 'A group of 4 independent rollouts has roughly a 1.6% chance of containing even one success.',
  },
  {
    id: 'coldstart',
    carries: '80/80 degenerate',
    label: 'Cold start',
    owns: 'Almost every group draws all-zero rewards, so no positive example ever enters the surrogate — degenerate 80/80 steps on all 3 seeds.',
    handoff: 'No learned policy exists to compare: greedy and sampled success are both exactly 0.0.',
  },
  {
    id: 'attributed',
    carries: '22.2% -> 1/200, 0.4% -> 80/80, ~0% -> 200/200',
    label: 'Explained null',
    owns: 'Degeneracy tracks baseline success by construction across the three environments.',
    handoff: 'A real, explained finding instead of an environment bug — the interleaved rollout is the price of honest partial-observability measurement.',
  },
];

export default function MinigridColdStart(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A solvable room, a 0.4% random baseline, a cold start with no gradient"
      question="What happens when GRPO cold start meets partial observability?"
      steps={STEPS}
      loop="The room is solvable — a heuristic reaches the goal 500/500 times — while a random policy succeeds 2/500, so a group of 4 rollouts almost never contains a success. Almost every group draws all-zero rewards, no positive example ever enters the surrogate, and training degenerates 80/80 steps on all 3 seeds. The null is attributed to the 0.4% cold start, not to the environment."
    />
  );
}
