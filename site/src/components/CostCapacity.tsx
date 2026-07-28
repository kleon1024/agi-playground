import React, { useState } from 'react';

const MEASURED_ADV_USD = 12_578_055_538;
const MEASURED_DAILY_VOLATILITY = 0.017839;
const IMPACT_COEFFICIENT = 0.6;
const SPREAD_FRACTION = 2 / 10_000;
const COMMISSION_FRACTION = 0.5 / 10_000;

export default function CostCapacity(): React.ReactElement {
  const [book, setBook] = useState(10);
  const [turnover, setTurnover] = useState(6);
  const gross = 12;
  const tradedPerRebalance = book * 1_000_000 * turnover / 12;
  const participation = tradedPerRebalance / MEASURED_ADV_USD;
  const impact = IMPACT_COEFFICIENT * MEASURED_DAILY_VOLATILITY * Math.sqrt(participation);
  const cost = turnover * (COMMISSION_FRACTION + SPREAD_FRACTION + impact) * 100;
  return <div className="learning-widget">
    <p>Defaults reproduce the recorded USD 10m, 6x-turnover point: measured AAPL liquidity inputs plus the chapter's disclosed impact, spread, and commission assumptions.</p>
    <label>Book size, USD millions {book}<select aria-label="Book size in millions" value={book} onChange={e => setBook(Number(e.target.value))}>{[1, 10, 25, 50, 100].map(value => <option key={value} value={value}>{value}</option>)}</select></label>
    <label>Annual turnover {turnover.toFixed(1)}x<select aria-label="Annual turnover" value={turnover} onChange={e => setTurnover(Number(e.target.value))}>{[1, 3, 6, 10, 20].map(value => <option key={value} value={value}>{value}</option>)}</select></label>
    <p>Participation per rebalance: <strong>{(participation * 100).toFixed(4)}%</strong>. Paper return: <strong>{gross.toFixed(1)}%</strong>. Modeled annual cost: <strong>{cost.toFixed(4)}%</strong>. Net return: <strong>{(gross - cost).toFixed(4)}%</strong>.</p>
    <p>Holding paper return fixed cannot hold net return fixed: larger and faster books consume more liquidity.</p>
  </div>;
}
