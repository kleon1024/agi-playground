/**
 * Three Tox21 endpoints, two approaches, three seeds each, judged by the rule
 * this mission declared before any of them ran.
 *
 * Values are per-seed test ROC-AUC read from this mission's own
 * `runs/*-seed{0,1,2}.json` files. Means, spreads and verdicts are computed by
 * SpreadComparison from those seeds rather than copied, and they reproduce the
 * recorded summaries in `runs/2026-08-01-cross-endpoint-analysis.json` to four
 * decimal places.
 */
import React from 'react';

import SpreadComparison, { type Group } from './chart/SpreadComparison';

/** Ordered by positive count, so question 1's monotonic trend is the reading order. */
const GROUPS: Group[] = [
  {
    name: 'NR-PPAR-gamma',
    meta: '118 positives in train',
    compare: [0, 1],
    arms: [
      { label: 'Descriptors', values: [0.6530447559859325, 0.6574649515825987, 0.6558028616852146] },
      { label: 'Trained model', values: [0.6956327985739751, 0.633653707183119, 0.6480223539047069], subject: true },
    ],
  },
  {
    name: 'NR-ER',
    meta: '628 positives in train',
    compare: [0, 1],
    arms: [
      { label: 'Descriptors', values: [0.6410500279900835, 0.6409529195370783, 0.6420382493059602] },
      { label: 'Trained model', values: [0.6803875198501103, 0.657692703156596, 0.6655813368977848], subject: true },
    ],
  },
  {
    name: 'SR-MMP',
    meta: '689 positives in train',
    compare: [0, 1],
    arms: [
      { label: 'Descriptors', values: [0.814241805198943, 0.8146119534456585, 0.8136186442266244] },
      { label: 'Trained model', values: [0.7217375414659745, 0.7376632869164308, 0.7341257941788332], subject: true },
    ],
  },
];

export default function EndpointSpread(): React.ReactElement {
  return (
    <SpreadComparison
      groups={GROUPS}
      domain={[0.62, 0.83]}
      ticks={[0.65, 0.7, 0.75, 0.8]}
      narrowTicks={[0.65, 0.75]}
      axisLabel="test ROC-AUC"
      selectLabel="Which endpoint to judge"
      readout={['Gap, model minus descriptors', 'Widest seed spread']}
      lead={
        'Each row is one approach on one endpoint: three seeds as circles, the line between them '
        + 'their spread, the upright bar their mean. The endpoints are ordered by how many positive '
        + 'training examples they had. Select one to run the mission’s own rule on it.'
      }
      verdict={({ group, gap, widest, decisive }) => (
        <>
          <strong>
            {group.name}:{' '}
            {!decisive
              ? 'no result, the gap is inside the spread'
              : gap > 0
                ? 'the trained model wins, beyond the spread'
                : 'the descriptor baseline wins, beyond the spread'}
            .
          </strong>{' '}
          {decisive
            ? `The two approaches are ${Math.abs(gap).toFixed(4)} apart and the noisier of them `
              + `wanders ${widest.toFixed(4)} across seeds, so the difference survives the noise `
              + 'that produced it.'
            : `The two approaches are ${Math.abs(gap).toFixed(4)} apart and the noisier of them `
              + `wanders ${widest.toFixed(4)} across seeds — ${(widest / Math.abs(gap)).toFixed(0)}x `
              + 'further than the gap being claimed. Reporting a winner here would be reporting a seed.'}
        </>
      )}
      close={
        'Read the trained-model rows top to bottom and the spread shrinks as positive examples '
        + 'rise: 118, 628, 689 positives give 0.0620, 0.0227 and 0.0159. Read the same rows for '
        + 'which side wins and there is no such order — the two endpoints with positive counts '
        + 'within 10% of each other land on opposite sides. One variable explains the variance; it '
        + 'does not explain the winner.'
      }
    />
  );
}
