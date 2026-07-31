import React, { useState } from 'react';

const VISION = [0.5128, 0.5153, 0.2844];
const TEXT_ONLY = [0.3304, 0.3482, 0.3023];

function mean(xs: number[]): number {
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}

export default function VisionSeedSpread(): React.ReactElement {
  const [included, setIncluded] = useState([true, true, true]);
  const visionActive = VISION.filter((_, i) => included[i]);
  const textMean = mean(TEXT_ONLY);
  const visionMean = visionActive.length ? mean(visionActive) : NaN;
  const spread = visionActive.length ? Math.max(...visionActive) - Math.min(...visionActive) : NaN;
  const gap = visionMean - textMean;
  const beats = visionActive.length > 1 && Math.abs(gap) > spread;
  return (
    <div className="learning-widget">
      {VISION.map((v, i) => (
        <label key={i} style={{ marginRight: '1rem' }}>
          <input
            type="checkbox"
            checked={included[i]}
            onChange={() =>
              setIncluded((prev) => prev.map((x, j) => (j === i ? !x : x)))
            }
          />{' '}
          seed {i}: {v.toFixed(4)}
        </label>
      ))}
      <p>vision mean: <strong>{isNaN(visionMean) ? '--' : visionMean.toFixed(4)}</strong>, spread: <strong>{isNaN(spread) ? '--' : spread.toFixed(4)}</strong></p>
      <p>text-only mean: <strong>{textMean.toFixed(4)}</strong>, gap: <strong>{isNaN(gap) ? '--' : gap.toFixed(4)}</strong></p>
      <p>beats text-only outside noise: <strong>{visionActive.length > 1 ? (beats ? 'yes' : 'no') : '--'}</strong></p>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        {visionActive.length < 3
          ? 'With seed 2 (the collapsed run) excluded, the gap is real and decisive.'
          : 'With all 3 seeds, the gap (0.1105) is smaller than the seed spread (0.2309) -- not distinguishable from noise, which is why stage 02 cannot claim vision wins.'}
      </p>
    </div>
  );
}
