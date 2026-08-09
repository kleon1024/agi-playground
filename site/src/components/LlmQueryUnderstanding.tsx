import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'parse',
    carries: 'flight_search, dest tokyo',
    label: 'The parse',
    owns: 'The LLM reads the raw string and emits intent plus slots: cheap flights to tokyo becomes flight_search with dest tokyo and max_price cheap.',
    handoff: 'The parse can be incomplete (origin None) or overcomplete (max_price invented), and both change what retrieval serves.',
  },
  {
    id: 'aggregate',
    carries: 'aggregate quality 0.765',
    label: 'The aggregate read',
    owns: 'A head-dominated log reports the LLM parse is good, and aggregate parse quality reads 0.765.',
    handoff: 'Head parses agree at 1.000 and score 0.976; the tail does not.',
  },
  {
    id: 'swing',
    carries: 'tail agreement 0.520',
    label: 'The swinging judgment call',
    owns: 'Tail parses agree at only 0.520, score 0.554, and carry 2.4 low-confidence slots per query — the same string can flip the retrieval path across samples.',
    handoff: 'A low-confidence slot silently filters retrieval.',
  },
  {
    id: 'fix',
    carries: 'sample and take the majority',
    label: 'The fix',
    owns: 'Sample the parse and take the majority (self-consistency), and treat a low-confidence slot as a clarification or a broadening, never a silent guess.',
    handoff: 'Sampling multiplies LLM latency and cost per query, and the slot floor costs calibration.',
  },
];

export default function LlmQueryUnderstanding(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A raw string that becomes the keys retrieval serves, parsed by a model that can invent slots"
      question="Why does the aggregate parse quality hide swinging judgment calls?"
      steps={STEPS}
      loop="The LLM parses raw strings into intent plus slots, and it can invent them: origin None or max_price invented both change retrieval. Aggregate quality of 0.765 is a head artifact — tail parses agree at only 0.520 with 2.4 low-confidence slots per query. The fix is self-consistency sampling plus treating a low-confidence slot as a clarification, never a silent guess."
    />
  );
}
