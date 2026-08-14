/**
 * The platform plane map for the agentic-platform topic (mission 04).
 *
 * Wraps the shared ProcessDiagram with the topic's six groups as stages,
 * each one owning a plane of the platform and handing a concrete artifact
 * to the next. The artifact is the contract — the same rule every other
 * pipeline diagram in the curriculum follows.
 */
import React from 'react';

import ProcessDiagram from './ProcessDiagram';

const STEPS = [
  {
    id: 'call',
    label: 'Call',
    owns: 'the task set and the blind-call baseline',
    handoff: 'a scored task',
    carries: 'task',
  },
  {
    id: 'intent',
    label: 'Intent',
    owns: 'grounding and the plan-as-contract',
    handoff: 'an approved plan',
    carries: 'plan',
  },
  {
    id: 'harness',
    label: 'Harness',
    owns: 'the loop, tier routing, and feedback',
    handoff: 'a candidate patch',
    carries: 'patch',
  },
  {
    id: 'capabilities',
    label: 'Platform capabilities',
    owns: 'sandbox, runtime, memory, and tool protocols',
    handoff: 'an executed, remembered agent',
    carries: 'agent',
  },
  {
    id: 'organization',
    label: 'Platform organization',
    owns: 'orchestration, control plane, verification, and autonomy',
    handoff: 'a governed decision',
    carries: 'decision',
  },
  {
    id: 'production',
    label: 'Impact and production',
    owns: 'industry fit and real-task runs',
    handoff: 'a measured outcome',
    carries: 'outcome',
  },
];

export default function PlatformMap(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="The platform, drawn as its planes"
      question="Each plane owns one decision and hands its artifact to the next."
      steps={STEPS}
      loop="Every stage in this topic is one plane of this map; the record lives in its runs."
    />
  );
}
