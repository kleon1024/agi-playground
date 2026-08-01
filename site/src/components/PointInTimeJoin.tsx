import React, { useState } from 'react';

const JOINS = {
  naive: {
    label: 'naive join (keyed on fiscal period alone)',
    value: '174,472,000,000',
    filed: '2016-07-28',
    note: 'the latest restatement — silently handed back even when asked "what was knowable on 2015-07-31"',
  },
  pit: {
    label: 'point-in-time join (respects filed date)',
    value: '176,223,000,000',
    filed: '2015-07-31',
    note: 'the value actually filed on the as-of date, before any later revision existed',
  },
} as const;

type Join = keyof typeof JOINS;

export default function PointInTimeJoin(): React.ReactElement {
  const [join, setJoin] = useState<Join>('naive');
  const j = JOINS[join];
  return (
    <div className="learning-widget">
      <label>
        <input type="radio" checked={join === 'naive'} onChange={() => setJoin('naive')} /> naive join
      </label>{' '}
      <label>
        <input type="radio" checked={join === 'pit'} onChange={() => setJoin('pit')} /> point-in-time join
      </label>
      <p>
        Asking "what were MSFT's FY2015 total assets, as of 2015-07-31?" via the {j.label}:
      </p>
      <p style={{ fontSize: 'var(--type-lg)' }}>
        <strong>${j.value}</strong>, filed <strong>{j.filed}</strong>
      </p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        {join === 'naive'
          ? `This is ${j.note}. Microsoft's FY2015 total assets were first filed at $176.223B, then revised down by $1.75B (about 1%) thirteen months later — a naive join keyed only on fiscal period 2015-06-30 cannot tell the difference and always hands back whichever value is newest.`
          : `This is ${j.note}. point_in_time_value() filters every filed fact to only those filed at-or-before the as-of date, then keeps the most recent of those — the query a live backtest could actually have made on 2015-07-31.`}
      </p>
    </div>
  );
}
