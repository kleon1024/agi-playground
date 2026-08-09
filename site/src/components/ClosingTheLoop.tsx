import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'baseline',
    carries: '0/12 resolved',
    label: 'Twelve unresolved attempts',
    owns: 'Stage 01 non-resolving, non-timeout attempts: eleven diffs git apply rejected, one applied but wrong.',
    handoff: 'None of the twelve ever saw the outcome of its own diff before this stage.',
  },
  {
    id: 'gap',
    carries: 'one corrected attempt',
    label: 'The unmeasured slice',
    owns: 'Between zero feedback and a full tool loop sits the narrowest slice: outcome feedback with no tools at all.',
    handoff: 'The model sees the real result of its own last diff, not a critique and not a reward.',
  },
  {
    id: 'retry',
    carries: '2/12 resolved after one retry',
    label: 'Real outcome shown back',
    owns: 'The prior diff is re-applied for real and its actual git apply stderr or pytest failure is added to a fresh prompt.',
    handoff: 'One corrected attempt, with the original context restated rather than resumed.',
  },
  {
    id: 'bimodal',
    carries: '2/12 diff applied',
    label: 'Bimodal result',
    owns: 'Every resolved retry is exactly the one whose corrected diff applied at all; ten of twelve still produce a rejected diff.',
    handoff: 'The same failure mode stage 04 catalogued, measured on the retry step instead of the first attempt.',
  },
];

export default function ClosingTheLoop(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Twelve retries, one new fact each, a bimodal outcome"
      question="Does showing a model the real outcome of its own failed attempt help it fix the bug?"
      steps={STEPS}
      loop="Twelve real retry attempts move 0/12 to 2/12, and the run is fully bimodal: every attempt that resolved is exactly the attempt whose corrected diff applied at all, while ten of twelve still produce a diff git apply rejected. A genuine, small, mixed result — not a clean win, not a clean null."
    />
  );
}
