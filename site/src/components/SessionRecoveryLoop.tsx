import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'query',
    carries: '21.9M queries',
    label: 'Per-query verdict',
    owns: 'Scoring every query by what happened after it: clicked, reformulated, or abandoned.',
    handoff: '46.6% of queries counted as failures — zero clicks.',
  },
  {
    id: 'session',
    carries: 'one session read',
    label: 'Session re-read',
    owns: 'Reclassifying zero-click queries that ended in a reformulation that then clicked.',
    handoff: '19.9% of the failures reclassified as recovered sessions.',
  },
  {
    id: 'strata',
    carries: 'a stratum split',
    label: 'Stratify by frequency',
    owns: 'Splitting recovery by head (4.3%), body (13.0%), and tail (27.5%) query strata.',
    handoff: 'Recovery concentrates in the tail, where head optimization never reaches.',
  },
  {
    id: 'resolution',
    carries: '0.980 vs 0.380',
    label: 'Resolution audit',
    owns: 'Stratifying session resolution by length: short sessions resolve, long sessions lose the first-turn grounding.',
    handoff: 'The addressable gap is the reformulated-but-unresolved share (16.5%), not the click rate.',
  },
];

export default function SessionRecoveryLoop(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="One query log, two units of measurement"
      question="What does a conversational surface actually repair: the user's behavior or the loop's target?"
      steps={STEPS}
      loop="The user behaved identically in both readings — they reformulated and clicked. The per-query report called the episode two failures because it measured clicks; the session read counts one recovery because it measures resolution. That is the whole claim: a conversational surface does not fix the user's experience first, it fixes what the loop optimizes, which is the precondition for fixing the experience."
    />
  );
}
