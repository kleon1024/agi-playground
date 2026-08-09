import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'batch',
    carries: 'audio 0.032 at top',
    label: 'The batch order',
    owns: 'For a user who dwelled 40 seconds on an audio item three minutes ago, the batch model serves its learned priors: audio at 0.032, cases at the bottom.',
    handoff: 'The batch model would need a retrain to learn what one dwell already knows.',
  },
  {
    id: 'realtime',
    carries: 'audio boosted to 0.041',
    label: 'The session boost',
    owns: 'The realtime path reads the live session signal and pulls audio up to 0.041, re-ranking the slate before any retrain.',
    handoff: 'The cost is computing the boost per request, for every session.',
  },
  {
    id: 'depth',
    carries: 'shallow owns 70% of traffic',
    label: 'The depth split',
    owns: 'Across 400 sessions per depth, depth-1 sessions carry 70% of traffic and earn a +0.0066 lift (58% of the blended share) against depth-4 at +0.0118.',
    handoff: 'The blended +0.0079 hides a nearly 2x ROI difference per session.',
  },
  {
    id: 'cost',
    carries: 'p95 38ms to 118ms',
    label: 'The per-request price',
    owns: 'Realtime state is paid per request for every session, including the shallow ones: p95 climbs from 38ms to 118ms as features grow, and the boost decays back to batch order within forty minutes.',
    handoff: 'Gate the boost on a second signal and run the audit on the leak-safe feature.',
  },
];

export default function RealtimeUserState(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A session feature the batch model cannot see"
      question="Why does the per-request session state beat a retrain?"
      steps={STEPS}
      loop="One 40-second dwell tells the serving path the user is momentarily in an audio mood, and the realtime boost re-ranks the slate before any retrain. Stratified by depth, the single-dwell sessions that own 70% of traffic earn 58% of the blended lift per session, so the blended +0.0079 hides a nearly 2x ROI difference — and the per-request cost (p95 from 38ms to 118ms) is paid for every session, shallow ones included."
    />
  );
}
