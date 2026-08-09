import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'blend',
    carries: 'd1, d4, d2, d3, d5',
    label: 'The blend',
    owns: 'Teams a and b each propose a ranking; the system blends them into one list — d1, d4, d2, d3, d5 — and every user sees the same interleaved list.',
    handoff: 'Each click credits the team that proposed the clicked result: d4 credits b, d2 credits a.',
  },
  {
    id: 'positions',
    carries: 'A takes 1, 3, 5',
    label: 'The naive blend',
    owns: 'A team-A-first blend hands A positions 1, 3, 5 whose click mass sums to 0.51, and team B positions 2, 4, 6 at 0.35.',
    handoff: 'Users click whatever sits near the top independent of quality.',
  },
  {
    id: 'credit',
    carries: 'A credited 59.2%',
    label: 'The biased credit',
    owns: 'Across 10,000 sessions team A is credited with 59.2% of clicked sessions despite proposing nothing better; a random start per session restores 49.7/50.3.',
    handoff: 'At 200,000 sessions the naive interval sits 78 standard errors from the true 50/50.',
  },
  {
    id: 'fix',
    carries: 'random start costs 3.6%',
    label: 'The fix',
    owns: 'Randomize the start per session, decide the tie rule, and test pooled credits; the fix costs exactly 3.6% more sessions for the same interval width.',
    handoff: 'The sensitivity gain is why the design is worth the care: 400 users instead of 10,000.',
  },
];

export default function InterleavingExperiments(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A blended list that hands the win to whichever team got the better positions"
      question="Why does an interleaving experiment with equal teams hand one team the win?"
      steps={STEPS}
      loop="Interleaving blends two rankings into one list and credits each click to the team that proposed it. A team-A-first blend hands A positions 1, 3, 5 with click mass 0.51 against team B at 0.35, so A is credited with 59.2% of clicked sessions despite proposing nothing better. A random start per session restores 49.7/50.3, costing 3.6% more sessions for the same interval width."
    />
  );
}
