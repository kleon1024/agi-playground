/** Ring-allreduce, from a cluster-computing result to a deep-learning default.
 *  Dates and claims come from infra/01-networking's own cited history. */
import React from 'react';
import Timeline, { Moment } from './timeline/Timeline';

const MOMENTS: Moment[] = [
  {
    year: 2009,
    label: 'The bandwidth-optimal argument, proved for clusters',
    source: 'Patarasuk and Yuan, "Bandwidth Optimal All-reduce Algorithms for Clusters of Workstations" (Journal of Parallel and Distributed Computing, 2009)',
    what:
      "Proves a ring's per-rank bandwidth cost is independent of world size while a naive "
      + "star's is not — the same asymptotic gap this chapter's sweep reproduces. The result "
      + 'predates deep learning entirely.',
  },
  {
    year: 2017,
    label: 'The same algorithm applied to gradient synchronization',
    source: 'Andrew Gibiansky, Baidu, "Bringing HPC Techniques to Deep Learning" (2017)',
    what:
      'Applies ring-allreduce to multi-GPU gradient synchronization, which is what made it a '
      + "fixture of deep learning. NCCL's ring implementation and PyTorch's gloo backend both "
      + 'still default to it for many message sizes today.',
  },
];

export default function AllreduceLineage(): React.ReactElement {
  return (
    <Timeline
      moments={MOMENTS}
      lead={
        'Select either entry to see what it established. Eight years separate the proof from '
        + 'the moment this became the way gradients move.'
      }
      close={
        'The collective this chapter measures was not designed for training. It was a result '
        + 'about clusters of workstations that turned out to describe gradient synchronization '
        + 'exactly, because the constraint is the same one: per-rank bandwidth, not aggregate '
        + 'bandwidth, is what a growing world size has to leave unchanged.'
      }
    />
  );
}
