import React, { useState } from 'react';

const REGIMES = {
  '8': {
    wallClock: 152.5,
    ceilingPct: 8.5,
    mse: 0.0851,
    mseSpread: 0.0078,
    exactMatch: '19.3% - 22.0%',
  },
  '16': {
    wallClock: 660,
    ceilingPct: 39.4,
    mse: 0.0856,
    mseSpread: 0.0074,
    exactMatch: '8.7% - 33.3%',
  },
} as const;

type Frames = keyof typeof REGIMES;

export default function SequenceLengthScaling(): React.ReactElement {
  const [frames, setFrames] = useState<Frames>('8');
  const r = REGIMES[frames];
  const other = REGIMES[frames === '8' ? '16' : '8'];
  const wallClockRatio = REGIMES['16'].wallClock / REGIMES['8'].wallClock;
  return (
    <div className="learning-widget">
      <label>
        <input type="radio" checked={frames === '8'} onChange={() => setFrames('8')} /> 8 frames (stage 02)
      </label>{' '}
      <label>
        <input type="radio" checked={frames === '16'} onChange={() => setFrames('16')} /> 16 frames (this stage)
      </label>
      <p>wall-clock (mean): <strong>{r.wallClock}s</strong>, ceiling used: <strong>{r.ceilingPct}%</strong></p>
      <p>lm_completion MSE: <strong>{r.mse.toFixed(4)}</strong> (spread {r.mseSpread.toFixed(4)})</p>
      <p>exact-match rate across 3 seeds: <strong>{r.exactMatch}</strong></p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        {frames === '16'
          ? `Doubling frame count grew wall-clock ${wallClockRatio.toFixed(1)}x, more than the codec's roughly-linear-per-frame cost alone predicts -- consistent with the LM's attention cost over a longer token sequence growing faster than linear too. MSE barely moved (${other.mse.toFixed(4)} to ${r.mse.toFixed(4)}), but exact-match rate went from a tight 2.7-point spread to a 24.6-point spread across seeds -- the same underlying reconstruction quality, a much noisier discrete-token metric.`
          : `Compute headroom was large here -- only ${r.ceilingPct}% of the declared ceiling used -- which is exactly what stage 03's report flagged as room to spend on a harder version. Switch to 16 frames to see what that headroom actually cost.`}
      </p>
    </div>
  );
}
