/** From a general resampling method to a standard-practice argument for NLP.
 *  Dates and claims come from 02-statistical-significance's own cited history. */
import React from 'react';
import Timeline, { Moment } from './timeline/Timeline';

const MOMENTS: Moment[] = [
  {
    year: 1979,
    label: 'Resample the data instead of assuming a noise model',
    source: 'B. Efron, "Bootstrap Methods: Another Look at the Jackknife" (Annals of Statistics, 1979)',
    what:
      "The general resampling method this chapter's core/ implements directly: estimate a "
      + "statistic's sampling distribution from the observed data itself, without assuming a "
      + 'parametric noise model.',
  },
  {
    year: 2004,
    label: 'Paired bootstrap arrives in system comparison',
    source: 'Philipp Koehn, "Statistical Significance Tests for Machine Translation Evaluation" (EMNLP 2004)',
    what:
      'Brings paired bootstrap resampling into NLP system comparison specifically — two MT '
      + "systems' BLEU scores on the same test sentences. It is also the source of this "
      + "chapter's small-sample teaching point: a 300-sentence test set can already give real "
      + 'assurance a difference is not noise, which is why the "large" condition here is 300 '
      + 'items rather than an arbitrary round number.',
  },
  {
    year: 2018,
    label: 'The case that this should be standard practice',
    source: 'Dror, Baumer, Shlomov and Reichart, "The Hitchhiker\'s Guide to Testing Statistical Significance in NLP" (ACL 2018)',
    what:
      'A later, broader survey arguing significance testing belongs across NLP evaluation '
      + 'rather than as a machine-translation-specific habit — the same argument this chapter '
      + 'makes for any close-score comparison.',
  },
];

export default function BootstrapLineage(): React.ReactElement {
  return (
    <Timeline
      moments={MOMENTS}
      lead={
        'Select an entry to see what it added. Read the distance between them as the delay '
        + 'between a method existing and a field agreeing to use it.'
      }
      close={
        'The method was available for twenty-five years before a paper made the case for it in '
        + 'system comparison, and another fourteen passed before a survey argued it should be '
        + 'routine. Nothing in the arithmetic got easier over that span. What was missing was '
        + 'the habit of running it before reporting a win — which is what this chapter is '
        + 'asking you to build.'
      }
    />
  );
}
