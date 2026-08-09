import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'generate',
    carries: '0.08 variant wins',
    label: 'Generate then select',
    owns: 'The LLM generates four variants scored 0.08, 0.06, 0.04, 0.02; a scoring model ranks them and only the winner is delivered — generation is cheap, impressions are not.',
    handoff: 'The score decides which creative earns an impression.',
  },
  {
    id: 'surface',
    carries: 'misses CTR-best 55.1%',
    label: 'The surface score',
    owns: 'A score mixing 60% true-signal proxy with 40% appeal junk misses the CTR-best creative in 55.1% of 5,000 batches and gives up 7.3% of delivered CTR (0.0848 chosen vs 0.0914 best).',
    handoff: 'The score rewards surface appeal instead of measured CTR.',
  },
  {
    id: 'collapse',
    carries: 'CTR 0.0911 to 0.0515',
    label: 'Generator collapse',
    owns: 'A mode-seeking generator re-emits the historical winners: at collapse 0.6, delivered CTR falls from 0.0911 to 0.0515 with 59.8% of deliveries re-running seen copy.',
    handoff: 'The creative wears out at generation time, before a single new impression is bought.',
  },
  {
    id: 'fix',
    carries: 'calibrate on CTR',
    label: 'The fix',
    owns: 'Calibrate the score on measured CTR — the same rule stage 16 set for pCTR — because the surface score and the delivery loop pick different winners.',
    handoff: 'Generation diversity and score calibration stay owned by different teams.',
  },
];

export default function LlmCreativeGeneration(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A surface score that picks the creative that does not convert"
      question="Why does the scoring model pick a different winner than the delivery loop?"
      steps={STEPS}
      loop="The LLM generates variants and a scoring model gates which one gets delivered. With a 0.40 surface-appeal component the score misses the CTR-best creative on 55.1% of 5,000 batches and gives up 7.3% of delivered CTR (0.0848 vs 0.0914). Upstream, a mode-seeking generator re-emits seen copy, cutting delivered CTR from 0.0911 to 0.0515 — so the fix is calibrating the score on measured CTR."
    />
  );
}
