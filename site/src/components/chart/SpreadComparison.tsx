/**
 * The chart this repository's acceptance rule needs: per-seed points, the
 * spread between them, and a margin held against that spread.
 *
 * Several missions declare the same rule before running anything -- if the gap
 * between two approaches is smaller than the run-to-run spread, the honest
 * answer is no result -- and then report it as a table of means and plus-minus
 * numbers, leaving the comparison that decides the verdict to be done in the
 * reader's head. Drawn, it is a length against a length.
 *
 * Two properties are load-bearing and are why this is shared rather than
 * redrawn per chapter. Every point is a real run, never a modelled band: an arm
 * with a single measurement is drawn as a single point and says so, because a
 * symmetric band around one number would dress a single run as a settled
 * result. And the verdict is computed here from the values, so a chapter cannot
 * illustrate a claim its own numbers do not support.
 */
import React, { useState } from 'react';
import { scaleLinear } from 'd3-scale';

import Chart from './Chart';

export interface Arm {
  label: string;
  /** One entry per run. Length 1 means a single measurement, drawn as such. */
  values: number[];
  /** Why this arm has no spread, when it has none. Shown beside the point. */
  note?: string;
  /** The arm under test, as opposed to what it is being held against. */
  subject?: boolean;
}

export interface Group {
  name: string;
  /** Right-aligned annotation on the group's header row. */
  meta?: string;
  arms: Arm[];
  /** Indices into `arms`: the reference, then the subject. */
  compare: [number, number];
}

/**
 * Which spread the margin is held against. Missions declare this differently
 * and the difference changes verdicts, so it is stated per chapter rather than
 * assumed: mission 09 compares against the noisier of the two arms, mission 05
 * against the arm under test, because one of its references is a single API
 * call with no spread of its own.
 */
export type SpreadRule = 'widest' | 'subject';

export interface Judgement {
  group: Group;
  gap: number;
  /** The spread the margin is being held against, under this chapter's rule. */
  widest: number;
  decisive: boolean;
  ratio: number;
}

interface SpreadComparisonProps {
  groups: Group[];
  domain: [number, number];
  ticks: number[];
  /** Fewer ticks for a phone-width plot. Defaults to every other tick. */
  narrowTicks?: number[];
  axisLabel: string;
  /** Label for the group selector, for a reader using a screen reader. */
  selectLabel: string;
  lead: React.ReactNode;
  close: React.ReactNode;
  /** The sentence a verdict deserves in this chapter's own terms. */
  verdict: (judgement: Judgement) => React.ReactNode;
  /** Names the two quantities in the readout, e.g. ['Gap', 'Widest spread']. */
  readout: [string, string];
  tickFormat?: (value: number) => string;
  spreadRule?: SpreadRule;
}

const ROW_H = 30;
const GROUP_GAP = 26;
/* Name, then annotation on its own line. Right-aligning the annotation across
   from the name collides with it as soon as the plot is phone-width. */
const HEADER_H = 40;
const PADDING = { top: 12, right: 14, bottom: 52, left: 96 };

const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;
const spread = (xs: number[]) => (xs.length > 1 ? Math.max(...xs) - Math.min(...xs) : 0);

export function judge(group: Group, rule: SpreadRule = 'widest'): Judgement {
  const [reference, subject] = group.compare.map((i) => group.arms[i]);
  const gap = mean(subject.values) - mean(reference.values);
  const widest = rule === 'subject'
    ? spread(subject.values)
    : Math.max(spread(reference.values), spread(subject.values));
  return {
    group,
    gap,
    widest,
    decisive: Math.abs(gap) > widest,
    ratio: widest === 0 ? Infinity : Math.abs(gap) / widest,
  };
}

