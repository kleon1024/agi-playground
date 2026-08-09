import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'label',
    carries: 'GMV tail',
    label: 'Heavy-tail label',
    owns: 'Transaction value where a few orders dwarf the rest; squared error weights large residuals quadratically.',
    handoff: 'A whale order ten times the median carries a hundred times the weight, so raw MSE spends its capacity on the tail.',
  },
  {
    id: 'raw',
    carries: '21.2% whale share',
    label: 'Raw MSE',
    owns: 'Fitting GMV directly: the largest orders own a fifth of the gradient and the 99% is treated as noise.',
    handoff: 'Rel err 1.409, with the whales owning the fit and the common case unmodeled.',
  },
  {
    id: 'log',
    carries: '5.2% whale share',
    label: 'log(1+GMV)',
    owns: 'Compress the tail so the common case gets a vote; one line, the cheapest repair.',
    handoff: 'Rel err drops to 1.045 and the whale share to a twentieth, at a small scale-interpretability cost.',
  },
  {
    id: 'decomp',
    carries: 'rel err 1.290',
    label: 'Decomposed objective',
    owns: 'Split the target into an order probability and a conditional amount, two levers each tuned and monitored independently.',
    handoff: 'Pays a little error for structure — its payoff is the levers, not the headline number.',
  },
];

export default function HeavyTailObjective(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Three objectives for one GMV label"
      question="Who owns the gradient when a whale order dwarfs the median?"
      steps={STEPS}
      loop="Raw MSE lands at rel err 1.409 with the whales owning 21.2% of the gradient; log(1+GMV) drops error to 1.045 and the whale share to 5.2%; the decomposed model lands at 1.290 with no single whale share. Whether the tail is signal worth fitting or noise worth compressing is a product decision the loss function cannot make."
    />
  );
}
