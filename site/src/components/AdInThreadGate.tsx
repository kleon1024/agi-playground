import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'displacement',
    carries: '0.3 / 0.8 / 1.5',
    label: 'Displacement model',
    owns: 'Pricing the organic value an ad displaces: one ad displaces 0.3 for 0.6 of ad value, three displace 1.5 for 1.8.',
    handoff: 'The externality, still the price of entry when the ad moves inside the answer.',
  },
  {
    id: 'auction',
    carries: 'trade_rate=0.8',
    label: 'Value-tree auction',
    owns: 'The gate that decides whether the ad clears: at trade_rate=0.2 it does not, at 0.8 it enters and displaces item_6 (organic value 0.499).',
    handoff: 'The platform still decides, arithmetically, how much organic it may displace for revenue.',
  },
  {
    id: 'pacing',
    carries: '88.4 / 11.6',
    label: 'Budget pacing',
    owns: 'Delivering the budget across the day: naive delivery exhausts at hour 3 under a morning spike, paced delivery survives with 11.6 unused.',
    handoff: 'A budget that exhausts at hour 3 is the same failure in a thread as in a feed.',
  },
  {
    id: 'event',
    carries: 'the conversion',
    label: 'Conversion event',
    owns: 'The thing the loop optimizes: in a thread, the click becomes the agent-authorized action the answer enables.',
    handoff: 'The machinery survives; the surface and the event change — displacement is still the price of entry.',
  },
];

export default function AdInThreadGate(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="The auction, read inside the answer thread"
      question="When an ad stops being an item and becomes a step in the answer, what survives?"
      steps={STEPS}
      loop="The thread changes the surface (the ad's position in the loop) and the conversion event (click becomes authorized action). It does not change the machinery: auction, trade rate, pacing, and displacement cost all survive in the recorded runs. A thread-only reading misses the failure the runs keep visible — displacement is still the price of entry, and the value tree is still where the platform decides how much organic it may displace."
    />
  );
}
