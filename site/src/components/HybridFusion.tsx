import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'fusion',
    carries: 'd1 0.0323 first',
    label: 'Reciprocal rank fusion',
    owns: 'Each matcher rank scores 1/(k + rank) summed across matchers; d1 and d4 appear in both lists and score roughly double the single-source survivors.',
    handoff: 'The union is preserved — nothing a matcher retrieved is dropped.',
  },
  {
    id: 'sweep',
    carries: 'aggregate sweep flat',
    label: 'The weight sweep',
    owns: 'A head-dominated sweep looks flat, so the team concludes the weight does not matter, while the tail swings with it.',
    handoff: 'Head queries are covered by either matcher, so the weight barely moves their score.',
  },
  {
    id: 'swing',
    carries: 'tail swings 0.343',
    label: 'The tail swing',
    owns: 'Tail NDCG swings 0.343 — from 0.451 served dense-only to 0.794 balanced — against a 0.020 head swing.',
    handoff: 'The flat aggregate sweep is a head artifact.',
  },
  {
    id: 'fix',
    carries: 'tune on the tail',
    label: 'The fix',
    owns: 'Tune the weight on the tail, report the swing per stratum, and keep a per-matcher health check so the hybrid does not silently degrade into whichever matcher is alive.',
    handoff: 'The weight is a product decision: which retrieval failure the platform trusts less.',
  },
];

export default function HybridFusion(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Two retrieval sets, one answer list, a weight that hides the tail"
      question="Why does the fusion weight look irrelevant until you split the queries?"
      steps={STEPS}
      loop="Reciprocal rank fusion rewards agreement — d1 and d4 score roughly double the single-source survivors — and keeps the union. The weight sweep looks flat because head queries move only 0.020, while tail NDCG swings 0.343, from 0.451 dense-only to 0.794 balanced. The fix is to tune the weight on the tail and report the swing per stratum."
    />
  );
}
