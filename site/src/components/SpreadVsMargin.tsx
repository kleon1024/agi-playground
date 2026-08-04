/**
 * The noise-band rule with its own measurement left visible.
 *
 * `report.py` decides each comparison against that arm's *measured* seed
 * spread, not against a number anyone chose. The slider here exists to falsify
 * the obvious objection -- "a stricter bar would have changed the verdict" --
 * so it deliberately does not replace the measured spread: every row keeps
 * showing the spread the run recorded and the verdict that spread produces,
 * beside whatever the reader's threshold would say instead.
 *
 * Margins and spreads are stage 02's own, from
 * `runs/2026-07-31-outcome-report.md`: greedy decode mean 0.0727 with spread
 * 0.016, sampled decode mean 0.1787 with spread 0.066, against a 0.222 random
 * baseline and a 0.824 scripted-greedy baseline.
 */
import React, { useState } from 'react';

interface Comparison {
  name: string;
  margin: number;
  /** max(per_seed) - min(per_seed) for the candidate arm, as recorded. */
  spread: number;
}

const COMPARISONS: Comparison[] = [
  { name: 'greedy decode vs random', margin: -0.1493, spread: 0.016 },
  { name: 'greedy decode vs greedy baseline', margin: -0.7513, spread: 0.016 },
  { name: 'sampled decode vs random', margin: -0.0433, spread: 0.066 },
  { name: 'sampled decode vs greedy baseline', margin: -0.6453, spread: 0.066 },
];

const decisive = (c: Comparison, bar: number) => Math.abs(c.margin) > bar;

export default function SpreadVsMargin(): React.ReactElement {
  const [threshold, setThreshold] = useState(0.05);
  const disagreements = COMPARISONS.filter(
    (c) => decisive(c, c.spread) !== decisive(c, threshold),
  );

  return (
    <div className="learning-widget">
      <p>
        Each block below is one comparison stage 02 ran. &ldquo;At that spread&rdquo; is the
        verdict <code>report.py</code> printed, decided against that arm&rsquo;s own measured
        spread. Move the threshold and the last line shows what a chosen bar would have said
        instead.
      </p>

      <label>
        <span>Chosen threshold</span>
        <input
          type="range"
          min={0.01}
          max={0.1}
          step={0.005}
          value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
        />
        <strong>{threshold.toFixed(3)}</strong>
      </label>

      <ul className="verdict-rows">
        {COMPARISONS.map((c) => {
          const recorded = decisive(c, c.spread);
          const chosen = decisive(c, threshold);
          return (
            <li key={c.name}>
              <h4>{c.name}</h4>
              <dl>
                <div>
                  <dt>margin</dt>
                  <dd>{c.margin.toFixed(4)}</dd>
                </div>
                <div>
                  <dt>measured spread</dt>
                  <dd>{c.spread.toFixed(3)}</dd>
                </div>
                <div>
                  <dt>at that spread</dt>
                  <dd data-verdict={recorded ? 'decisive' : 'noise'}>
                    {recorded ? 'decisive loss' : 'inside the noise band'}
                  </dd>
                </div>
                <div>
                  <dt>at {threshold.toFixed(3)}</dt>
                  <dd data-verdict={chosen ? 'decisive' : 'noise'}>
                    {chosen ? 'decisive loss' : 'inside the noise band'}
                  </dd>
                </div>
              </dl>
            </li>
          );
        })}
      </ul>

      <p className="widget-caption">
        {disagreements.length === 0
          ? 'At this threshold every row agrees with the recorded verdict. The measured spreads '
            + '(0.016 for greedy decode, 0.066 for sampled) are what actually decided them.'
          : `${disagreements.length === 1 ? 'One row disagrees' : `${disagreements.length} rows disagree`}`
            + ` with the recorded verdict at this threshold: ${disagreements.map((c) => c.name).join(', ')}.`
            + ' Only the three-seed range the run actually produced gets to decide, which is why'
            + ' the rule names it instead of a fixed number.'}
      </p>

      <p>
        Sweeping the whole range moves only <em>sampled decode vs random</em>: its margin of 0.0433 is
        smaller than the 0.066 its three seeds already wandered, so it is a no-result at the
        measured spread and would read as a loss under any bar below 0.0433. The other three
        margins are large enough that no threshold in this range touches them &mdash; the verdict
        does not depend on where the line is drawn.
      </p>
    </div>
  );
}
