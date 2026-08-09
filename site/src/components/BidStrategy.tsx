import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'derive',
    carries: 'bid $0.10',
    label: 'Derive the bid',
    owns: 'A target-CPA bid is value times conversion rate: a $5 target at 2% conversion values each click at $0.10, and that is the bid.',
    handoff: 'The bid changes with the estimate, and it is a walk-away line when the price passes the click value.',
  },
  {
    id: 'wins',
    carries: '35,672 won auctions',
    label: 'The winner log',
    owns: 'The bidder only logs the 35,672 auctions it won, and it won them because its estimate — hence its bid — was high.',
    handoff: 'Those impressions convert better than the market, so the log is a biased sample.',
  },
  {
    id: 'naive',
    carries: 'CVR 0.0316 vs 0.0188',
    label: 'The biased read',
    owns: 'Naive CVR from the winner log reads 0.0316 against a true 0.0188, and the target-CPA bid overpays 1.68x for every auction it actually wins.',
    handoff: 'The delay side reads in-flight clicks as negatives: 0.0096 against a true 0.02, a 52% under-read.',
  },
  {
    id: 'fix',
    carries: 'IPW recovers $0.09',
    label: 'The fix',
    owns: 'Inverse-propensity weighting each won observation by the inverse of its win probability recovers CVR 0.0187 and the $0.09 bid; delay-corrected soft labels recover 0.0197.',
    handoff: 'The corrections cost data and drift as the funnel changes.',
  },
];

export default function BidStrategy(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A bidder that overpays for every auction it wins"
      question="Why is the winner log a biased sample for the conversion rate?"
      steps={STEPS}
      loop="A target-CPA bid is value times conversion rate: $5 at 2% gives a $0.10 bid. The bidder logs only the 35,672 auctions it won, and it won them because its bid was high, so naive CVR reads 0.0316 against a true 0.0188 and the bid overpays 1.68x. Inverse-propensity weighting recovers 0.0187 and the $0.09 bid; delay-corrected labels fix the 52% under-read of in-flight clicks."
    />
  );
}
