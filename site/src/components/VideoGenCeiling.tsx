/**
 * Mission 08's acceptance line and the ceiling sitting just behind it.
 *
 * The report prints one comparison -- LM completion against the frame-repeat
 * control -- and it passes by 5.5x the seed spread. The same three seeds carry
 * a second number the acceptance line never used: the MSE you get by decoding
 * the *true* future tokens through the same codec. That is the best stage 01's
 * codec could do even with a perfect sequence model, and the trained model is
 * already sitting on it: the gap is 0.0008 against a 0.0103 spread.
 *
 * Both readings come from the same three files, so the switch changes only what
 * the model is held against, never the arm under test. It also explains the
 * caveat the report reports beside its verdict -- exact-token match stays at
 * 6.7-22% while pixel MSE is at the ceiling, because wrong token sequences
 * decode to frames this codec cannot tell apart from the right ones.
 *
 * Values are the raw per-seed floats from
 * `../02-generation-model/runs/generation-seed{0,1,2}.json`, so the readout
 * reproduces `runs/2026-07-31-outcome-report.txt` rather than restating it.
 */
import React from 'react';

import SpreadComparison, { type Group } from './chart/SpreadComparison';

const LM = [0.0804300382733345, 0.08648347854614258, 0.08824601769447327];
const ORACLE = [0.07794064283370972, 0.08646281063556671, 0.08824008703231812];

const GROUPS: Group[] = [
  {
    name: 'Against the baseline',
    meta: 'the acceptance line mission.yaml declared',
    compare: [0, 1],
    arms: [
      { label: 'Frame repeat', values: [0.12808586657047272], note: 'fixed, no learning' },
      { label: 'LM completion', values: LM, subject: true },
    ],
  },
  {
    name: 'Against the codec ceiling',
    meta: 'the same three seeds, decoding true tokens',
    compare: [0, 1],
    arms: [
      { label: 'Oracle tokens', values: ORACLE },
      { label: 'LM completion', values: LM, subject: true },
    ],
  },
];

export default function VideoGenCeiling(): React.ReactElement {
  return (
    <SpreadComparison
      groups={GROUPS}
      domain={[0.075, 0.133]}
      ticks={[0.08, 0.1, 0.12]}
      narrowTicks={[0.08, 0.12]}
      axisLabel="reconstruction MSE"
      selectLabel="What to hold the trained model against"
      readout={['Gap, model minus the other arm', 'Seed spread it is held against']}
      lead={
        'Lower is better on this axis. Circles are the three seeds, the line between them their '
        + 'spread, the upright bar their mean; the frame-repeat control is one fixed number and '
        + 'carries no spread. Switch what the model is held against — the model row does not move.'
      }
      verdict={({ group, gap, widest, decisive }) => (
        <>
          <strong>
            {group.name === 'Against the baseline'
              ? 'The acceptance line passes.'
              : decisive
                ? 'The model is still short of the ceiling.'
                : 'The model is already at the ceiling.'}
          </strong>{' '}
          {group.name === 'Against the baseline'
            ? `Completion MSE is ${Math.abs(gap).toFixed(4)} below a control that simply repeats `
              + `the last prompt frame, and the three seeds move only ${widest.toFixed(4)} among `
              + `themselves — ${(Math.abs(gap) / widest).toFixed(1)}x the spread the contract `
              + 'required it to clear. Every seed beats the control on its own, not only the mean.'
            : `Decoding the true future tokens through the same codec lands ${Math.abs(gap).toFixed(4)} `
              + `away from what the model produced, while the oracle arm's own seeds range `
              + `${widest.toFixed(4)}. The remaining pixel error belongs to stage 01's codec, not `
              + 'to the sequence model — a better predictor has almost nothing left to win here.'}
        </>
      )}
      close={
        <>
          The second reading is why the caveat this report records beside its verdict is not a
          contradiction: only 6.7&ndash;22% of predicted token sequences match the true continuation
          exactly, yet pixel MSE sits on the oracle ceiling. This codec reconstructs badly enough
          that many wrong token sequences decode to frames it cannot distinguish from the right
          ones. The verdict is <strong>MET</strong> on the metric the contract named, and the chart
          shows how much headroom that metric still had &mdash; almost none, and the next gain
          would have to come from stage 01, not stage 02.
        </>
      }
    />
  );
}
