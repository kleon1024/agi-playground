import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'goal',
    carries: 'a measurable mission contract',
    label: 'Outcome',
    owns: 'The user or business change worth producing.',
    handoff: 'A measurable mission contract.',
  },
  {
    id: 'mission',
    carries: 'the capabilities the loop needs',
    label: 'Mission',
    owns: 'One end-to-end decision loop with a declared evidence boundary.',
    handoff: 'The capabilities the loop actually needs.',
  },
  {
    id: 'capability',
    carries: 'a platform contract',
    label: 'Capability',
    owns: 'Understanding, retrieving, generating, deciding, or acting.',
    handoff: 'A platform contract that can run and evaluate it.',
  },
  {
    id: 'platform',
    carries: 'compute and storage requirements',
    label: 'Platform',
    owns: 'Data, training, adaptation, serving, evaluation, and safety.',
    handoff: 'Concrete compute, storage, and runtime requirements.',
  },
  {
    id: 'infrastructure',
    carries: 'a reproducible runtime',
    label: 'Infrastructure',
    owns: 'Compute, storage, networking, queues, and deployment boundaries.',
    handoff: 'A reproducible runtime and artifact trail.',
  },
  {
    id: 'evidence',
    carries: 'a keep, revise, or stop decision',
    label: 'Evidence',
    owns: 'Runs, costs, latency, quality, and named failure cases.',
    handoff: 'A decision to keep, revise, or stop the system.',
  },
];

export default function CurriculumMap(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="How to use this curriculum"
      question="What connects a model mechanism to a result that matters?"
      steps={STEPS}
      loop="Evidence is not the end of the line: it changes the next mission decision. That feedback loop is the organizing principle of every chapter."
    />
  );
}
