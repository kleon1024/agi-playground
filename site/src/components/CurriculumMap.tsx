import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'goal',
    label: 'Outcome',
    owns: 'The user or business change worth producing.',
    handoff: 'A measurable mission contract.',
  },
  {
    id: 'mission',
    label: 'Mission',
    owns: 'One end-to-end decision loop with a declared evidence boundary.',
    handoff: 'The capabilities the loop actually needs.',
  },
  {
    id: 'capability',
    label: 'Capability',
    owns: 'Understanding, retrieving, generating, deciding, or acting.',
    handoff: 'A platform contract that can run and evaluate it.',
  },
  {
    id: 'platform',
    label: 'Platform',
    owns: 'Data, training, adaptation, serving, evaluation, and safety.',
    handoff: 'Concrete compute, storage, and runtime requirements.',
  },
  {
    id: 'infrastructure',
    label: 'Infrastructure',
    owns: 'Compute, storage, networking, queues, and deployment boundaries.',
    handoff: 'A reproducible runtime and artifact trail.',
  },
  {
    id: 'evidence',
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
