import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'item',
    carries: 'a wins 2.55 vs 2.10',
    label: 'Item-score sum',
    owns: 'Adds the scores of the items in isolation; slate a wins on item scores.',
    handoff: 'Items look better individually than they compose into a page.',
  },
  {
    id: 'slate',
    carries: 'b wins 3.06 vs 3.36',
    label: 'Slate value',
    owns: 'Adds each item contribution to the page, including the diversity adjustment stage 06 introduced.',
    handoff: 'The winner flips once diversity counts: the better-isolated items compose into a worse page.',
  },
  {
    id: 'audit',
    carries: 'tail flips 10/10',
    label: 'Metric-agreement audit',
    owns: 'A 20-comparison log stratified by head and tail, reading where the two metrics pick different winners.',
    handoff: 'Head comparisons agree 10/10; every tail comparison flips.',
  },
  {
    id: 'verdict',
    carries: 'near-tied slate',
    label: 'Stratified verdict',
    owns: 'The item-level and slate-level metrics rank the same page differently exactly where the slate is near-tied.',
    handoff: 'Report the winner per metric and declare which metric the product optimizes before tuning the ranker.',
  },
];

export default function SlateVsItemEvaluation(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Two metrics, two winners, a page that is more than its items"
      question="Why can an item-level metric rank the wrong winner?"
      steps={STEPS}
      loop="slate a wins on item-score sum 2.55 vs 2.10 and loses on slate value 3.06 vs 3.36 once diversity counts. The metric-agreement audit localizes the break: head comparisons agree 10/10 while every tail comparison flips, so an item-only report picks the wrong winner exactly where the slate is near-tied."
    />
  );
}
