import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'metrics',
    carries: 'NDCG 0.814, MRR 1.0000',
    label: 'The two metrics',
    owns: 'NDCG grades and discounts by position; MRR rewards the first relevant hit and ignores everything after it.',
    handoff: 'B good spread scores MRR 1.0000 — identical to A single good hit.',
  },
  {
    id: 'blind',
    carries: 'C hides a grade-0 miss',
    label: 'The blind spots',
    owns: 'C NDCG 1.0000 hides a grade-0 miss at position 3 — the top-weighted discount makes the tail nearly invisible.',
    handoff: 'The metrics agree on the extremes and disagree where the decision actually is.',
  },
  {
    id: 'divergence',
    carries: 'MRR ties 5 rankings',
    label: 'The metric divergence',
    owns: 'MRR ties five rankings as joint best that NDCG separates across five ranks; the first-hit gamer F is MRR-perfect (1.0000) and NDCG-fifth (0.7519).',
    handoff: 'The rank gap names which metric each ranking exploits.',
  },
  {
    id: 'fix',
    carries: 'declared metric suite',
    label: 'The fix',
    owns: 'Graded labels, per-position NDCG@k curves, and a rank-gap audit — the divergence between leaderboards is the signal that someone must state which ranking users need.',
    handoff: 'The metric decides what the team optimizes next, so the product owner, not the ranker, resolves it.',
  },
];

export default function SearchEvaluation(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Two metrics, one leaderboard, five tied winners"
      question="Why does the metric choice change which ranking gets optimized?"
      steps={STEPS}
      loop="NDCG grades and discounts by position while MRR rewards one early hit: B good spread scores MRR 1.0000 identical to A single hit, and C NDCG 1.0000 hides a grade-0 miss at position 3. In the divergence audit MRR ties five rankings that NDCG separates across five ranks — the first-hit gamer is MRR-perfect and NDCG-fifth. The fix is a declared metric suite plus a rank-gap audit."
    />
  );
}
