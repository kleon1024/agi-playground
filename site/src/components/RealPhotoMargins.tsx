/**
 * The real-photo verdict: one metric, two comparisons, opposite answers.
 *
 * The vision pathway beats the text-only baseline by 1.5x its own seed spread
 * and loses to a hosted API by 22x it. Same arm, same spread, two verdicts --
 * which is why the mission's acceptance is NOT MET even though the finding it
 * set out to replicate did replicate.
 *
 * The hosted API is one run of a fixed endpoint over all 198 questions, so it
 * has no seeds and gets no spread line. Drawing a band around it would dress a
 * single measurement as a settled distribution; the rule instead falls back to
 * the vision arm's own spread, exactly as `core/report.py` does.
 *
 * Values from `runs/2026-08-01-real-photo-report.md`.
 */
import React from 'react';

import SpreadComparison, { type Group } from './chart/SpreadComparison';

const VISION = [0.2374, 0.2424, 0.2323];

const GROUPS: Group[] = [
  {
    name: 'Against text-only',
    meta: 'both arms trained from scratch, three seeds each',
    compare: [0, 1],
    arms: [
      { label: 'Text only', values: [0.2121, 0.1919, 0.2626] },
      { label: 'Vision', values: VISION, subject: true },
    ],
  },
  {
    name: 'Against a hosted API',
    meta: '198 questions, one run',
    compare: [0, 1],
    arms: [
      { label: 'Hosted API', values: [0.4596], note: 'one run, no seeds' },
      { label: 'Vision', values: VISION, subject: true },
    ],
  },
];

export default function RealPhotoMargins(): React.ReactElement {
  return (
    <SpreadComparison
      groups={GROUPS}
      domain={[0.17, 0.5]}
      ticks={[0.2, 0.3, 0.4, 0.5]}
      narrowTicks={[0.2, 0.4]}
      axisLabel="eval accuracy"
      selectLabel="Which comparison to judge"
      /* The mission's own report script holds every margin against vision's
         spread, because one of its references is a single API call. */
      spreadRule="subject"
      readout={['Margin, vision minus the other arm', 'Vision’s own seed spread']}
      lead={
        'The same vision pathway, held against two different things. Three seeds as circles, the '
        + 'line between them their spread, the upright bar their mean. Switch the comparison and '
        + 'the arm under test does not move — only what it is measured against.'
      }
      verdict={({ group, gap, widest, decisive }) => (
        <>
          <strong>
            {group.name}:{' '}
            {!decisive
              ? 'inside the noise band'
              : gap > 0
                ? 'vision is ahead by more than its own noise'
                : 'vision is behind by more than its own noise'}
            .
          </strong>{' '}
          {group.name === 'Against text-only'
            ? `Vision is ${gap.toFixed(4)} ahead and wanders ${widest.toFixed(4)} across its own `
              + 'seeds — a real margin, and a narrow one. This is stage 01’s synthetic-shapes '
              + 'finding replicating on real photographs.'
            : `Vision is ${Math.abs(gap).toFixed(4)} behind a fixed hosted endpoint, roughly `
              + `${(Math.abs(gap) / widest).toFixed(0)}x its own spread. The hosted arm has no `
              + 'spread of its own to compare against — it is one run of an API — so the rule '
              + 'falls back to vision’s, which is what the report script does.'}
        </>
      )}
      close={
        <>
          Both readings are true at once, and the mission&rsquo;s acceptance bar asked for the
          second one. A pathway trained from scratch on CPU reproduced its own earlier finding
          on real photographs and is nowhere near a hosted model that cost $0.2534 over the same
          198 questions. Reporting only the comparison it won would be choosing the baseline
          after seeing the result. One limit the drawing makes visible and the summary line does
          not: the text-only arm&rsquo;s own three seeds range 0.0707, wider than the 0.0152
          margin between the two means. That comparison rests on vision being stable, not on
          text-only being stable, and it is the narrower of the two claims this stage makes.
        </>
      }
    />
  );
}
