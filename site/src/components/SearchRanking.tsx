import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'formulations',
    carries: '0.6209 vs 0.5804',
    label: 'Pointwise versus pairwise',
    owns: 'Both linear rankers run on the same eight-item set: pointwise predicts an absolute score (NDCG 0.6209), pairwise fits preferences over pairs (0.5804).',
    handoff: 'The losses disagree on mid-list order; the metric is the arbiter.',
  },
  {
    id: 'labels',
    carries: 'NDCG swings 0.573-0.621',
    label: 'The label-consistency audit',
    owns: 'Re-fitting on two re-graded batches moves NDCG@A from 0.5727 to 0.6209 with zero model change; batch C flips three learned pair preferences while changing no pair direction.',
    handoff: 'A direction-only gate undercounts label fragility.',
  },
  {
    id: 'margin',
    carries: 'four smallest margins',
    label: 'The boundary concentration',
    owns: 'The flipped pairs are the smallest-margin pairs of the clean fit — margins 0.017-0.056, the four smallest of 23.',
    handoff: 'A one-grade label move bites exactly where the fit is thinnest.',
  },
  {
    id: 'fix',
    carries: 'smooth list-aware loss',
    label: 'The fix',
    owns: 'A label-consistency audit on re-graded batches plus a smooth list-aware loss — LambdaRank/LambdaMART — absorbs the sensitivity.',
    handoff: 'Redundant grading and majority vote dilute boundary noise at a larger labeling budget.',
  },
];

export default function SearchRanking(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A ranker whose output moves with the grader, not the model"
      question="Why does a one-grade label move flip learned preferences?"
      steps={STEPS}
      loop="Pointwise and pairwise rankers agree on the top of the list and diverge mid-list: NDCG 0.6209 versus 0.5804, arbitrated by the metric. Re-grading batches moves NDCG@A from 0.5727 to 0.6209 with zero model change, flipping the three smallest-margin pairs (0.017-0.056 of 23). The fix is a label-consistency audit plus a smooth list-aware loss."
    />
  );
}
