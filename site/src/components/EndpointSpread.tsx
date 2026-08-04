/**
 * Three endpoints, two approaches, three seeds each -- and the rule this
 * mission declared before any of them ran.
 *
 * The table above this widget reports a mean and a spread per cell, which
 * leaves the reader to do the comparison that matters in their head: is the
 * distance between two means larger than the distance a single approach
 * wanders across seeds? Drawn, that comparison is a length against a length.
 * Two of the three endpoints are decisive in opposite directions and the third
 * is a genuine no-result, so the same rule produces three different answers on
 * one screen.
 *
 * Every value is a per-seed test ROC-AUC read from this mission's own
 * `runs/*-seed{0,1,2}.json` files. Means and spreads are computed here from
 * those seeds rather than copied, and they reproduce the recorded summaries in
 * `runs/2026-08-01-cross-endpoint-analysis.json` to four decimal places.
 */
import React, { useState } from 'react';
import { scaleLinear } from 'd3-scale';

import Chart from './chart/Chart';

interface Endpoint {
  name: string;
  /** Training-split positive count, from each stage's split_summary.json. */
  positives: number;
  descriptor: [number, number, number];
  model: [number, number, number];
}

/** Ordered by positive count, so question 1's monotonic trend is the reading order. */
const ENDPOINTS: Endpoint[] = [
  {
    name: 'NR-PPAR-gamma',
    positives: 118,
    descriptor: [0.6530447559859325, 0.6574649515825987, 0.6558028616852146],
    model: [0.6956327985739751, 0.633653707183119, 0.6480223539047069],
  },
  {
    name: 'NR-ER',
    positives: 628,
    descriptor: [0.6410500279900835, 0.6409529195370783, 0.6420382493059602],
    model: [0.6803875198501103, 0.657692703156596, 0.6655813368977848],
  },
  {
    name: 'SR-MMP',
    positives: 689,
    descriptor: [0.814241805198943, 0.8146119534456585, 0.8136186442266244],
    model: [0.7217375414659745, 0.7376632869164308, 0.7341257941788332],
  },
];

const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;
const spread = (xs: number[]) => Math.max(...xs) - Math.min(...xs);

const ROW_H = 30;
const GROUP_GAP = 26;
const HEADER_H = 22;
const GROUP_H = HEADER_H + ROW_H * 2;
/* Bottom leaves room for a tick row and the axis caption under it; at 40 the
   caption's descenders were clipped by the frame. */
const PADDING = { top: 12, right: 14, bottom: 52, left: 96 };
const HEIGHT = PADDING.top + ENDPOINTS.length * GROUP_H + (ENDPOINTS.length - 1) * GROUP_GAP
  + PADDING.bottom;

