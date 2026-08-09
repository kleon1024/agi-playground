import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'logs',
    carries: 'no match possible',
    label: 'Interaction recall',
    owns: 'Stage 02 recall runs on interaction logs; a never-clicked item has no query-side match.',
    handoff: 'Cold items are unreachable by construction from logs alone.',
  },
  {
    id: 'content',
    carries: 'cold retrievable 2/3',
    label: 'Content vectors',
    owns: 'The VLM embeds the image and the text embedder embeds the description; either vector gives the cold item a place in the index.',
    handoff: 'Item e has neither vector and stays unreachable — a cold item is only as retrievable as its content.',
  },
  {
    id: 'audit',
    carries: 'tail single 100%',
    label: 'Modality-coverage audit',
    owns: 'The aggregate reachable figure hides the single-modality item: reachable through one surface only.',
    handoff: 'Every head item has both modalities; every tail item has exactly one.',
  },
  {
    id: 'verdict',
    carries: 'half the surfaces miss',
    label: 'Stratified verdict',
    owns: 'Image-only tail items are invisible to text queries and text-only items to image queries.',
    handoff: 'Report coverage per modality; for a single-modality item, fall back to the modality it has or synthesize the missing one.',
  },
];

export default function MultimodalRecall(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Content makes the cold item reachable, one modality at a time"
      question="Why is a cold item only as retrievable as its available content?"
      steps={STEPS}
      loop="Content vectors make 2 of 3 cold items retrievable, but the modality-coverage audit shows the defect the aggregate hides: head items carry both modalities while every tail item carries exactly one, so half the query surfaces miss every tail item. The fix is to report coverage per modality and fall back to the modality present or synthesize the missing one."
    />
  );
}
