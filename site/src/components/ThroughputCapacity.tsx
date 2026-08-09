import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'mean',
    carries: '17ms average service',
    label: 'The mean capacity',
    owns: 'With 10ms mean service and 5% of queries at 150ms, the naive mean-based capacity is roughly 59 req/s.',
    handoff: 'A service at capacity by the mean is spending its budget failing the slow queries the mean never saw.',
  },
  {
    id: 'tail',
    carries: 'p99 933ms at 55 req/s',
    label: 'The tail grows first',
    owns: 'At 55 req/s the p99 reaches 933ms and 68.8% of queries miss the 100ms deadline, while p50 stays at 192ms.',
    handoff: 'The slow queries, not the average, push latency past the deadline.',
  },
  {
    id: 'scan',
    carries: 'p95 150ms exceeds deadline',
    label: 'The load scan',
    owns: 'The deadline percentile is unachievable at every load: p95 of the service mix (150ms) already exceeds the 100ms deadline, so no machine count satisfies a p95 deadline tighter than the service tail.',
    handoff: 'The mean capacity is the divergence load, not a serving answer.',
  },
  {
    id: 'fix',
    carries: 'hedge cuts 18.5% to 3.4%',
    label: 'The fix',
    owns: 'Cut the service tail before adding machines: a hedge serves a redundant shard at 2x work to cut a fan-out miss rate from 18.5% back to 3.4%.',
    handoff: 'The capacity number expires whenever the deadline, service mix, or launch calendar moves.',
  },
];

export default function ThroughputCapacity(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A service at capacity by the mean that misses the deadline for the slow queries"
      question="Why is capacity throughput times deadline, not throughput times average latency?"
      steps={STEPS}
      loop="A service averaging 17ms gets a naive capacity of about 59 req/s, but the tail grows first: at 55 req/s the p99 reaches 933ms and 68.8% of queries miss the 100ms deadline. The load scan shows p95 of the service mix (150ms) already exceeds the deadline at every load, so the fix is cutting the service tail — hedge, timeout, parallel shards — before buying machines."
    />
  );
}
