import React, { useState } from 'react';

// The only fold configuration this repository has actually run. Every other
// combination of the two controls below was never executed, so this component
// refuses to print a statistic for it rather than interpolating one: an
// invented number set in the same sentence as two measured ones reads as a
// third measurement. Recorded in
// missions/03-quantitative-research/03-walk-forward-validation/runs/.
const MEASURED = {
  purgeDays: 5,
  gapDays: 5,
  shuffled: 0.7393,
  chronological: 0.9722,
  protected: 0.9722,
};

const DAY_CHOICES = [0, 5, 10, 20];

export default function PurgedFolds(): React.ReactElement {
  const [purgeDays, setPurgeDays] = useState(MEASURED.purgeDays);
  const [gapDays, setGapDays] = useState(MEASURED.gapDays);
  const isMeasured = purgeDays === MEASURED.purgeDays && gapDays === MEASURED.gapDays;
  const moreProtection = purgeDays + gapDays > MEASURED.purgeDays + MEASURED.gapDays;

  return (
    <div className="learning-widget">
      <p>
        The label window is five days, so a five-day purge is the smallest window that removes
        every training row whose label reaches into the test block. That configuration is the one
        that was run.
      </p>

      <label>
        Purged label days
        <select
          aria-label="Purged label days"
          value={purgeDays}
          onChange={(event) => setPurgeDays(Number(event.target.value))}
        >
          {DAY_CHOICES.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>

      <label>
        Boundary gap days
        <select
          aria-label="Boundary gap days"
          value={gapDays}
          onChange={(event) => setGapDays(Number(event.target.value))}
        >
          {DAY_CHOICES.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>

      <p>
        Invalid shuffled estimate: <strong>{MEASURED.shuffled.toFixed(4)}</strong>. Chronological,
        unpurged: <strong>{MEASURED.chronological.toFixed(4)}</strong>. Both are properties of the
        split, not of these two controls, so neither moves.
      </p>

      {isMeasured ? (
        <p>
          Purged {purgeDays}d, gapped {gapDays}d: <strong>{MEASURED.protected.toFixed(4)}</strong>.
          Identical to the unpurged number — in this run, purging changed nothing. That is the
          recorded result, not a demonstration that purging is unnecessary.
        </p>
      ) : (
        <p>
          Purged {purgeDays}d, gapped {gapDays}d: <strong>not run</strong>. This configuration was
          never executed, so there is no statistic to show.{' '}
          {purgeDays < MEASURED.purgeDays
            ? 'A purge shorter than the five-day label leaves training rows whose labels reach into the test block, which is the leak this control exists to close.'
            : moreProtection
              ? 'Wider windows discard more training rows, so the statistic is computed on less data; whether it rises or falls here is not something this page can tell you without running it.'
              : 'Change the command in the run record and execute it if you want this number.'}
        </p>
      )}

      <p>
        A lower protected statistic is not worse evidence; it is less contaminated evidence. The
        reason to widen a window is the label definition, never the number that comes out.
      </p>
    </div>
  );
}
