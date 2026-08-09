import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'rank',
    carries: 'Ad B wins at 150.00',
    label: 'Rank by expected revenue',
    owns: 'eCPM is bid times pCTR times 1000. Ad B at 0.50 bid and 0.30 pCTR scores 150.00, above Ad C (1.00 x 0.12 = 120.00) and Ad A (2.00 x 0.05 = 100.00).',
    handoff: 'The low bidder wins, because the platform earns clicks, not bids.',
  },
  {
    id: 'audit',
    carries: '7 of 18 cells flip',
    label: 'Perturb the estimate',
    owns: 'Perturb each ad pCTR by six multipliers and re-rank: 7 of 18 cells (38.9%) flip the winner, mean realized revenue falls to 136.11 against the optimal 150.00.',
    handoff: 'A flip costs 30-50 per impression; a half-measure error that keeps the winner costs nothing.',
  },
  {
    id: 'knife',
    carries: '0.07 to 0.09 swaps',
    label: 'The flip point',
    owns: 'Sweep one ad pCTR and a 2-point change (0.07 to 0.09) swaps the winner, so the flip point is the tolerance budget the estimate must stay inside.',
    handoff: 'Calibration is the precondition that keeps estimates inside that budget.',
  },
  {
    id: 'fix',
    carries: 'calibrated pCTR',
    label: 'The fix',
    owns: 'Calibrated pCTR keeps estimates inside the flip-point budget; the tie-break rule and the reserve stay policy choices, not arithmetic.',
    handoff: 'Re-audit the realized column whenever the model or the floor changes.',
  },
];

export default function EcpmRanking(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A ranking that hands the slot to the low bid, and revenue that follows"
      question="Why is realized revenue below the ranking promise when pCTR is wrong?"
      steps={STEPS}
      loop="eCPM ranking multiplies bid by pCTR, so Ad B wins at 150.00 with the lowest bid. The audit perturbs each pCTR by six multipliers: 7 of 18 cells flip the winner (38.9%), mean realized revenue falls to 136.11 against the optimal 150.00, and every flip costs 30-50 per impression while half-measure errors cost nothing. The flip point is a 2-point pCTR change, and calibrated estimates are what keep the ranking inside that budget."
    />
  );
}
