import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'context',
    carries: 'video wins mobile',
    label: 'CTR is context-dependent',
    owns: 'Video scores 0.07 on mobile and 0.03 on desktop; image 0.04 and 0.05; text 0.02 and 0.02. The winner depends on placement, so selection is part of expected value.',
    handoff: 'A global-average selection would pick video everywhere and leave desktop clicks on the table.',
  },
  {
    id: 'greedy',
    carries: '635 clicks',
    label: 'Sticky lifetime CTR',
    owns: 'Greedy on lifetime CTR serves the mature creative all 20,000 placements: its 0.06 history hides decay toward 0.025, so selection never estimates the alternative and earns 635 clicks.',
    handoff: 'The estimator reads a sticky average the new creative cannot break.',
  },
  {
    id: 'explore',
    carries: '645 clicks',
    label: 'Exploration alone',
    owns: 'Epsilon-greedy 0.10 corrects the new creative estimate but the greedy arm still reads the same sticky average, moving clicks only to 645.',
    handoff: 'Exploration learns the truth and the estimator refuses to use it.',
  },
  {
    id: 'fix',
    carries: 'EWMA 828 clicks',
    label: 'The fix',
    owns: 'A recency-weighted EWMA (828) or a Thompson posterior with decaying counts (807) lets selection see the wear and switch, recovering about 30% of the clicks.',
    handoff: 'Cold start still needs both traffic and a recency-aware estimate.',
  },
];

export default function CreativeSelection(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A creative that keeps winning after it stopped earning its slot"
      question="Why does a selection that averages logged CTR crown the stale winner?"
      steps={STEPS}
      loop="The winning creative is context-dependent: video wins mobile at 0.07, image wins desktop at 0.05. Greedy selection on lifetime CTR serves the mature creative all 20,000 placements, hiding its decay to 0.025 and earning 635 clicks; exploration alone barely helps at 645. A recency-weighted EWMA (828) or a Thompson posterior with decaying counts (807) sees the wear and recovers about 30% of clicks — the fix is the estimator, not the policy."
    />
  );
}
