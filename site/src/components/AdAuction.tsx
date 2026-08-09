import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'secondprice',
    carries: 'winner pays second',
    label: 'Second-price rule',
    owns: 'The highest bidder wins and pays the second-highest bid, so truthful bidding is dominant and no bidder games the price by shading.',
    handoff: 'With one bidder the winner pays zero, which is why real auctions add a reserve.',
  },
  {
    id: 'thinning',
    carries: 'revenue 0.2514 vs 0.6118',
    label: 'The thinning market',
    owns: 'Revenue per auction falls from 0.6118 with four bidders to 0.2514 with one — about a 59% cut — while the sale rate merely halves.',
    handoff: 'Fill looks alive, revenue does not: the symptom is measurable while fill stays flat.',
  },
  {
    id: 'reserve',
    carries: '100% pay the reserve',
    label: 'The reserve-binding diagnostic',
    owns: 'When nearly every sale pays exactly the floor, the auction has no competition left to set prices.',
    handoff: 'The reserve-binding share is the diagnostic of a thin market.',
  },
  {
    id: 'depth',
    carries: '0.2492 vs 0.6118',
    label: 'Bidder depth, not the rule',
    owns: 'Reserve tuning in a one-bidder market peaks at 0.2492, far below the 0.6118 four bidders deliver at the same floor.',
    handoff: 'The durable fix is demand-side depth — more partners, an open exchange — tuned together with the reserve.',
  },
];

export default function AdAuction(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A collapsing revenue per auction under a flat fill rate"
      question="Why is revenue per auction collapsing while fill stays flat?"
      steps={STEPS}
      loop="Second-price is the canonical rule, but the audit shows the failure is the market, not the rule: thinning from four bidders to one cuts revenue per auction from 0.6118 to 0.2514 while the sale rate merely halves. The reserve-binding share is the diagnostic, and bidder depth — not reserve tuning — is the durable fix."
    />
  );
}
