import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'age',
    carries: '0 to 6 wrong pairs',
    label: 'The snapshot ages',
    owns: 'A model trained at hour 0 ranks its own world exactly (0 wrong pairs), then ages: 5 wrong pairs at hour 6, 6 at hour 12, against the current truth.',
    handoff: 'A snapshot from hour 6 cuts the hour-12 error to a single pair.',
  },
  {
    id: 'panel',
    carries: 'volatile cohort due first',
    label: 'The per-cohort panel',
    owns: 'The gap grows unevenly: the volatile cohort already ranks 2 pairs wrong at hour 6 while the stable cohort is still exact.',
    handoff: 'An aggregate row dominated by fast movers hides which cohort is due.',
  },
  {
    id: 'trigger',
    carries: 'aggregate misses the mover',
    label: 'The calendar trigger',
    owns: 'A retraining trigger tuned to the aggregate average leaves the fast-moving cohort stale longest, because a single cadence for both cohorts is a compromise nobody asked for.',
    handoff: 'The trigger should be derived from measured error per cohort, not assumed by a calendar.',
  },
  {
    id: 'budget',
    carries: 'one retrain, 3x cut',
    label: 'The budget trade',
    owns: 'Retraining is a budget decision: the peak-hits detour prices one extra retrain for a threefold cut in stale exposure, and the cost owner decides whether the purchase is worth it.',
    handoff: 'Too rare and the snapshot silently ages; too frequent and the platform retrains on noise.',
  },
];

export default function RetrainingStaleness(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A snapshot that ranks its own world exactly and then silently ages"
      question="How do you notice that a model snapshot has stopped paying?"
      steps={STEPS}
      loop="A model trained at hour 0 ranks its own world exactly, then ages to 5 wrong pairs at hour 6 and 6 at hour 12; a snapshot from hour 6 holds the error to 1 pair. The per-cohort panel shows the volatile cohort due first — 2 wrong pairs at hour 6 while the stable cohort is still exact — so the trigger is derived from measured error per cohort, and retraining stays a budget decision the cost owner prices."
    />
  );
}
