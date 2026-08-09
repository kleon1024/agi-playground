import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'model',
    carries: 'ECE 0.2450',
    label: 'The model',
    owns: 'Predicts 0.50-0.59 and observes 3 clicks in 10; calibration asks what fraction of impressions predicted at p actually clicked.',
    handoff: 'A calibrated model says 0.55 and means 0.55; this one says 0.55 and means 0.30.',
  },
  {
    id: 'aggregate',
    carries: 'aggregate ECE 0.0238',
    label: 'The passing bar',
    owns: 'Global ECE 0.0238 sits below a typical 0.05 alert bar, so a global monitor passes.',
    handoff: 'Every subsystem that consumes pCTR — eCPM, the auction, the budget — inherits whatever the slice carries.',
  },
  {
    id: 'slice',
    carries: 'mobile ECE 0.2303',
    label: 'The hidden slice',
    owns: 'The mobile slice runs at 0.268 clicks against a mean prediction of 0.498 — an overestimate of nearly half, invisible at the aggregate.',
    handoff: 'Stratifying by slice is how the case is found.',
  },
  {
    id: 'monitor',
    carries: 'per-slice alert',
    label: 'Stratified monitoring',
    owns: 'One multiplicative factor cannot fix a bias that varies by slice, and a fixed correction goes stale when the click rate moves.',
    handoff: 'Calibration is a monitoring loop, not a one-time fit — per-slice monitoring needs enough impressions per slice to detect the gap.',
  },
];

export default function CtrCalibration(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A global bar that passes and a slice that overpays every auction"
      question="Why does the global calibration bar pass while one slice overpays eCPM?"
      steps={STEPS}
      loop="Aggregate ECE 0.0238 sits below a typical 0.05 alert bar, yet the mobile slice runs at 0.268 clicks against a mean prediction of 0.498 — an overestimate of nearly half that eCPM, the auction, and the budget all consume. The aggregate passes, the slice fails, and the fix is stratified monitoring, not a tighter global bar."
    />
  );
}
