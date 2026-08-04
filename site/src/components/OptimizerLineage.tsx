/** Where the three update rules in this chapter came from. Dates and claims come
 *  from foundations/02-optimization's own cited history; nothing is added. */
import React from 'react';
import Timeline, { Moment } from './timeline/Timeline';

const MOMENTS: Moment[] = [
  {
    year: 1951,
    label: 'A noisy gradient is enough',
    source: 'Robbins and Monro, "A Stochastic Approximation Method" (1951)',
    what:
      'Establishes that a noisy, stochastic estimate of a gradient — not the exact '
      + 'gradient — can still find a root or minimum under decaying step sizes and fairly '
      + 'mild conditions. This is the theoretical origin of training on mini-batches at all.',
  },
  {
    year: 1964,
    label: 'Momentum, from a rolling ball',
    source: 'Polyak, "Some Methods of Speeding Up the Convergence of Iteration Methods" (1964)',
    what:
      'Introduces the heavy-ball method: exactly the velocity update in section 3, derived '
      + 'from a physical analogy — a ball rolling in the bowl with momentum, rather than a '
      + 'particle immediately following the local slope.',
  },
  {
    year: 2014,
    label: 'Per-parameter step sizes, and a default that stuck',
    source: 'Kingma and Ba, "Adam: A Method for Stochastic Optimization" (2014, published ICLR 2015)',
    what:
      'Combines a momentum-like first moment with the per-parameter second-moment '
      + 'normalization in section 4, plus the bias correction the formulas above include. It '
      + 'remains the default optimizer for most transformer training in this repository and '
      + 'in the field at large, eleven years after publication.',
  },
];

export default function OptimizerLineage(): React.ReactElement {
  return (
    <Timeline
      moments={MOMENTS}
      lead={
        'Each of the three update rules you just ran arrived decades apart. Select one to see '
        + 'what it added, and read the distance between entries as the years it actually took.'
      }
      close={
        'Fifty years separate the result that made stochastic gradients defensible from the '
        + 'optimizer this repository trains with, and the second half of that gap is longer '
        + 'than the first. Adam is not a recent idea either — it has been the default for over '
        + 'a decade, which is why "use Adam" is a starting point in this chapter rather than a '
        + 'finding.'
      }
    />
  );
}
