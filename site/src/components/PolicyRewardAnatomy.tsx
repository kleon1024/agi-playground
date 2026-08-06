/**
 * The policy anatomy: the same decoder, a two-part reward.
 *
 * Mission 06's policy is mission 01's Transformer (692,864 params)
 * instantiated for a 28-character grid vocabulary, driven by a two-part
 * reward — format credit (0.2/0.5/1.0 for legal moves) plus a terminal
 * goal-reached bit. The slider moves what share of the completion is legal
 * moves, so the reader can see format credit accrue without the goal ever
 * being reached — the mechanism behind the recorded collapse (seeds emit
 * constant direction strings at 0.062-0.078 greedy success, below random's
 * 0.222).
 */
import React, { useMemo, useState } from 'react';

const LEGAL_THRESHOLDS = [
  { min: 1.0, credit: 1.0, label: 'all legal — full format credit' },
  { min: 0.5, credit: 0.5, label: 'at least half legal — half credit' },
  { min: 0.0001, credit: 0.2, label: 'any legal — token credit' },
];

export default function PolicyRewardAnatomy(): React.ReactElement {
  const [legalShare, setLegalShare] = useState(1.0);
  const [reachedGoal, setReachedGoal] = useState(false);

  const credit = useMemo(() => {
    if (legalShare <= 0) return 0;
    for (const t of LEGAL_THRESHOLDS) {
      if (legalShare >= t.min) return t.credit;
    }
    return 0;
  }, [legalShare]);

  const total = credit + (reachedGoal ? 1.0 : 0.0);

  return (
    <div className="learning-widget">
      <label style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span>Share of completion that is legal moves</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={legalShare}
          aria-label="Share of legal moves"
          onChange={(e) => setLegalShare(Number(e.target.value))}
        />
        <strong>{Math.round(legalShare * 100)}%</strong>
      </label>
      <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', minHeight: '2.75rem' }}>
        <input
          type="checkbox"
          checked={reachedGoal}
          onChange={(e) => setReachedGoal(e.target.checked)}
        />
        Terminal goal reached
      </label>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(8rem, 1fr))',
          gap: '0.7rem',
          margin: '0.9rem 0',
        }}
      >
        <span>Format credit<br /><strong>{credit.toFixed(1)}</strong></span>
        <span>Terminal bit<br /><strong>{reachedGoal ? '1.0' : '0.0'}</strong></span>
        <span>Total reward<br /><strong>{total.toFixed(1)}</strong></span>
      </div>
      <p>
        A constant string like <code>RRRRRRRRRRRR</code> is all-legal, so it
        earns full format credit and never touches the terminal bit — a real
        gradient signal the policy optimizes. That is the collapse: the same
        692,864-parameter decoder that learns next-token prediction in mission
        01 never learns to navigate here, because the reward rewards the
        format without the goal.
      </p>
    </div>
  );
}
