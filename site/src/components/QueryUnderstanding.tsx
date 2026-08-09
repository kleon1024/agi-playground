import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'steps',
    carries: '28-term key space',
    label: 'Tokenize, normalize, classify',
    owns: 'Six queries become normalized tokens and an intent: navigational, transactional, or informational, and the intent decides the retrieval path.',
    handoff: 'The 28-term vocabulary is the key space the retrieval index must serve.',
  },
  {
    id: 'mix',
    carries: 'aggregate looks clean',
    label: 'The intent mix',
    owns: 'A 32-query log (12 head, 20 tail) classifies cleanly on the aggregate, so the rule order looks fine.',
    handoff: 'The tail carries every ambiguity the aggregate hides.',
  },
  {
    id: 'collision',
    carries: '3 tail collisions',
    label: 'The collision',
    owns: 'All three keyword-collision queries are tail: 15% of tail versus 0% of head, each assigned silently by rule order — "cheap how to fix iphone screen" fires transactional first.',
    handoff: 'A keyword classifier cannot commit when keywords fire two intents or none.',
  },
  {
    id: 'fix',
    carries: 'ambiguous bucket',
    label: 'The fix',
    owns: 'A confidence-aware intent model with an explicit ambiguous bucket costs a defined fallback path instead of a confident wrong route.',
    handoff: 'Dual-path retrieval guarantees the right candidate type but pushes disambiguation to the ranker.',
  },
];

export default function QueryUnderstanding(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A query that is a string with noise"
      question="Why does the aggregate intent mix hide the queries the classifier cannot commit on?"
      steps={STEPS}
      loop="Query understanding tokenizes, normalizes, and classifies a 28-term key space. The aggregate mix over a 32-query log looks clean, but all three keyword-collision queries are tail queries (15% of tail versus 0% of head), each assigned silently by rule order. The fix is a confidence-aware intent model with an explicit ambiguous bucket, audited by a stratified intent-mix read."
    />
  );
}
