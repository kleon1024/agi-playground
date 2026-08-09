import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'intent',
    carries: 'intent to delivery',
    label: 'Stakeholder intent',
    owns: 'The loop exists to deliver an intent; the question is how often the intent actually arrives.',
    handoff: 'Search, ads, commerce, and risk control converge on intent-to-delivery as their decision surface.',
  },
  {
    id: 'blind',
    carries: '4/18 produced',
    label: 'Un-reconciled call',
    owns: 'A blind call produces a fix 4/18 times; 12/18 still failing, 11 of those never applying.',
    handoff: 'The produced-versus-delivered gap is where the loop pays for itself.',
  },
  {
    id: 'gate',
    carries: '14/18 rejected',
    label: 'Reconciliation gate',
    owns: 'The gate rejects 14/18 blind calls before delivery, at a measured cost against the harness.',
    handoff: 'Governance is a gate on real failures, not a permission ceremony.',
  },
  {
    id: 'delivered',
    carries: '18/18 delivered',
    label: 'Reconciled loop',
    owns: 'The harness delivers 18/18, and the six frontier chapters read the loop at industrial scale.',
    handoff: 'Each chapter names the failure before the fix, with every number traced to runs or dated external evidence.',
  },
];

export default function AgentFrontier(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="From stakeholder intent to a delivered outcome"
      question="What happens when the loop has to deliver?"
      steps={STEPS}
      loop="The blind call produces 4/18 with 12/18 still failing and 11 never applying; the reconciliation gate rejects 14/18 before delivery; the reconciled harness delivers 18/18. The six frontier chapters read this chain at industrial scale — where the agent stops recommending an action and becomes the action."
    />
  );
}
