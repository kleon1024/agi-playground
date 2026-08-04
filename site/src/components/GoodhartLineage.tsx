/** From a monetary-policy observation to a measured proxy-versus-gold divergence.
 *  Dates and claims come from 01-metric-gaming's own cited history. */
import React from 'react';
import Timeline, { Moment } from './timeline/Timeline';

const MOMENTS: Moment[] = [
  {
    year: 1975,
    label: 'The original observation, about monetary targets',
    source: 'Charles Goodhart, Bank of England paper on UK monetary policy (1975)',
    what:
      'The observation this failure is named after was about monetary targets, not machine '
      + 'learning, and not about optimization pressure from a trained model.',
  },
  {
    year: 1997,
    label: 'The restatement everyone quotes',
    source: 'Marilyn Strathern, "\'Improving ratings\': audit in the British university system" (European Review, 1997)',
    what:
      '"When a measure becomes a target, it ceases to be a good measure" — the version usually '
      + 'quoted, and closer to what section 1 describes: the failure appears specifically once '
      + 'optimization pressure targets the measure.',
  },
  {
    year: 2016,
    label: 'Reward hacking named as an engineering problem',
    source: 'Amodei et al., "Concrete Problems in AI Safety" (2016, arXiv:1606.06565)',
    what:
      'Names reward hacking as one of several concrete, addressable AI safety problems rather '
      + 'than a purely philosophical concern.',
  },
  {
    year: 2022,
    label: 'Proxy and gold measured pulling apart',
    source: 'Gao, Schulman and Hilton, "Scaling Laws for Reward Model Overoptimization" (2022, arXiv:2210.10760)',
    what:
      "The closest empirical analogue to this chapter's toy: they measure a gold reward model's "
      + 'score alongside the proxy reward model actually being optimized against, and show the '
      + 'two diverge as KL distance from the reference policy increases — at model scale, not a '
      + 'constructed example.',
  },
  {
    year: 2023,
    label: 'One gameable feature, isolated',
    source: 'Singhal et al. (2023)',
    what:
      'Narrows that finding to one concrete, gameable feature: response length in RLHF.',
  },
];

export default function GoodhartLineage(): React.ReactElement {
  return (
    <Timeline
      moments={MOMENTS}
      lead={
        'Select an entry to see what it established. The gaps matter here: the idea was stated '
        + 'as economics long before anyone measured it happening inside a training run.'
      }
      close={
        'Forty-one years separate the observation from the paper that treats it as an '
        + 'engineering defect, and only six more separate that from a measurement of the '
        + 'divergence itself. The quotable version is old; the evidence that optimization '
        + 'pressure produces it in practice is recent, and it is the evidence this chapter '
        + 'reproduces at toy scale.'
      }
    />
  );
}
