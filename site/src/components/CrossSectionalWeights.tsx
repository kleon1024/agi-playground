/**
 * Why sizing is part of the strategy, not a post-processing detail.
 *
 * The stage 02 core run held one momentum signal family fixed and measured how
 * four sizing rules changed concentration and turnover. Select one rule to see
 * its recorded paper-portfolio diagnostics; these are not forecasts.
 */
import React, { useState } from 'react';

const RULES = {
  'Equal-weight decile': { hhi: '0.6667', turnover: '0.638', gross: '2.00', constrainedGross: '0.16', violations: '7', belief: 'Only the tails contain useful order.' },
  'Rank-proportional': { hhi: '0.1776', turnover: '0.348', gross: '2.00', constrainedGross: '1.32', violations: '47', belief: 'Order matters across the full universe; gap size does not.' },
  'Signal-proportional': { hhi: '0.2243', turnover: '0.369', gross: '2.00', constrainedGross: '1.21', violations: '35', belief: 'Raw score magnitude represents conviction.' },
  'Volatility-scaled': { hhi: '0.1952', turnover: '0.404', gross: '2.00', constrainedGross: '1.21', violations: '43', belief: 'Conviction should be adjusted for trailing risk.' },
};

export default function CrossSectionalWeights(): React.ReactElement {
  const [ruleName, setRuleName] = useState<keyof typeof RULES>('Rank-proportional');
  const rule = RULES[ruleName];
  return (
    <div className="learning-widget">
      <label style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span>Sizing rule</span>
        <select aria-label="Sizing rule" value={ruleName} onChange={(event) => setRuleName(event.target.value as keyof typeof RULES)}>
          {Object.keys(RULES).map((name) => <option key={name}>{name}</option>)}
        </select>
      </label>
      <p style={{ margin: '0.9rem 0' }}><strong>Belief encoded:</strong> {rule.belief}</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(8rem, 1fr))', gap: '0.7rem' }}>
        <span>Raw gross<br /><strong>{rule.gross}</strong></span>
        <span>Concentration (HHI)<br /><strong>{rule.hhi}</strong></span>
        <span>Turnover / month<br /><strong>{rule.turnover}</strong></span>
        <span>Gross after naive constraints<br /><strong>{rule.constrainedGross}</strong></span>
        <span>Cap violations after sector de-mean<br /><strong>{rule.violations}</strong></span>
      </div>
      <p>Measured defaults from the 2026-07-27 stage 02 CPU run on a 30-name, cost-free paper panel. The same signal becomes a different strategy when its sizing rule changes. Post-hoc cap then sector de-mean can break the cap; a production optimizer must satisfy both constraints together.</p>
    </div>
  );
}
