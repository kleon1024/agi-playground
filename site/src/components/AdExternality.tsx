import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'displace',
    carries: '0.3 to 1.5 displaced',
    label: 'Ads displace organic',
    owns: 'On a five-slot slate with organic values [0.9, 0.8, 0.7, 0.5, 0.3], one ad displaces 0.3 of organic value, two ads 0.8, three ads 1.5.',
    handoff: 'Ad value is earned revenue minus the organic value pushed out.',
  },
  {
    id: 'aggregate',
    carries: 'net +0.0688',
    label: 'The aggregate verdict',
    owns: 'Across 20,000 users the aggregate net is +0.0688 per user, so an ad-load decision made on the aggregate keeps the ad.',
    handoff: 'The aggregate is the number the report shows and the slice the report hides.',
  },
  {
    id: 'slice',
    carries: 'engaged -0.3249',
    label: 'The hidden slice',
    owns: 'Casual users (75% share) gain +0.2000, engaged users (25%) lose -0.3249 because the ad displaces the high-value organic driving their sessions.',
    handoff: 'The slice that pays is the one the platform can least afford to damage.',
  },
  {
    id: 'fix',
    carries: 'net per slice and slot',
    label: 'The fix',
    owns: 'Admit an ad only when net value clears the organic bar, priced per user slice and per slot; the whale tail and slot scarcity both move the bar.',
    handoff: 'The measurement team owns the substitution experiment that prices the externality.',
  },
];

export default function AdExternality(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="An aggregate that says keep the ad, and an engaged slice that pays for it"
      question="Why does the aggregate ad-value view hide who pays for the slot?"
      steps={STEPS}
      loop="Every ad displaces an organic result: 1-3 ads on a five-slot slate displace 0.3 to 1.5 of organic value. The aggregate net across 20,000 users is +0.0688, so the report keeps the ad, while the engaged 25% slice loses -0.3249 per user because the ad displaces the high-value organic driving their sessions. The fix is a net-value rule priced per slice and per slot, not off the aggregate average."
    />
  );
}
