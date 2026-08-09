import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'pointwise',
    carries: 'd1..d5 stable',
    label: 'Pointwise order',
    owns: 'Scores each document and sorts; the baseline order is d1, d2, d3, d4, d5.',
    handoff: 'A stable order that ignores interactions between documents.',
  },
  {
    id: 'listwise',
    carries: '4/5 positions change',
    label: 'Listwise reorder',
    owns: 'The LLM reads the list as one context and emits a new order; d4 jumps to the top.',
    handoff: 'Listwise interactions are the frontier advantage, at a prompt cost that grows with the list.',
  },
  {
    id: 'audit',
    carries: 'tail swing 10/10',
    label: 'Prompt-order audit',
    owns: 'The same candidate set is ranked under a forward and a reversed prompt, stratified by head and tail.',
    handoff: 'Head queries are stable at 0/10 swing; every tail query changes with the written order.',
  },
  {
    id: 'verdict',
    carries: 'displacement 1.040',
    label: 'Stratified verdict',
    owns: 'The aggregate displacement 0.520 is a head artifact — all prompt-order sensitivity lives where the preference is a judgment call.',
    handoff: 'Gate the reorder on forward-versus-reverse tail agreement; where it swings, keep pointwise or aggregate multiple samples.',
  },
];

export default function LlmRanking(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="The same candidates, two orders, a prompt that decides"
      question="Why does the LLM reorder the list it can afford to see?"
      steps={STEPS}
      loop="The listwise reorder changes 4 of 5 positions and is the frontier advantage, but the prompt-order audit shows where the reorder is real: head rankings are stable at 0/10 swing, while every tail query changes with the written order at a mean displacement of 1.04. The aggregate 0.520 hides the tail, so the decision is to gate the reorder on forward-versus-reverse tail agreement."
    />
  );
}
