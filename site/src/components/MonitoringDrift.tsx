import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'offline',
    carries: 'eval flat',
    label: 'The offline harness',
    owns: 'Labels come from the same broken world, so an eval on those labels stays flat while the live page collapses.',
    handoff: 'The eval and the model share their blindness.',
  },
  {
    id: 'gap',
    carries: 'gap 0.001 to 0.020',
    label: 'The gap',
    owns: 'Predicted CTR holds at 0.040 while observed CTR falls from 0.039 to 0.020 across the hours.',
    handoff: 'The prediction-observation gap, smoothed, is the signal that changes.',
  },
  {
    id: 'alert',
    carries: 'ALERT at hour 10',
    label: 'The alert',
    owns: 'The EWMA crosses the threshold at hour 10 while nothing in the offline harness moved.',
    handoff: 'Online tracking catches the regression nobody flagged.',
  },
  {
    id: 'owner',
    carries: 'online only',
    label: 'The owner',
    owns: 'Monitoring lives online, not in the eval harness, because offline labels inherit the broken world.',
    handoff: 'The gap tracked online is the controlled version of the prediction-observation gap the experiment formalizes.',
  },
];

export default function MonitoringDrift(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A prediction that holds while the world quietly moves"
      question="Who notices when the world breaks at serve time?"
      steps={STEPS}
      loop="The model kept predicting 0.040 while users clicked less every hour; the offline eval cannot see it because its labels come from the same broken world. The smoothed prediction-observation gap crosses the alert threshold at hour 10 — ALERT — while nothing in the offline harness moved, which is why monitoring lives online."
    />
  );
}