export default function EndpointSpread(): React.ReactElement {
  const [selected, setSelected] = useState(0);
  const active = ENDPOINTS[selected];

  const descMean = mean(active.descriptor);
  const modelMean = mean(active.model);
  const gap = modelMean - descMean;
  const widest = Math.max(spread(active.descriptor), spread(active.model));
  const decisive = Math.abs(gap) > widest;
  const verdict = !decisive
    ? 'No result: the gap is inside the spread'
    : gap > 0
      ? 'The trained model wins, beyond the spread'
      : 'The descriptor baseline wins, beyond the spread';

  return (
    <div className="learning-widget">
      <p>
        Each row is one approach on one endpoint: three seeds as circles, the line
        between them their spread, the upright bar their mean. The endpoints are
        ordered by how many positive training examples they had. Select one to run
        the mission&rsquo;s own rule on it.
      </p>

      <div className="widget-controls" role="group" aria-label="Which endpoint to judge">
        {ENDPOINTS.map((endpoint, i) => (
          <button
            key={endpoint.name}
            type="button"
            aria-pressed={i === selected}
            onClick={() => setSelected(i)}
          >
            {endpoint.name}
          </button>
        ))}
      </div>

      <Chart
        height={HEIGHT}
        padding={PADDING}
        label={
          'Test ROC-AUC for a descriptor baseline and a trained model on three Tox21 endpoints, '
          + 'three seeds each, with each approach’s seed spread drawn as a line.'
        }
      >
        {(frame) => {
          const { padding, innerWidth, innerHeight } = frame;
          const x = scaleLinear().domain([0.62, 0.83]).range([0, innerWidth]);

          return (
            <g transform={`translate(${padding.left},${padding.top})`}>
              {ENDPOINTS.map((endpoint, g) => {
                const top = g * (GROUP_H + GROUP_GAP);
                const chosen = g === selected;
                const rows: [string, [number, number, number], string][] = [
                  ['Descriptors', endpoint.descriptor, 'var(--rehearse-copy-muted)'],
                  ['Trained model', endpoint.model, 'var(--rehearse-action)'],
                ];
                return (
                  <g key={endpoint.name} opacity={chosen ? 1 : 0.42}>
                    <text
                      x={-padding.left + 2}
                      y={top + 14}
                      fill="var(--rehearse-ink)"
                      fontSize={14}
                      fontWeight={700}
                    >
                      {endpoint.name}
                    </text>
                    <text
                      x={innerWidth}
                      y={top + 14}
                      textAnchor="end"
                      fill="var(--rehearse-copy-muted)"
                      fontSize={13}
                    >
                      {endpoint.positives} positives in train
                    </text>
                    {rows.map(([label, seeds, colour], r) => {
                      const y = top + HEADER_H + r * ROW_H + ROW_H / 2;
                      const lo = Math.min(...seeds);
                      const hi = Math.max(...seeds);
                      return (
                        <g key={label}>
                          <text
                            x={-10}
                            y={y + 4}
                            textAnchor="end"
                            fill="var(--rehearse-copy-muted)"
                            fontSize={13}
                          >
                            {label}
                          </text>
                          <line
                            x1={x(lo)}
                            x2={x(hi)}
                            y1={y}
                            y2={y}
                            stroke={colour}
                            strokeWidth={2}
                            opacity={0.5}
                          />
                          {seeds.map((seed, s) => (
                            <circle
                              key={s}
                              cx={x(seed)}
                              cy={y}
                              r={3.5}
                              fill="var(--rehearse-warm-white)"
                              stroke={colour}
                              strokeWidth={1.6}
                            />
                          ))}
                          <line
                            x1={x(mean(seeds))}
                            x2={x(mean(seeds))}
                            y1={y - 8}
                            y2={y + 8}
                            stroke={colour}
                            strokeWidth={2.5}
                          />
                        </g>
                      );
                    })}
                  </g>
                );
              })}

              <g transform={`translate(0,${innerHeight + 8})`}>
                <line x1={0} x2={innerWidth} y1={0} y2={0} stroke="var(--rehearse-rule)" />
                {(innerWidth < 260 ? [0.65, 0.75] : [0.65, 0.7, 0.75, 0.8]).map((tick) => (
                  <g key={tick} transform={`translate(${x(tick)},0)`}>
                    <line y1={0} y2={5} stroke="var(--rehearse-rule)" />
                    <text y={20} textAnchor="middle" fill="var(--rehearse-copy-muted)" fontSize={13}>
                      {tick.toFixed(2)}
                    </text>
                  </g>
                ))}
                <text
                  x={innerWidth}
                  y={35}
                  textAnchor="end"
                  fill="var(--rehearse-copy-muted)"
                  fontSize={13}
                >
                  test ROC-AUC &rarr;
                </text>
              </g>
            </g>
          );
        }}
      </Chart>

      <div className="objective-readout">
        <div>
          <span>Gap, model minus descriptors</span>
          <strong>{gap >= 0 ? '+' : ''}{gap.toFixed(4)}</strong>
        </div>
        <div>
          <span>Widest seed spread</span>
          <strong>{widest.toFixed(4)}</strong>
        </div>
        <div>
          <span>Gap as a multiple of it</span>
          <strong>{(Math.abs(gap) / widest).toFixed(2)}x</strong>
        </div>
      </div>

      <p className="widget-caption">
        <strong>{active.name}: {verdict}.</strong>{' '}
        {decisive
          ? `The two approaches are ${Math.abs(gap).toFixed(4)} apart and the noisier of them `
            + `wanders ${widest.toFixed(4)} across seeds, so the difference survives the noise `
            + 'that produced it.'
          : `The two approaches are ${Math.abs(gap).toFixed(4)} apart and the noisier of them `
            + `wanders ${widest.toFixed(4)} across seeds — ${(widest / Math.abs(gap)).toFixed(0)}x `
            + 'further than the gap being claimed. Reporting a winner here would be reporting a seed.'}
      </p>

      <p>
        Read the trained-model rows top to bottom and the spread shrinks as positive
        examples rise: 118, 628, 689 positives give 0.0620, 0.0227 and 0.0159. Read
        the same rows for which side wins and there is no such order — the two
        endpoints with positive counts within 10% of each other land on opposite
        sides. One variable explains the variance; it does not explain the winner.
      </p>
    </div>
  );
}
