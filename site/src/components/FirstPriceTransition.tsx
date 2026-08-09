import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'shade',
    carries: 'bid sets win and price',
    label: 'Bidding becomes shading',
    owns: 'In first price the winner pays its own bid, so net is (value - bid) times win probability; bid the full value and any win nets zero.',
    handoff: 'With a uniform competitor the optimum is half the value: bidding $0.50 nets $0.25, the peak of the executed sweep.',
  },
  {
    id: 'censored',
    carries: 'the signal was free',
    label: 'The censored signal',
    owns: 'Second-price logs revealed the competitor bid with every win; first price hides it — a win shows only the price paid for its own bid, so shading becomes an estimate of an unobservable distribution.',
    handoff: 'Belief error lands directly in net value.',
  },
  {
    id: 'error',
    carries: 'loss 0.022 to 0.100',
    label: 'Belief error priced',
    owns: 'A belief error of 0.3 costs 0.022 per auction (9% of the 0.25 optimum); mis-specifying weaker competition (U[0, 0.4]) loses 0.100 because the bidder wins everything but overpays.',
    handoff: 'Probing is rationed: each probe is an impression the bidder risks overpaying for.',
  },
  {
    id: 'fix',
    carries: 'probe at 1,000 trials',
    label: 'The fix',
    owns: 'Treat shading as a prediction: probe the competitor landscape and hedge uncertainty. At 100 trials per probe the fitted optimum wanders to 0.60 and loses 0.011 per auction, against 0.001 at 1,000 trials.',
    handoff: 'The launch-day revenue forecast must assume learned shading: $0.95 settles at $0.42.',
  },
];

export default function FirstPriceTransition(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A bidder that pays its own bid, where the estimate decides the net"
      question="Why does shading under first price make the competitor distribution the whole game?"
      steps={STEPS}
      loop="Under first price the winner pays its own bid, so net is (value - bid) times win probability and the optimum with a uniform competitor is half the value — bidding $0.50 nets $0.25. The second-price log that revealed competition is censored, so shading is an estimate: a belief error of 0.3 costs 0.022 per auction, and mis-specifying weaker competition loses 0.100. Probing the landscape is the fix, and probe budget is the trade."
    />
  );
}
