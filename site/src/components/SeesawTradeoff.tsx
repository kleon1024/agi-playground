import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'naive',
    carries: 'click 0.726 / buy 0.716',
    label: 'Naive shared trunk',
    owns: 'One shared bottom, one click loss: the head rows are denser and higher-signal, so the gradient fits the head click signal.',
    handoff: 'The tail slice pays silently — the seesaw is invisible at the aggregate.',
  },
  {
    id: 'stratify',
    carries: 'head vs tail',
    label: 'Stratify by slice and task',
    owns: 'Splitting the metric by head (762 click positives) and tail (359) and by task before reading any number.',
    handoff: 'The trade appears: the dashboard said flat, the slices say the tail moved.',
  },
  {
    id: 'slice-weight',
    carries: 'buy 0.781',
    label: 'Slice weighting',
    owns: 'Explicitly upweighting the tail and the sparse buy task at a measured head cost.',
    handoff: 'Tail and buy lift to 0.781 while click AUC moves only 0.726 to 0.723.',
  },
  {
    id: 'gating',
    carries: 'buy 0.653',
    label: 'Gated trunk (MMoE-lite)',
    owns: 'A structural answer that separates task experts behind a gate — it does not automatically win.',
    handoff: 'On this cohort gating lands at 0.653, below explicit weighting: the seesaw is a trade you choose, not a structure that deletes it.',
  },
];

export default function SeesawTradeoff(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Three trunks, one cohort, one stratified read"
      question="Why is the AUC-label seesaw invisible until the metric is stratified?"
      steps={STEPS}
      loop="The aggregate click AUC moves 0.726 to 0.723 under slice weighting — a number a dashboard would call flat — while the per-slice audit shows the tail trade beneath it. Gating does not win either: buy AUC 0.653 against 0.781 for explicit slice weighting on this cohort. The seesaw is only visible when the metric is stratified by slice and task, which is why the chapter's first step is the decision rule, not the model."
    />
  );
}
