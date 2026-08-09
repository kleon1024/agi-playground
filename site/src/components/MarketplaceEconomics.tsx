import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'sweep',
    carries: 'peak at 35%',
    label: 'The take-rate sweep',
    owns: 'With volume = 1000 x (1 - 1.6 x rate), revenue peaks at 35% with $154 — past it revenue falls even though the per-transaction cut keeps rising.',
    handoff: 'The cut is a marketplace decision about where on the demand curve to sit.',
  },
  {
    id: 'curve',
    carries: 'peak follows elasticity',
    label: 'The demand curve',
    owns: 'Sweeping the slope moves the peak: sticky k=1.2 peaks at 42% / $208, the stage curve k=1.6 at 31% / $156, elastic k=2.0 at 25% / $125.',
    handoff: 'A rate fitted to one curve is a bet on that demand curve.',
  },
  {
    id: 'fixed',
    carries: '$203 vs $105',
    label: 'The fixed rate cost',
    owns: 'The stage 35% rate earns $203 on the sticky market and $105 on the elastic one — a 48% revenue difference with no change in the rate.',
    handoff: 'The two-sided market moves the peak again: 31% to 21%.',
  },
  {
    id: 'fix',
    carries: 'estimate the response',
    label: 'The fix',
    owns: 'Estimate the actual volume response before pricing and set the rate against the measured curve; pricing at the one-sided optimum earns 15% below the two-sided peak.',
    handoff: 'The curve moves, and the reserve, ad load, and take rate sit on the same demand curve.',
  },
];

export default function MarketplaceEconomics(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A take rate that is optimal on one market and a collapse on another"
      question="Why does the demand curve, not the take rate, set the revenue peak?"
      steps={STEPS}
      loop="Revenue is take rate times volume, and volume falls as the rate rises: on the stage curve the peak is 35% at $154. Sweeping elasticity moves the peak from 42% / $208 (sticky) to 25% / $125 (elastic), and the fixed 35% rate earns $203 on one market and $105 on the other — 48% apart with no change in the rate. The fix is estimating the actual volume response before pricing."
    />
  );
}
