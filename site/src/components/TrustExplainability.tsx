import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'contributions',
    carries: 'largest term 47%',
    label: 'The contribution table',
    owns: 'One item score splits into contributions: similar-users-bought is 47% of the score, you-viewed-this-category 33%, category affinity 19%, price a penalty.',
    handoff: 'The largest contribution is the term the user has no record to check.',
  },
  {
    id: 'surface',
    carries: 'similar-users leads unverifiable',
    label: 'The explanation surface',
    owns: 'The similar-users recs surface leads with an uncheckable claim on 70% of its items against a 62% aggregate; home feed (72%) and search (85%) are verifiable-heavy.',
    handoff: 'The aggregate hides the surface that spends trust on a black box.',
  },
  {
    id: 'fragile',
    carries: 'headline flips with counterfactual',
    label: 'The fragile headline',
    owns: 'The largest contribution flips from unverifiable to verifiable depending on which counterfactual the tool subtracts, so stability is part of the claim.',
    handoff: 'A 5% false-explanation rate nearly doubles opt-outs; at 50% a seventh of users leave.',
  },
  {
    id: 'fix',
    carries: 'lead with verifiable terms',
    label: 'The fix',
    owns: 'A per-surface verifiability bar: lead with the terms the user can check and drop or reorder the black-box headline where the audit says it dominates.',
    handoff: 'Headline-verifiable share is the telemetry the product team routes on, and opt-out per surface is the measurement.',
  },
];

export default function TrustExplainability(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="An explanation as good as the claim the user can check"
      question="Why is the largest contribution not the one that builds trust?"
      steps={STEPS}
      loop="For one shown item, similar-users-bought contributes 47% of the score — and the user has no record to check it. The similar-users recs surface leads with that uncheckable headline on 70% of its items against a 62% aggregate, and the headline itself is fragile, flipping with the counterfactual. The fix is a per-surface verifiability bar that leads with the terms the user can falsify."
    />
  );
}
