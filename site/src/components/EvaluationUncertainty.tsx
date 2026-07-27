import React, { useMemo, useState } from 'react';

function clamp(value: number): number {
  return Math.max(0, Math.min(1, value));
}

export default function EvaluationUncertainty(): React.ReactElement {
  const [sampleSize, setSampleSize] = useState(300);
  const [successRate, setSuccessRate] = useState(50);
  const probability = successRate / 100;

  const { trials, lower, upper } = useMemo(() => {
    const standardError = Math.sqrt(probability * (1 - probability) / sampleSize);
    const estimates = Array.from({ length: 12 }, (_, index) => (
      clamp(probability + Math.sin((index + 1) * 2.17) * standardError * 1.7)
    ));
    const z = 1.96;
    const denominator = 1 + z * z / sampleSize;
    const center = (probability + z * z / (2 * sampleSize)) / denominator;
    const margin = z * Math.sqrt(
      probability * (1 - probability) / sampleSize + z * z / (4 * sampleSize * sampleSize),
    ) / denominator;
    return {
      trials: estimates,
      lower: clamp(center - margin),
      upper: clamp(center + margin),
    };
  }, [probability, sampleSize]);

  return (
    <div className="learning-widget uncertainty-lab">
      <header className="lab-header">
        <div>
          <span className="lab-eyebrow">Sampling uncertainty</span>
          <strong>Is a four-point leaderboard gap distinguishable from noise?</strong>
        </div>
        <output>95% interval · {(lower * 100).toFixed(1)}–{(upper * 100).toFixed(1)}%</output>
      </header>

      <div className="lab-controls">
        <label>
          <span>Tasks <strong>{sampleSize}</strong></span>
          <input type="range" min={50} max={2000} step={50} value={sampleSize} onChange={(event) => setSampleSize(Number(event.target.value))} />
        </label>
        <label>
          <span>Observed success <strong>{successRate}%</strong></span>
          <input type="range" min={10} max={90} value={successRate} onChange={(event) => setSuccessRate(Number(event.target.value))} />
        </label>
      </div>

      <div className="uncertainty-lab__plot" aria-label="Twelve simulated repeat estimates">
        {trials.map((estimate, index) => (
          <div className="uncertainty-lab__trial" key={index}>
            <span style={{ transform: `scaleY(${estimate})` }} />
            <small>{(estimate * 100).toFixed(0)}</small>
          </div>
        ))}
      </div>

      <p>
        The model did not change across these repeats; only the sample did.
        Increasing the task count narrows both the Wilson interval and the
        spread of repeat estimates. Compare systems with paired task outcomes
        whenever possible, and report the interval rather than only the mean.
      </p>
    </div>
  );
}
