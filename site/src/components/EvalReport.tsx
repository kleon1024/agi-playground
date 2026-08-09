import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'claim',
    carries: '68% on benchmark X',
    label: 'The number-shaped object',
    owns: 'A score without the tokenizer, context length, harness, seeds, and baseline is precise-looking and uninterpretable.',
    handoff: 'Any one missing disclosure turns a number into a number-shaped object.',
  },
  {
    id: 'refuse',
    carries: 'raises, never emits',
    label: 'The refusing report',
    owns: 'evaluate.py writes the tokenizer sha256 and context length, requires seeds >= 3, a named baseline, and a harness block, and raises when any is missing.',
    handoff: 'The format itself refuses the claims it cannot support.',
  },
  {
    id: 'numbers',
    carries: 'perplexity 21.677',
    label: 'The actual numbers',
    owns: 'Perplexity 21.677 at context 1024 against the 9.712-nat uniform baseline; loglik 0.625 with CI [0.250, 0.875] at n=8; generate 0.050 +/- 0.100; agent 0.000 [0.000, 0.000].',
    handoff: 'Every number carries the disclosure that makes it mean something.',
  },
  {
    id: 'boundary',
    carries: 'does not prove',
    label: 'The boundary',
    owns: 'Each eval type ends in its own does-not-prove section, because a correct number can still be false.',
    handoff: 'Loglik beats chance but the CI spans half the range at n=8 — the report says so instead of rounding it up.',
  },
];

export default function EvalReport(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A report format that refuses numbers it cannot support"
      question="How would you know if any of this worked?"
      steps={STEPS}
      loop="The stage is not a script that computes a score; it computes a score and refuses to emit it when the surrounding disclosure is missing. The measured numbers then carry their own limits: perplexity 21.677 at context 1024 against a 9.712-nat uniform baseline, loglik 0.625 with a CI spanning half the range at n=8, and an agent score of 0.000 that traces to a format-following failure, not a reasoning one."
    />
  );
}
