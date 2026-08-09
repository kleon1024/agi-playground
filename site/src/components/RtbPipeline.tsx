import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'budget',
    carries: '80ms of 100ms',
    label: 'The deadline budget',
    owns: 'Five stages consume 80ms of the 100ms deadline — parse 5, profile 20, context 10, inference 25, bid 15, send 5 — leaving a 20ms margin for jitter.',
    handoff: 'Every stage is a latency source and a potential timeout.',
  },
  {
    id: 'tail',
    carries: 'p99 blows the deadline',
    label: 'The tail constraint',
    owns: 'Across 20,000 requests p50 sits at 81.7ms and p95 at 99.5ms, both inside the budget, while p99 runs to 108.2ms and blows the deadline.',
    handoff: '933 of 20,000 requests (4.7%) time out, invisible in the 82.4ms mean.',
  },
  {
    id: 'timeout',
    carries: '933 slots with no bid',
    label: 'The invisible loss',
    owns: 'The mean looks healthy while 4.7% of requests lose the auction before the bid is compared; every timeout is a slot that sells nothing.',
    handoff: 'The margin has to be sized for the p99, not the p95.',
  },
  {
    id: 'fix',
    carries: 'cascade cuts 18.0% to 6.9%',
    label: 'The fix',
    owns: 'Size the margin for the p99 and give the model stage a fallback: a cheap cascade cuts a heavy model timeout rate from 18.0% to 6.9% at the price of cheap bids on 33.1% of worst-tail requests.',
    handoff: 'Timeout rate is a revenue metric before it is an availability footnote.',
  },
];

export default function RtbPipeline(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A mean that looks healthy and a p99 that loses the auction"
      question="Why does a latency pipeline fit the deadline on average and still time out?"
      steps={STEPS}
      loop="Five RTB stages consume 80ms of the 100ms deadline, leaving 20ms of margin. Across 20,000 requests p50 is 81.7ms and p95 is 99.5ms — both inside the budget — while p99 runs to 108.2ms and blows it, timing out 933 requests (4.7%) that the 82.4ms mean hides. The fix is a tail budget sized for the p99 plus a cascade fallback that cuts a heavy model timeout rate from 18.0% to 6.9%."
    />
  );
}
