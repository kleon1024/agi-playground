import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'exposure',
    carries: 'p(click) then p(pay|click)',
    label: 'Exposure space',
    owns: 'All impressions are the population the pay head must score, but pay is only observed after a click.',
    handoff: 'A funnel event: the pay label never appears on a non-click, so the training set can censor the funnel.',
  },
  {
    id: 'subset',
    carries: 'CVR AUC 0.735',
    label: 'Clicked-subset head',
    owns: '705 pay positives, drawn only from rows that clicked; training on them censors every non-click exposure.',
    handoff: 'The head learns pay inside a selected population, then scores a different one — selection bias, not just fewer positives.',
  },
  {
    id: 'fullspace',
    carries: 'CVR AUC 0.740',
    label: 'Full-space heads (ESMM)',
    owns: 'A CTR head on every impression plus a CTCVR head on every impression; 936 positives give the sparse event the whole space.',
    handoff: 'The conditional is derived, not trained: p(pay) = CTCVR / CTR keeps the funnel constraint structural.',
  },
  {
    id: 'derived',
    carries: 'clip + calibrate',
    label: 'Derived conditional',
    owns: 'A small CTCVR error at 2% CTR is a 3x swing in p(pay), so the ratio needs a per-slice clip and a calibration check.',
    handoff: 'The censored alternative reads 0.448 versus 0.618 for the full-space head on the funnel it is asked to score.',
  },
];

export default function EntireSpaceFunnel(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Two training populations, one funnel score"
      question="Why is a pay head trained on clicked rows biased on the full funnel?"
      steps={STEPS}
      loop="The two heads are nearly indistinguishable on AUC — 0.735 on the clicked subset against 0.740 on the full space — so the metric does not expose the break. The damage shows as the population mismatch: the subset head scores exposures it never trained on, and the funnel arithmetic downstream multiplies a biased conditional. Full-space training costs the joint label distribution, and the derived ratio must be clipped and re-checked where CTR is tiny."
    />
  );
}
