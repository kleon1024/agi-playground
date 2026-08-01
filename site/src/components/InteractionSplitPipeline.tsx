import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  { id: 'parse', carries: '100,836 rows', label: 'Parse', owns: 'Reading MovieLens-style rows, dropping malformed ones.', handoff: 'Clean interaction rows: user, item, timestamp, rating.' },
  { id: 'dedupe', carries: 'deduplicated rows', label: 'Dedupe', owns: 'Dropping exact (user, item, timestamp) repeats — a retried write is not a second preference signal.', handoff: 'One row per genuine interaction.' },
  { id: 'filter', carries: '90,274 rows', label: 'Min-interaction filter', owns: 'Iteratively dropping users/items below a count threshold, looping until nothing changes.', handoff: '610 users and their remaining items — every one of them holds enough history to both train and test on.' },
  { id: 'split', carries: 'one timestamp cutoff', label: 'Time split', owns: 'Assigning every interaction before the cutoff to train, at or after it to test — no shuffling.', handoff: 'A split that matches how a live system actually sees data: never the future.' },
  { id: 'leakage', carries: 'a leakage rate', label: 'Leakage check', owns: 'Counting test rows whose user has a later train row.', handoff: '0 of 1,223 eligible test rows leak under the time split; 17,885 of 18,055 (99.1%) leak under a random split on the same data.', },
  { id: 'popularity', carries: 'the popularity floor', label: 'Popularity ranking', owns: 'Ranking items by train-set frequency only — no user, no query, no signal beyond the split.', handoff: 'hit-rate@20 of 0.0389 (honest split) vs 0.0496 (leaking split) — the floor every later stage in this mission must clear.' },
];

export default function InteractionSplitPipeline(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="One interaction log, six steps to a fair split"
      question="Where exactly does a random split let a model see its own answer key?"
      steps={STEPS}
      loop="Re-running the identical log through a random split instead of a time split is what turns 'a random split leaks the future' from an assertion into a number: 99.1% of test rows gain a same-user train row that happened later in time. Every stage downstream — recall, pre-rank, fine-rank, the value tree — is scored against the split this pipeline produces, so a leak here quietly inflates every number after it."
    />
  );
}
