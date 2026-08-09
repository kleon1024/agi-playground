import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'contract',
    carries: '7 bullets',
    label: 'Contract first',
    owns: 'Seven acceptance bullets written into mission.yaml before any run executed.',
    handoff: 'The verdicts are judged against a declared contract, not against a favorable reading.',
  },
  {
    id: 'evidence',
    carries: 'committed runs/ only',
    label: 'Read-only verdicts',
    owns: 'A report script reads committed runs/ records and cannot soften a number after seeing it.',
    handoff: 'The mechanism makes bullet 7 true of itself.',
  },
  {
    id: 'verdicts',
    carries: '1 PARTIAL / 6 MET',
    label: 'The verdicts',
    owns: 'Bullet 1 reads PARTIAL; bullets 2-7 read MET on their own terms.',
    handoff: 'The question is why the first bullet cannot be rounded up.',
  },
  {
    id: 'gap',
    carries: 'CANNOT DETERMINE inside PARTIAL',
    label: 'The narrower gap',
    owns: 'On the private set the harness beats no-harness at haiku and sonnet and produces a genuine no-result at opus, where the margin sits inside the arm\'s own run-to-run spread at N=2 tasks; on the public set only the harness arm ran.',
    handoff: 'PARTIAL is the honest label: the evidence does not inherit the private set decisive result, and it is not rounded to MET.',
  },
];

export default function AgentReport(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="Seven bullets, one contract, six MET and one honest PARTIAL"
      question="What did this mission actually establish?"
      steps={STEPS}
      loop="The contract was written before any run; the report script reads only committed runs/ and cannot soften a number. Six bullets read MET, while bullet 1 stays PARTIAL because the private-set margin at opus sits inside that arm's own run-to-run spread at N=2 tasks and only the harness arm ran on the public set — a narrower, more specific gap than the old no-public-set gap."
    />
  );
}
