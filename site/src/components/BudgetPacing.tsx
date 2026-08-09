import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'demand',
    carries: '100 budget, 200 demand',
    label: 'Front-loaded demand',
    owns: 'A daily budget delivered against a demand curve that spikes in the morning and returns in the evening.',
    handoff: 'Uncapped, the campaign exhausts the budget before the evening demand arrives.',
  },
  {
    id: 'naive',
    carries: 'exhausts at hour 3',
    label: 'Naive spend',
    owns: '36.3, 33.2, 30.2 in the first three hours, then zero for the rest of the day.',
    handoff: 'The budget is fully spent and the evening is dark.',
  },
  {
    id: 'loose',
    carries: '3 dark hours',
    label: 'Loose cap',
    owns: 'At cap multiplier 1.50 total spend looks healthy at 100.0 of 100, but the late-window column collapses to 0.0.',
    handoff: 'Late-window delivery is the metric that catches the loose cap before the advertiser does.',
  },
  {
    id: 'paced',
    carries: '0 dark hours',
    label: 'Paced spend',
    owns: 'Cap per time slice at budget/hours, then adjust as actual delivery deviates; 88.4 of 100 spent across the day.',
    handoff: 'The trade — unspent budget against missed evening demand — is tuned against logged delivery, not fixed once.',
  },
];

export default function BudgetPacing(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A fully spent budget and an advertiser evening that is dark"
      question="The budget is spent, so why is the advertiser evening dark?"
      steps={STEPS}
      loop="Naive spend exhausts the 100-unit budget at hour 3; a loose cap looks healthy at 100.0 spent but leaves three dark hours when evening demand arrives; pacing caps per-slice spend at 8.3 per hour and survives the day at 88.4 spent. Late-window delivery is the metric that catches the loose cap before the advertiser does."
    />
  );
}
