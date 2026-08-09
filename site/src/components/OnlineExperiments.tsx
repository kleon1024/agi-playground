import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'claim',
    carries: 'the change helped',
    label: 'The claim',
    owns: 'An offline verdict cannot see online outcome; the experiment is the controlled version of the prediction-observation gap.',
    handoff: 'A p-value can be true while the conclusion is wrong.',
  },
  {
    id: 'gate',
    carries: 'first failure named',
    label: 'The validity gate',
    owns: 'Three conditions checked before the outcome test is read: the split matches the declared ratio, the analysis unit matches the randomization unit, and switchback logs carry no serial dependence.',
    handoff: 'The gate finds the broken split before the outcome test is read.',
  },
  {
    id: 'failures',
    carries: 'chi2=21.52 / SE gap 3.19x',
    label: 'The three failures',
    owns: 'SRM fires at roughly 2,000 users while a 2% effect needs 78,000; unit mismatch gives 24% false positives at declared alpha 5%; switchback minutes analyzed as independent give 53% per-minute false positives.',
    handoff: 'Each failure is cheaper to detect than the outcome effect it would fake.',
  },
  {
    id: 'verdict',
    carries: 'INVALID -> INTERPRETABLE',
    label: 'The verdict',
    owns: 'The broken fixture wins with p=0.03 and the effect is a ghost; the same log with the bucket constant corrected reads INTERPRETABLE.',
    handoff: 'The fix is cheap, the silence is not — the gate exists because silence is the expensive option.',
  },
];

export default function OnlineExperiments(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A p-value that is true, and a conclusion that is wrong"
      question="How do you know the change you shipped actually helped?"
      steps={STEPS}
      loop="The broken fixture wins with p=0.03 and the effect is a ghost: the traffic split drifted to 51.5% against a declared 50/50, and the SRM check catches it at chi2=21.52 with far less traffic than the outcome test needs. The same log with the constant corrected reads INTERPRETABLE — the fix is cheap, the silence is not."
    />
  );
}
