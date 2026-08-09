import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'logged',
    carries: '0.042 / 0.023 / 0.018',
    label: 'The logged world',
    owns: 'The training set is built from logged features — what the world looked like when the decision was made.',
    handoff: 'Offline ranking: P1001, P1002, P1003.',
  },
  {
    id: 'live',
    carries: '0.026 / 0.026 / 0.030',
    label: 'The live world',
    owns: 'Serving reads live features, and the price moved: live CTRs are 0.026, 0.026, 0.030.',
    handoff: 'Live truth: P1003, P1001, P1002.',
  },
  {
    id: 'skew',
    carries: 'offline P1001 vs live P1003',
    label: 'The skew',
    owns: 'Offline says P1001 wins while live reality says P1003 wins — the model is right about a world that ended.',
    handoff: 'The skew is not an estimation error; it is a pipeline property.',
  },
  {
    id: 'fix',
    carries: 'log at serve time',
    label: 'The fix',
    owns: 'Serving-time feature logging and re-validation on live features make the skew visible where it is born.',
    handoff: 'Training-serving consistency is a pipeline property, not a model one.',
  },
];

export default function TrainingServingSkew(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Two worlds, one model, a ranking that is honest for the wrong one"
      question="Why does training-serving skew survive an honest offline eval?"
      steps={STEPS}
      loop="Offline ranking reads logged CTRs and says P1001, P1002, P1003; live truth at the served price says P1003, P1001, P1002. The model is right about a world that ended — the skew is born between the moment a feature was logged and the moment it was served, and the fix is serving-time feature logging and re-validation on live features."
    />
  );
}
