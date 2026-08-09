import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'fact',
    carries: 'price, age',
    label: 'The feature',
    owns: 'A feature is a fact about the world, and the world moves; price is identical on both paths, age is not.',
    handoff: 'The score function rewards freshness, so age decides the order.',
  },
  {
    id: 'store',
    carries: 'scores 17.5 / -2.5 / 11.5',
    label: 'Store read',
    owns: 'Serves the ingestion-time value, 0 hours for every item, so training and serving read the same number.',
    handoff: 'The model and the ranker agree by construction.',
  },
  {
    id: 'naive',
    carries: 'scores 12.5 / -5.5 / 7.5',
    label: 'Naive read',
    owns: 'Recomputes on read: ages of 3-5 hours, reordering P1002 above P1001 on a feature the model never trained on.',
    handoff: 'The same items rank differently on a feature the model never saw.',
  },
  {
    id: 'contract',
    carries: 'agreement by construction',
    label: 'The contract',
    owns: 'Compute the feature once at ingestion and serve it unchanged to both sides; recomputing on read is how the two worlds drift apart.',
    handoff: 'The store exists to make the served world the trained world.',
  },
];

export default function FeatureStore(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="One fact, two reads, a reordered ranking"
      question="Why does the feature store make training and serving read the same number?"
      steps={STEPS}
      loop="The prices are identical on both paths; what differs is the age feature. The store serves the ingestion-time value at 0 hours for every item, while the naive path serves the current 3-5 hour age, and the score function rewards freshness — so the naive path reorders P1002 above P1001 on a feature the model never trained on."
    />
  );
}
