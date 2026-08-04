/**
 * The nine recorded checkpoints of the first training loop, scrubbable.
 *
 * The chapter makes two claims about this run that a static PNG can only assert.
 * First, that the starting loss is not arbitrary: 4.3266 sits just above
 * ln(65) = 4.174, the score of a model that has learned nothing. Second, that the
 * train/validation gap opening from 0.0006 to 0.2630 is memorization becoming
 * visible. Both are properties of *when* you look, so the learner's variable here
 * is the checkpoint, and the readout is the gap.
 *
 * Every value is transcribed from
 * foundations/01-first-training-loop/runs/2026-07-26-tiny-shakespeare.md. Nothing
 * is interpolated: the marker snaps to recorded checkpoints, because the run
 * evaluated at 250-iteration intervals and the curve between them was not
 * measured.
 */
import React, { useState } from 'react';
import { scaleLinear } from 'd3-scale';
import { area, line as d3line } from 'd3-shape';

import Chart, { type Frame } from './chart/Chart';

interface Checkpoint {
  iter: number;
  train: number;
  val: number;
  seconds: number;
}

/** foundations/01-first-training-loop/runs/2026-07-26-tiny-shakespeare.md */
const RUN: Checkpoint[] = [
  { iter: 0, train: 4.3266, val: 4.3272, seconds: 0.6 },
  { iter: 250, train: 2.5375, val: 2.5448, seconds: 5.1 },
  { iter: 500, train: 2.0374, val: 2.0952, seconds: 9.2 },
  { iter: 750, train: 1.6536, val: 1.8108, seconds: 13.4 },
  { iter: 1000, train: 1.4815, val: 1.6638, seconds: 17.5 },
  { iter: 1250, train: 1.3846, val: 1.6047, seconds: 21.7 },
  { iter: 1500, train: 1.3269, val: 1.5698, seconds: 25.8 },
  { iter: 1750, train: 1.2844, val: 1.5447, seconds: 30.0 },
  { iter: 2000, train: 1.2753, val: 1.5383, seconds: 34.2 },
];

/** Cross-entropy of a uniform distribution over the 65-character vocabulary. */
const UNIFORM = Math.log(65);

const HEIGHT = 250;
const PADDING = { top: 18, right: 14, bottom: 44, left: 46 };

const LOSS_LO = 1.1;
const LOSS_HI = 4.5;
const LAST = RUN[RUN.length - 1].iter;

const scales = (frame: Frame) => ({
  x: scaleLinear().domain([0, LAST]).range([0, frame.innerWidth]),
  y: scaleLinear().domain([LOSS_LO, LOSS_HI]).range([frame.innerHeight, 0]),
});

