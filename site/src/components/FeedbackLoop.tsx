import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'loop',
    carries: '300 rounds',
    label: 'Show and update',
    owns: 'Show top-5 and update on clicks, 300 rounds over 20 items; the ranker trains on what it showed.',
    handoff: 'More of what works works — until the world changes.',
  },
  {
    id: 'entrench',
    carries: 'head 99% / tail 0%',
    label: 'Entrenchment',
    owns: 'Items 0-4 gather clicks and their estimates rise; items 5-19 never gather enough to outrank the head, even where their true rate beats the prior.',
    handoff: 'Exposure concentrates on the head until the tail is invisible.',
  },
  {
    id: 'starve',
    carries: '5/20 sustained exposure',
    label: 'Starvation',
    owns: 'The whole catalogue was once eligible — 20 of 20 items ever shown — but sustained exposure reaches only 5 of 20.',
    handoff: 'The starved tail is where a world change would first be visible.',
  },
  {
    id: 'blindspot',
    carries: 'coverage hides it',
    label: 'The blind spot',
    owns: 'Coverage of 20/20 looks healthy while exposure is 99% head; the metric that catches the loop is sustained exposure, not eligibility.',
    handoff: 'The model own output became its training data, so the loop entrenches what it shows.',
  },
];

export default function FeedbackLoop(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="The ranker trains on what it showed, and what it showed entrenches"
      question="Why does the feedback loop starve the tail it once served?"
      steps={STEPS}
      loop="Over 300 rounds of show-top-5-and-update-on-clicks, items 0-4 gather clicks and their estimates rise while the tail never gathers enough to outrank the head — even where its true rate beats the prior. Catalogue coverage stays 20/20 while sustained exposure reaches 5 of 20, and the starved tail is where the change would first be visible."
    />
  );
}