export default function SpreadComparison({
  groups,
  domain,
  ticks,
  narrowTicks,
  axisLabel,
  selectLabel,
  lead,
  close,
  verdict,
  readout,
  tickFormat = (v) => v.toFixed(2),
  spreadRule = 'widest',
}: SpreadComparisonProps): React.ReactElement {
  const [selected, setSelected] = useState(0);
  const judgement = judge(groups[selected], spreadRule);

  const offsets: number[] = [];
  let cursor = 0;
  groups.forEach((group) => {
    offsets.push(cursor);
    cursor += HEADER_H + group.arms.length * ROW_H + GROUP_GAP;
  });
  const plotHeight = cursor - GROUP_GAP;
  const height = PADDING.top + plotHeight + PADDING.bottom;

  return (
    <div className="learning-widget">
      <p>{lead}</p>

      {groups.length > 1 && (
        <div className="widget-controls" role="group" aria-label={selectLabel}>
          {groups.map((group, i) => (
            <button
              key={group.name}
              type="button"
              aria-pressed={i === selected}
              onClick={() => setSelected(i)}
            >
              {group.name}
            </button>
          ))}
        </div>
      )}

      <Chart height={height} padding={PADDING} label={axisLabel}>
        {(frame) => {
          const { padding, innerWidth, innerHeight } = frame;
          const x = scaleLinear().domain(domain).range([0, innerWidth]);
          const shown = innerWidth < 260
            ? (narrowTicks ?? ticks.filter((_, i) => i % 2 === 0))
            : ticks;

          return (
            <g transform={`translate(${padding.left},${padding.top})`}>
              {groups.map((group, g) => {
                const top = offsets[g];
                return (
                  <g key={group.name} opacity={g === selected || groups.length === 1 ? 1 : 0.42}>
                    <text
                      x={-padding.left + 2}
                      y={top + 14}
                      fill="var(--rehearse-ink)"
                      fontSize={14}
                      fontWeight={700}
                    >
                      {group.name}
                    </text>
                    {group.meta && (
                      <text
                        x={-padding.left + 2}
                        y={top + 32}
                        fill="var(--rehearse-copy-muted)"
                        fontSize={13}
                      >
                        {group.meta}
                      </text>
                    )}
                    {group.arms.map((arm, r) => {
                      const y = top + HEADER_H + r * ROW_H + ROW_H / 2;
                      const colour = arm.subject
                        ? 'var(--rehearse-action)'
                        : 'var(--rehearse-copy-muted)';
                      const single = arm.values.length === 1;
                      return (
                        <g key={arm.label}>
                          <text
                            x={-10}
                            y={y + 4}
                            textAnchor="end"
                            fill="var(--rehearse-copy-muted)"
                            fontSize={13}
                          >
                            {arm.label}
                          </text>
                          {!single && (
                            <line
                              x1={x(Math.min(...arm.values))}
                              x2={x(Math.max(...arm.values))}
                              y1={y}
                              y2={y}
                              stroke={colour}
                              strokeWidth={2}
                              opacity={0.5}
                            />
                          )}
                          {arm.values.map((value, v) => (
                            <circle
                              key={v}
                              cx={x(value)}
                              cy={y}
                              r={3.5}
                              fill="var(--rehearse-warm-white)"
                              stroke={colour}
                              strokeWidth={1.6}
                            />
                          ))}
                          {!single && (
                            <line
                              x1={x(mean(arm.values))}
                              x2={x(mean(arm.values))}
                              y1={y - 8}
                              y2={y + 8}
                              stroke={colour}
                              strokeWidth={2.5}
                            />
                          )}
                          {arm.note && (() => {
                            /* A point near the right edge would push its own
                               note past the frame, which clips it silently. */
                            const at = x(mean(arm.values));
                            const room = innerWidth - at - 10;
                            const flip = room < arm.note.length * 6.6;
                            return (
                              <text
                                x={flip ? at - 10 : at + 10}
                                y={y + 4}
                                textAnchor={flip ? 'end' : 'start'}
                                fill="var(--rehearse-copy-muted)"
                                fontSize={13}
                              >
                                {arm.note}
                              </text>
                            );
                          })()}
                        </g>
                      );
                    })}
                  </g>
                );
              })}

              <g transform={`translate(0,${innerHeight + 8})`}>
                <line x1={0} x2={innerWidth} y1={0} y2={0} stroke="var(--rehearse-rule)" />
                {shown.map((tick) => (
                  <g key={tick} transform={`translate(${x(tick)},0)`}>
                    <line y1={0} y2={5} stroke="var(--rehearse-rule)" />
                    <text y={20} textAnchor="middle" fill="var(--rehearse-copy-muted)" fontSize={13}>
                      {tickFormat(tick)}
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
                  {axisLabel} &rarr;
                </text>
              </g>
            </g>
          );
        }}
      </Chart>

      <div className="objective-readout">
        <div>
          <span>{readout[0]}</span>
          <strong>{judgement.gap >= 0 ? '+' : ''}{judgement.gap.toFixed(4)}</strong>
        </div>
        <div>
          <span>{readout[1]}</span>
          <strong>{judgement.widest.toFixed(4)}</strong>
        </div>
        <div>
          <span>Margin as a multiple of it</span>
          <strong>
            {Number.isFinite(judgement.ratio) ? `${judgement.ratio.toFixed(2)}x` : 'no spread'}
          </strong>
        </div>
      </div>

      <p className="widget-caption">{verdict(judgement)}</p>

      <p>{close}</p>
    </div>
  );
}
