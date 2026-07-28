/**
 * What each initialization choice in the dense-to-MoE remap is actually worth.
 *
 * Every loss here is measured, from
 * platform/training/05-upcycling/runs/2026-07-28-upcycle-88m.md, over 20
 * batches of 8x1024 held-out tokens on one 24GB card.
 *
 * The learner turns off one choice at a time and reads the resulting starting
 * loss against two reference lines: the parent at 3.0498 and the untrained
 * floor at ln(16512) = 9.7118. The control worth dwelling on is the last one,
 * which scores worse than knowing nothing.
 */
import React, { useState } from 'react';

const PARENT_LOSS = 3.0498;
const FLOOR = 9.7118;

type Control = {
  key: string;
  label: string;
  loss: number;
  verdict: 'exact' | 'damaged' | 'destroyed';
  note: string;
};

const CONTROLS: Control[] = [
  {
    key: 'correct',
    label: 'Every expert is a copy of the dense feed-forward',
    loss: 3.0499,
    verdict: 'exact',
    note: 'The remap as intended. Top-k routing renormalises its weights to sum to one, so identical experts compute w1*F(x) + w2*F(x) = F(x) — the dense output. The remaining 0.0001 is the order two floating-point sums were accumulated in, not a change of function.',
  },
  {
    key: 'router-zero',
    label: 'Same, but the router is initialised to zero instead of random',
    loss: 3.0498,
    verdict: 'exact',
    note: 'Identical to the parent, to four decimals. This is the sharpest demonstration that the routing is irrelevant at step 0: the output does not depend on it at all. It is still the wrong choice, because a zero router leaves every expert equally likely forever and the four copies never diverge into four different functions.',
  },
  {
    key: 'shared-copy',
    label: 'A shared expert is added, copying the parent instead of zeroed',
    loss: 3.7949,
    verdict: 'damaged',
    note: 'Costs 0.745 nats. The shared expert runs on every token in addition to the routed ones, so the block now emits roughly twice the feed-forward contribution the residual stream was trained to receive. Zeroing its output projection lets it start contributing nothing and learn its way in.',
  },
  {
    key: 'first-only',
    label: 'One expert copied, the other three randomly initialised',
    loss: 10.5968,
    verdict: 'destroyed',
    note: 'Above the untrained floor. Top-2 of 4 means a random expert is in the mix for almost every token, and half of each block output is noise. Partial copying is not a partial result — it is a broken model.',
  },
  {
    key: 'random',
    label: 'All experts randomly initialised, everything else copied',
    loss: 13.0573,
    verdict: 'destroyed',
    note: 'Worse than knowing nothing, by 3.35 nats. An untrained model spreads probability evenly and is merely uninformative. This one has trained embeddings and trained attention driving random feed-forwards, so it commits confidently to wrong tokens — and cross-entropy punishes confident errors far harder than uncertainty.',
  },
];

const VERDICT_TEXT: Record<Control['verdict'], string> = {
  exact: 'Starts at the parent. The surgery preserved the function.',
  damaged: 'Starts above the parent but below the floor. Trained weights are in there, wired wrongly.',
  destroyed: 'Starts above the untrained floor. This is worse than a model that knows nothing.',
};

const SCALE_MAX = 13.5;
const width = (loss: number) => (loss / SCALE_MAX) * 100;

export default function UpcycleSurgery(): React.ReactElement {
  const [index, setIndex] = useState(0);
  const current = CONTROLS[index];

  return (
    <div className="learning-widget">
      <p>
        The same 88M checkpoint, converted to a 258M mixture of experts five different
        ways, then scored on held-out text before any training. Only the feed-forward
        initialization changes.
      </p>

      <ul className="upcycle-controls">
        {CONTROLS.map((control, i) => (
          <li key={control.key}>
            <button
              type="button"
              aria-pressed={i === index}
              onClick={() => setIndex(i)}
            >
              <span className="upcycle-controls__label">{control.label}</span>
              <span className="upcycle-controls__loss">{control.loss.toFixed(4)}</span>
            </button>
            <span
              className="upcycle-bar"
              data-verdict={control.verdict}
              data-selected={i === index}
              style={{ width: `${width(control.loss)}%` }}
              aria-hidden="true"
            />
          </li>
        ))}
      </ul>

      <p className="upcycle-legend">
        Parent {PARENT_LOSS.toFixed(4)} &middot; untrained floor ln(16512) ={' '}
        {FLOOR.toFixed(4)}. Bars are drawn to a common scale, so a bar past the floor is a
        model that has been made worse than untrained.
      </p>

      <div className="objective-readout">
        <div>
          <span>Starting validation loss</span>
          <strong>{current.loss.toFixed(4)}</strong>
        </div>
        <div>
          <span>Against the parent</span>
          <strong>
            {current.loss - PARENT_LOSS >= 0 ? '+' : ''}
            {(current.loss - PARENT_LOSS).toFixed(4)}
          </strong>
        </div>
        <div>
          <span>Against the untrained floor</span>
          <strong>
            {current.loss - FLOOR >= 0 ? '+' : ''}
            {(current.loss - FLOOR).toFixed(4)}
          </strong>
        </div>
      </div>

      <p className="objective-note">{VERDICT_TEXT[current.verdict]}</p>

      <div className="widget-swap">
        {CONTROLS.map((control) => (
          <p className="widget-caption" key={control.key} data-shown={control.key === current.key}>
            {control.note}
          </p>
        ))}
      </div>

      <p>
        Measured on one 24GB card over 20 batches of 8x1024 held-out tokens, in{' '}
        <code>platform/training/05-upcycling/runs/2026-07-28-upcycle-88m.md</code>. Every
        variant loads without an exception and reports a plausible-looking number, which is
        the reason a loss comparison against the parent is the acceptance test and a
        successful load is not.
      </p>
    </div>
  );
}
