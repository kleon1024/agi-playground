import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'flip',
    carries: 'top slot flips',
    label: 'Same query, two users',
    owns: 'For running shoes, user A gets trail runners first and user B gets track spikes first — relevance identical, only the affinity vector differs.',
    handoff: 'Personalization is context added to the query.',
  },
  {
    id: 'aggregate',
    carries: 'aggregate +0.070',
    label: 'The aggregate lift',
    owns: 'Across a 16-query log crossing history depth with query stratum, the aggregate lift is +0.070 — as if it applied to everyone.',
    handoff: 'The average is entirely the history-bearing slice.',
  },
  {
    id: 'slice',
    carries: 'heavy-tail +0.250, new-tail -0.020',
    label: 'The slice split',
    owns: 'Heavy-history users lift +0.250 (tail) and +0.050 (head), while new-user slices get nothing: -0.020 on the tail and +0.000 on the head.',
    handoff: 'The tail even degrades when the attempt runs without history.',
  },
  {
    id: 'fix',
    carries: 'cold-start policy',
    label: 'The fix',
    owns: 'Report the lift per slice, check the traffic share, and pair the model with a cold-start policy for the no-history majority — with 70% of sessions carrying no history, the product decision is the cold-start prior, not the heavy-slice lift.',
    handoff: 'The query must be allowed to win when history narrows coverage.',
  },
];

export default function PersonalizedSearch(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Same query, two users, two orders, one aggregate that certifies a slice"
      question="Why does the personalization lift hide that most sessions see no change?"
      steps={STEPS}
      loop="Personalized search scores relevance plus affinity: same query, two users, two top slots. The aggregate lift of +0.070 is entirely the history-bearing slice — heavy-tail +0.250 against new-tail -0.020 — so with 70% of sessions carrying no history, the fix is a cold-start policy, not the heavy-slice number."
    />
  );
}
