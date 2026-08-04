/**
 * Mission 06's null result, on one axis, in two environments.
 *
 * The verdict table says the policy landed "decisively below both baselines,"
 * which is a phrase doing a lot of work: below by how much, against how much
 * seed-to-seed movement, and below what? Plotted, the answer is unmissable --
 * the trained policy sits left of a policy that picks actions at random, on
 * both environments, by many times its own spread.
 *
 * The MiniGrid group is the sharper picture. Three seeds all land on exactly
 * 0.0000, so the spread line has no length at all: the collapse is not noisy,
 * it is identical. That is also the mechanical reason stage 04 recorded zero
 * gradient steps, since a group of rollouts that all score zero has no reward
 * variance for GRPO to normalize.
 *
 * Values from `runs/2026-08-01-full-chain-report.md`, which reads every
 * upstream stage's own runs/ JSON.
 */
import React from 'react';

import SpreadComparison, { type Group } from './chart/SpreadComparison';

const GROUPS: Group[] = [
  {
    name: '5x5 grid-world (stages 00-01)',
    meta: 'fully observed; both baselines measured',
    /* Against random, which is the weaker of the two baselines it failed. */
    compare: [0, 3],
    arms: [
      { label: 'Random', values: [0.222], note: 'one measurement' },
      { label: 'Scripted greedy', values: [0.824], note: 'one measurement' },
      { label: 'GRPO, sampled', values: [0.182, 0.144, 0.21] },
      { label: 'GRPO, greedy', values: [0.078, 0.062, 0.078], subject: true },
    ],
  },
  {
    name: 'MiniGrid-Empty-6x6 (stage 04)',
    meta: 'partially observed; baselines over 500 trials',
    compare: [0, 2],
    arms: [
      { label: 'Random', values: [0.004], note: '500 trials' },
      { label: 'Wall-follow', values: [1.0], note: '500 trials' },
      { label: 'GRPO, greedy', values: [0, 0, 0], subject: true },
    ],
  },
];

export default function GrpoNullResult(): React.ReactElement {
  return (
    <SpreadComparison
      groups={GROUPS}
      domain={[-0.02, 1.02]}
      ticks={[0, 0.25, 0.5, 0.75, 1]}
      narrowTicks={[0, 0.5, 1]}
      axisLabel="success rate"
      selectLabel="Which environment to judge"
      readout={['Margin against random', 'Seed spread it is held against']}
      tickFormat={(v) => v.toFixed(2)}
      lead={
        'Every arm of the chain on one axis. Circles are seeds, the line between them the spread, '
        + 'the upright bar the mean; baselines are single measured rates and carry no spread line. '
        + 'Switch environments and read where the trained policy sits.'
      }
      verdict={({ group, gap, widest }) => (
        <>
          <strong>
            {group.name.split(' (')[0]}:{' '}
            {gap < 0 ? 'the trained policy is below random' : 'the trained policy is above random'}
            .
          </strong>{' '}
          {widest === 0
            ? 'All three seeds scored exactly 0.0000, so there is no spread to hold the margin '
              + 'against. That is not a small effect that needs more seeds — it is the same '
              + 'degenerate policy three times, and a rollout group that all scores zero gives '
              + 'GRPO no reward variance to learn from.'
            : `It is ${Math.abs(gap).toFixed(4)} below a policy that picks at random, while its `
              + `own three seeds move only ${widest.toFixed(4)}. The shortfall is `
              + `${(Math.abs(gap) / widest).toFixed(0)}x the noise, so no number of reruns turns `
              + 'it into a near miss.'}
        </>
      )}
      close={
        'Both environments give the same answer and the mission reports it as one: a null result, '
        + 'not a shortfall waiting on a longer run. What makes it publishable rather than '
        + 'embarrassing is that the baselines are on the same axis — a scripted heuristic solves '
        + 'the MiniGrid room every single time, which is how you know the environment works and '
        + 'the policy does not.'
      }
    />
  );
}
