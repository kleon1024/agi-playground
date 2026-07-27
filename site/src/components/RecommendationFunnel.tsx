import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  { id: 'context', label: 'Context', owns: 'User, query, session, market, and eligibility.', handoff: 'A request-level decision context.' },
  { id: 'recall', label: 'Recall', owns: 'Coverage across semantic, lexical, graph, and fresh queues.', handoff: 'About one thousand eligible candidates.' },
  { id: 'prerank', label: 'Pre-rank', owns: 'Cheap removal without losing the fine-ranker winners.', handoff: 'About one hundred candidates.' },
  { id: 'rank', label: 'Fine-rank', owns: 'Calibrated click, consumption, satisfaction, and risk estimates.', handoff: 'A prediction vector per item.' },
  { id: 'value', label: 'Value tree', owns: 'Explicit trade rates between user value, safety, and revenue.', handoff: 'One comparable utility score.' },
  { id: 'slate', label: 'Slate', owns: 'Diversity, ads displacement, creator caps, and hard rules.', handoff: 'The actual ordered page.' },
  { id: 'feedback', label: 'Feedback', owns: 'Exposure, action, dwell, negative feedback, and attribution.', handoff: 'Training evidence with policy bias disclosed.' },
];

export default function RecommendationFunnel(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Discovery decision loop"
      question="Which stage owns each irreversible loss of options?"
      steps={STEPS}
      loop="Downstream models cannot recover an item recall removed. Feedback then trains tomorrow's policy, so every serving decision also changes the future data distribution."
    />
  );
}
