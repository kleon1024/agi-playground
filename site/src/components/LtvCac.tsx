import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'economics',
    carries: 'LTV/CAC ratio',
    label: 'Unit economics',
    owns: 'Lifetime value is retention times revenue per retained user over the horizon; acquisition cost is what the channel charges.',
    handoff: 'A low CAC is not a cheap channel if its users leave.',
  },
  {
    id: 'verdicts',
    carries: 'organic 6.08, referral 1.80, paid 0.94',
    label: 'The verdicts',
    owns: 'Organic search pays back about six times its acquisition cost; paid installs return less than the cost of the user.',
    handoff: 'Every paid signup loses money once retention is counted.',
  },
  {
    id: 'window',
    carries: '1m to 24m curve',
    label: 'The measured window',
    owns: 'LTV/CAC is a curve over the horizon: at 3 months paid installs sits above referral, at 24 months referral tops the ranking while paid installs never improves.',
    handoff: 'The window you measured decides which channel you call the acquisition bet.',
  },
  {
    id: 'decision',
    carries: 'real growth',
    label: 'The decision',
    owns: 'Channels that ramp slowly and stay are understated at short windows, so re-measure LTV on the full retention curve before scaling spend.',
    handoff: 'Unit economics decide which growth is real growth — and which channel is a liability at any volume.',
  },
];

export default function LtvCac(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Retention times revenue, priced against what a channel charges"
      question="Which channels can the platform afford to buy users from at all?"
      steps={STEPS}
      loop="Organic search pays back 6.08x its acquisition cost, referral 1.80x, and paid installs 0.94x — every paid signup loses money once retention is counted. The verdict is window-dependent: at 3 months paid installs sits above referral, at 24 months referral tops the ranking at 10.02, so the measured window decides which channel you scale."
    />
  );
}
