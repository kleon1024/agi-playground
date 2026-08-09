import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'rules',
    carries: 'gap $0.20',
    label: 'The payment rules',
    owns: 'The same bids [1.20, 1.00, 0.80] pay $1.20 under first price and $1.00 under second price — a $0.20 per-auction gap.',
    handoff: 'That gap is not free revenue: bidders know the rule and shade their bids.',
  },
  {
    id: 'naive',
    carries: 'revenue 0.7485',
    label: 'The naive round',
    owns: 'Round 1 of a first-price market with three uniform bidders pays 0.7485 per auction — the winner value with no shading.',
    handoff: 'As bidders best-respond to observed competition, they shade.',
  },
  {
    id: 'settled',
    carries: 'settles at 0.4980',
    label: 'Revenue learns its way down',
    owns: 'Over 12 rounds of 300 auctions revenue settles at 0.4980, a 33% erosion to the symmetric equilibrium — exactly the second-price expected revenue of 0.5000.',
    handoff: 'A day-one read overstates the settled number by 57%.',
  },
  {
    id: 'fix',
    carries: 'measure the settled market',
    label: 'The fix',
    owns: 'Certify revenue on the settled market, not the transition: the reserve is the remaining lever, sitting on the demand curve with its own optimum at $0.8.',
    handoff: 'The market-design decision needs the settled state and the adaptation signal.',
  },
];

export default function AuctionRevenue(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A first-price advantage that erodes as bidders learn to shade"
      question="Why is the first-price revenue advantage a transient, not a property?"
      steps={STEPS}
      loop="The same bids pay $0.20 more per auction under first price, but the naive round pays 0.7485 and revenue settles at 0.4980 over 12 rounds as bidders shade — a 33% erosion to the second-price expected revenue of 0.5000. A day-one read overstates the settled number by 57%, so the revenue decision is made on the settled market, and the reserve is the remaining lever."
    />
  );
}
