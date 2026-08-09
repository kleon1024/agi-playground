import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'cascade',
    carries: '4.0 units per query',
    label: 'The cascade arithmetic',
    owns: 'Recall scores 100,000 candidates at 0.00001, pre-rank 1,000 at 0.001, fine-rank 50 at 0.02, mixing 20 at 0.05 — 1.0 unit each, 4.0 per query.',
    handoff: 'Exhaustive fine-rank of 10M items costs 200,000 units per query.',
  },
  {
    id: 'flat',
    carries: '1.0 each at 10M',
    label: 'The flat design',
    owns: 'Each stage buys the next a smaller problem and the product stays flat at 1.0 by design — the flat split is a property of one catalogue size.',
    handoff: 'As the catalogue grows, recall candidates scale sublinearly and the later stages keep fixed budgets.',
  },
  {
    id: 'dominant',
    carries: 'recall owns 68% at 1B',
    label: 'The attribution',
    owns: 'Recall owns 25% of the query budget at 10M items and 68% at 1B (total 4.00 to 9.31), so optimizing fine-rank before recall is optimizing the wrong stage.',
    handoff: 'The budget follows the ANN candidate set, not the expensive scorer.',
  },
  {
    id: 'fix',
    carries: 're-attribute on change',
    label: 'The fix',
    owns: 'Re-attribute the budget per stage whenever the catalogue or model changes; a bigger fine-ranker adds 0.013 NDCG and doubles the stage daily cost, and cache is a head discount, not a capacity plan.',
    handoff: 'The 50,000x gap that justified the funnel was measured at a catalogue size that no longer exists.',
  },
];

export default function CostPerQuery(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A cascade that was 1.0 per stage until the catalogue grew"
      question="Where does the query budget actually go as the catalogue scales?"
      steps={STEPS}
      loop="The cascade prices each stage at 1.0 unit — recall, pre-rank, fine-rank, mixing — 4.0 per query against 200,000 for exhaustive scoring. The flat split is a property of one catalogue size: recall owns 25% of the budget at 10M items and 68% at 1B, so re-attributing per stage and optimizing the dominant stage is the fix, not tuning the fine-ranker first."
    />
  );
}
