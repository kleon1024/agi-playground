/**
 * The rank-to-position pipeline, drawn as the stage where the strategy is.
 *
 * Mission 03 stage 02's cross-sectional rank model is a pipeline — signal,
 * cross-sectional rank, weight, position — and the sizing rule at stage 3
 * is where the strategy lives. This widget holds the signal fixed and lets
 * the reader switch the sizing rule, so the same score becomes four
 * different portfolios in one control. Every number is the recorded
 * stage-02 run's own (2026-07-27), not a rounded example.
 */
import React, { useState } from 'react';

const RULES: Record<
  string,
  { label: string; belief: string; hhi: string; turnover: string; sharpe: string; violations: string }
> = {
  equal: {
    label: 'Equal-weight decile',
    belief: 'Only the tails carry useful order.',
    hhi: '0.6667',
    turnover: '0.638',
    sharpe: '-0.68',
    violations: '7',
  },
  rank: {
    label: 'Rank-proportional',
    belief: 'Order matters across the full universe; gap size does not.',
    hhi: '0.1776',
    turnover: '0.348',
    sharpe: '-1.05',
    violations: '47',
  },
  signal: {
    label: 'Signal-proportional',
    belief: 'Raw score magnitude represents conviction.',
    hhi: '0.2243',
    turnover: '0.369',
    sharpe: '-1.20',
    violations: '35',
  },
  vol: {
    label: 'Volatility-scaled',
    belief: 'Conviction should be adjusted for trailing risk.',
    hhi: '0.1952',
    turnover: '0.404',
    sharpe: '-0.83',
    violations: '43',
  },
};

const STAGES = ['signal', 'rank', 'weight', 'position'];

export default function RankToPositionAnatomy(): React.ReactElement {
  const [rule, setRule] = useState('rank');
  const r = RULES[rule];
  return (
    <div className="learning-widget">
      <label style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span>Sizing rule</span>
        <select aria-label="Sizing rule" value={rule} onChange={(e) => setRule(e.target.value)}>
          {Object.entries(RULES).map(([key, v]) => (
            <option key={key} value={key}>
              {v.label}
            </option>
          ))}
        </select>
      </label>
      <ol
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(6.5rem, 1fr))',
          gap: '0.5rem',
          paddingLeft: '0',
          listStyle: 'none',
          margin: '1rem 0',
        }}
      >
        {STAGES.map((stage, i) => (
          <li
            key={stage}
            style={{
              border: '1px solid var(--rehearse-rule)',
              padding: '0.5rem',
              textAlign: 'center',
              background: i === 2 ? 'var(--rehearse-action-soft)' : 'var(--rehearse-paper)',
            }}
          >
            <strong>{stage}</strong>
            <br />
            <span style={{ fontSize: 'var(--type-xs)' }}>
              {i === 2 ? r.label : i === 0 ? 'one score per name' : i === 1 ? 'order, drop magnitude' : 'cap + de-mean'}
            </span>
          </li>
        ))}
      </ol>
      <p style={{ margin: '0.5rem 0' }}>
        <strong>Belief encoded:</strong> {r.belief}
      </p>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(8rem, 1fr))',
          gap: '0.7rem',
        }}
      >
        <span>Concentration (HHI)<br /><strong>{r.hhi}</strong></span>
        <span>Turnover / month<br /><strong>{r.turnover}</strong></span>
        <span>Paper Sharpe<br /><strong>{r.sharpe}</strong></span>
        <span>Cap violations<br /><strong>{r.violations}</strong></span>
      </div>
      <p>
        Recorded stage-02 defaults on a 30-name, cost-free paper panel. The same
        signal becomes a different strategy when its sizing rule changes — and
        every rule breaks the cap after sequential cap-then-de-mean, which is
        why the position stage must be a joint constrained optimizer.
      </p>
    </div>
  );
}
