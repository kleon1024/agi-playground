import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'followup',
    carries: 'cheaper marathon shoes 0.8',
    label: 'The follow-up',
    owns: '"what about the cheaper ones" names no product; without the session it could be shoes, headphones, or laptops, with the cheaper marathon shoes at 0.2.',
    handoff: 'The session, not the query, is what resolves the follow-up.',
  },
  {
    id: 'resolution',
    carries: 'aggregate resolution 0.680',
    label: 'The aggregate read',
    owns: 'A short-session-dominated log reports conversational search resolves well, and the aggregate resolution is 0.680.',
    handoff: 'Long sessions — where truncation drops the first-turn grounding — lose most of their resolution.',
  },
  {
    id: 'long',
    carries: '17.8 turns resolve at 0.380',
    label: 'The long-session loss',
    owns: 'Sessions of 2-4 turns resolve at 0.980; sessions of 12-24 turns at 0.380 — truncation drops the oldest turns first, and the first-turn topic is the grounding a follow-up like "back to the first pair" needs.',
    handoff: 'The first-turn referent must survive the window.',
  },
  {
    id: 'fix',
    carries: 'pin the first-turn grounding',
    label: 'The fix',
    owns: 'Pin the first-turn grounding as a standing summary or compress the middle turns; a bigger window is not the fix — it costs latency and still buries the grounding in the middle.',
    handoff: 'Resolution per session length is the acceptance bar.',
  },
];

export default function ConversationalSearch(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A session that is the other half of the query"
      question="Why does long-session resolution collapse while the aggregate looks fine?"
      steps={STEPS}
      loop="The follow-up about cheaper ones resolves to marathon shoes only with the session (0.8 versus 0.2). The aggregate resolution of 0.680 is a short-session artifact: 2-4 turn sessions resolve at 0.980, 12-24 turn sessions at 0.380, because truncation drops the first-turn grounding. The fix is to pin the first-turn topic or compress the middle turns."
    />
  );
}
