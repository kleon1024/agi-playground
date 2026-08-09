import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'runway',
    carries: '0.122 to 0.878',
    label: 'The runway',
    owns: 'NDCG@10 climbs from 0.122 on popularity to 0.878 after twenty interactions — a short runway, but one that must be bridged before the logs exist.',
    handoff: 'At zero interactions personalization has no signal, so the first page is a default decision.',
  },
  {
    id: 'prior',
    carries: 'right prior 0.878',
    label: 'The onboarding prior',
    owns: 'A right prior lifts the first page to 0.878 and retention to 0.55; a wrong prior collapses relevance to 0.000 and retention to 0.18.',
    handoff: 'A confident wrong prior is worse than asking nothing.',
  },
  {
    id: 'aggregate',
    carries: 'aggregate 0.254 hides it',
    label: 'The cohort split',
    owns: 'The wrong-prior path serves 0.000 first-page NDCG below the 0.122 popularity default, but the aggregate 0.254 hides it because 60% of new users arrive via popularity at exactly the baseline.',
    handoff: 'Stratify by onboarding path before declaring the first-page policy healthy.',
  },
  {
    id: 'fix',
    carries: 'route back to default',
    label: 'The fix',
    owns: 'Route any path underperforming the no-ask baseline back to the popularity default while its prior is re-measured; exploration is a tax — 10% costs 0.022, 30% costs 0.090.',
    handoff: 'The prior moves the first page more than the exploration budget on a short horizon.',
  },
];

export default function NewUserExperience(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A first page decided before personalization can see the user"
      question="Why is the first-page policy hidden by the aggregate?"
      steps={STEPS}
      loop="NDCG@10 climbs from 0.122 on popularity to 0.878 after twenty interactions. A right onboarding prior lifts the first page to 0.878, but a wrong one collapses it to 0.000 with 0.18 retention, below the 0.20 no-ask baseline — and the aggregate 0.254 hides the failing path because 60% of new users arrive via popularity. Stratify by onboarding path and route failing paths back to the default."
    />
  );
}
