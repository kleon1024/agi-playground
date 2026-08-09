import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'decode',
    carries: 'doc_17 0.9, doc_03 0.7',
    label: 'The decode',
    owns: 'A sequence model sees the query and emits document IDs directly — beam top-2 is doc_17, doc_03 — no index scan, no candidate step.',
    handoff: 'Retrieval becomes a decode, with decode latency and hallucination as the frontier costs.',
  },
  {
    id: 'aggregate',
    carries: 'aggregate recall@5 0.770',
    label: 'The aggregate read',
    owns: 'A head-dominated log reports the generative retriever decodes well, and the aggregate recall@5 of 0.770 is the headline.',
    handoff: 'The decode inherits the training distribution, where the tail has the least evidence.',
  },
  {
    id: 'tail',
    carries: 'tail recall 0.540',
    label: 'The tail divergence',
    owns: 'Head decodes perfectly (recall@5 1.000, precision 1.000) while tail recall is 0.540 with 0.740 precision — a quarter of the emitted tail IDs do not exist.',
    handoff: 'The model emits IDs that are not in the corpus.',
  },
  {
    id: 'fix',
    carries: 'gate the path',
    label: 'The fix',
    owns: 'Gate the generative path to queries it can decode, fall back to the dense or hybrid path for the tail, and verify every emitted ID against the corpus.',
    handoff: 'ID verification costs the very latency the approach was meant to save.',
  },
];

export default function GenerativeRetrieval(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A model that emits the document ID directly, and a tail it hallucinates"
      question="Why does the aggregate decode metric hide a quarter of nonexistent IDs?"
      steps={STEPS}
      loop="A generative retriever decodes document IDs directly — no scan, no candidates. The aggregate recall@5 of 0.770 is a head artifact: head decodes perfectly while tail recall is 0.540 with 0.740 precision, so a quarter of emitted tail IDs do not exist. The fix is to gate the generative path and fall back to dense or hybrid for the tail."
    />
  );
}