export default function TrainingLossCurve(): React.ReactElement {
  const [i, setI] = useState(RUN.length - 1);
  const at = RUN[i];
  const gap = at.val - at.train;
  const prev = i > 0 ? RUN[i - 1] : null;
  /** 16,384 tokens per iteration over a 1.1MB character-level corpus — about 30
   *  passes by iteration 2000, which is the figure the chapter quotes. */
  const epochs = Math.max(1, Math.round((at.iter * 16384) / 1_100_000));

  const caption = (() => {
    if (i === 0) {
      return `Step 0 scores 4.3266 against ln(65) = 4.174, the cross-entropy of guessing uniformly among 65 characters. Landing just above it is the check that initialisation, loss and label alignment are all wired correctly — and the train/validation gap is 0.0006, because a model that has learned nothing has nothing to memorise.`;
    }
    const dTrain = (prev as Checkpoint).train - at.train;
    const dVal = (prev as Checkpoint).val - at.val;
    const share = dVal / dTrain;
    if (share > 0.95) {
      return `Between iteration ${(prev as Checkpoint).iter} and ${at.iter}, training loss fell ${dTrain.toFixed(4)} and validation loss fell ${dVal.toFixed(4)} — essentially all of it. The model is still learning the shape of English, which transfers to text it has not seen. The gap stands at ${gap.toFixed(4)}.`;
    }
    return `Between iteration ${(prev as Checkpoint).iter} and ${at.iter}, training loss fell ${dTrain.toFixed(4)} but validation loss fell only ${dVal.toFixed(4)} — ${Math.round(share * 100)}% of it. The rest bought memorisation of a corpus the model has passed over about ${epochs} times by now. The gap stands at ${gap.toFixed(4)}.`;
  })();

  return (
    <div className="learning-widget">
      <p>
        The nine checkpoints this run recorded. Point anywhere on the curves, or drag the slider,
        and read the distance between them.
      </p>

      <ul className="widget-legend">
        <li>
          <svg width="26" height="8" aria-hidden="true">
            <line x1="0" y1="4" x2="26" y2="4" stroke="var(--rehearse-action)" strokeWidth="2.5" />
          </svg>
          Training loss
        </li>
        <li>
          <svg width="26" height="8" aria-hidden="true">
            <line
              x1="0"
              y1="4"
              x2="26"
              y2="4"
              stroke="var(--rehearse-caution)"
              strokeWidth="2.5"
              strokeDasharray="6 4"
            />
          </svg>
          Validation loss <span>held-out text</span>
        </li>
      </ul>

      <Chart
        height={HEIGHT}
        padding={PADDING}
        label="Training and validation loss across the nine recorded checkpoints"
        onPointerAt={(x, frame) => {
          if (x === null) return;
          const iter = scales(frame).x.invert(x);
          /* Snap: the run evaluated every 250 iterations and nothing between two
             checkpoints was measured, so there is no value to read there. */
          setI(RUN.reduce((best, c, n) => (
            Math.abs(c.iter - iter) < Math.abs(RUN[best].iter - iter) ? n : best
          ), 0));
        }}
      >
        {(frame) => {
          const { innerWidth, innerHeight } = frame;
          const { x, y } = scales(frame);
          const path = (key: 'train' | 'val') =>
            d3line<Checkpoint>().x((c) => x(c.iter)).y((c) => y(c[key]))(RUN) ?? undefined;
          /* The full sentence needs about 250px; below that it would run past the
             frame, and a clipped annotation reads as a rendering fault. */
          const note = innerWidth < 270
            ? 'ln(65) = 4.174'
            : 'ln(65) = 4.174, a model that knows nothing';

          return (
            <g transform={`translate(${PADDING.left},${PADDING.top})`}>
              {/* The gap between the curves is the thing being read, so it is one
                  filled region rather than something the eye has to measure. */}
              <path
                d={area<Checkpoint>()
                  .x((c) => x(c.iter))
                  .y0((c) => y(c.train))
                  .y1((c) => y(c.val))(RUN) ?? undefined}
                fill="var(--rehearse-caution-soft)"
                stroke="none"
              />

              <line
                x1={0}
                x2={innerWidth}
                y1={y(UNIFORM)}
                y2={y(UNIFORM)}
                stroke="var(--rehearse-copy-muted)"
                strokeDasharray="3 4"
              />
              {/* Parked over the flat stretch of the curves: at the right edge it
                  collided with the checkpoint marker, and at the left with the
                  initial descent. */}
              <text
                x={innerWidth * 0.31}
                y={y(UNIFORM) - 7}
                fill="var(--rehearse-copy-muted)"
                fontSize={13}
              >
                {note}
              </text>

              <path d={path('train')} fill="none" stroke="var(--rehearse-action)" strokeWidth="2" />
              <path
                d={path('val')}
                fill="none"
                stroke="var(--rehearse-caution)"
                strokeWidth="2"
                strokeDasharray="6 4"
              />

              <line
                x1={x(at.iter)}
                x2={x(at.iter)}
                y1={0}
                y2={innerHeight}
                stroke="var(--rehearse-ink)"
                strokeWidth="1"
              />
              <circle cx={x(at.iter)} cy={y(at.train)} r="4" fill="var(--rehearse-action)" />
              <circle cx={x(at.iter)} cy={y(at.val)} r="4" fill="var(--rehearse-caution)" />

              <line x1={0} x2={innerWidth} y1={innerHeight} y2={innerHeight} stroke="var(--rehearse-rule)" />
              {[4, 3, 2].map((tick) => (
                <text
                  key={tick}
                  x={-8}
                  y={y(tick) + 4}
                  textAnchor="end"
                  fill="var(--rehearse-copy-muted)"
                  fontSize={13}
                >
                  {tick.toFixed(1)}
                </text>
              ))}
              <text x={0} y={innerHeight + 22} fill="var(--rehearse-copy-muted)" fontSize={13}>
                iteration 0
              </text>
              <text
                x={innerWidth}
                y={innerHeight + 22}
                textAnchor="end"
                fill="var(--rehearse-copy-muted)"
                fontSize={13}
              >
                {LAST}
              </text>
            </g>
          );
        }}
      </Chart>

      <div className="widget-controls">
        <label>
          <span>Checkpoint</span>
          <input
            type="range"
            min={0}
            max={RUN.length - 1}
            step={1}
            value={i}
            onChange={(e) => setI(Number(e.target.value))}
          />
        </label>
        <span className="widget-controls__status">
          iteration {at.iter} &middot; {at.seconds.toFixed(1)}s
        </span>
      </div>

      <div className="objective-readout">
        <div>
          <span>Training loss</span>
          <strong>{at.train.toFixed(4)}</strong>
        </div>
        <div>
          <span>Validation loss</span>
          <strong>{at.val.toFixed(4)}</strong>
        </div>
        <div>
          <span>Gap</span>
          <strong>{gap.toFixed(4)}</strong>
        </div>
      </div>

      <p className="widget-caption">{caption}</p>

      <p>
        Every number here is transcribed from{' '}
        <code>runs/2026-07-26-tiny-shakespeare.md</code>, which evaluated every 250
        iterations on one 24GB card. The curve between two checkpoints was never
        measured, so the marker snaps to recorded points rather than sliding
        continuously between them.
      </p>
    </div>
  );
}
