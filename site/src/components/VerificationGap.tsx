import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'pointwise',
    carries: 'an honest order',
    label: 'Pointwise ranker',
    owns: 'Producing the top-of-cascade order the LLM is allowed to reorder.',
    handoff: 'The reference order the reorder should be checked against.',
  },
  {
    id: 'llm-reorder',
    carries: '4/5 positions',
    label: 'LLM listwise reorder',
    owns: 'Re-ranking the top of the cascade from an instruction reading, with no check against the pointwise order.',
    handoff: 'A reorder with no verification attached — plausible, unmeasured.',
  },
  {
    id: 'calibration',
    carries: '1.6x inflation',
    label: 'Calibration drift',
    owns: 'A value-tree sweep that inflates click predictions and does not re-calibrate.',
    handoff: 'The order changes with no product-strategy change — only calibration.',
  },
  {
    id: 'verify',
    carries: 'the gate',
    label: 'Verification step',
    owns: 'Checking the generated order against the reference before the answer is shown.',
    handoff: 'The failure the generated surface must catch before the user sees it: a reorder nothing checked.',
  },
];

export default function VerificationGap(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="The ranking loop inside a generator"
      question="When generation replaces the ranked list, which mechanism becomes load-bearing?"
      steps={STEPS}
      loop="When the surface was a ranked list, the miscalibration was visible only to an offline eval that happened to compare orders. When the surface is a generated answer, the same 1.6x inflation silently changes which items the answer mentions and the user cannot see the alternative. The ranked list does not disappear — it becomes the retrieval input a generator conditions on — and the verification step is what keeps a reorder honest."
    />
  );
}
