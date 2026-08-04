/**
 * Three optimizers on one bowl, with the condition number in the reader's hands.
 *
 * The chapter's static plot shows a single bowl at A/B = 100. That picture can
 * only assert what conditioning does; it cannot let the reader test it. The
 * chapter's own exercises 1 and 3 ask exactly that — push the learning rate past
 * the stability threshold, widen the condition number, watch what degrades — so
 * the causal variable here is the condition number and nothing else. The three
 * learning rates stay exactly as the run record set them.
 *
 * The arithmetic below is a transcription of core/optimizers.py, including the
 * sign-flip counter's habit of dropping the first and last point. At A = 100 it
 * reproduces the recorded run exactly: 343/138/82 steps and 341/47/4 flips. The
 * widget prints that agreement rather than asking to be trusted on it.
 *
 * The reading it makes available, which the static plot cannot: SGD needs 343
 * steps at A = 10 and 343 steps at A = 100. The oscillation changes completely
 * (0 flips against 341) and the step count does not move at all, because the
 * bottleneck was never the steep axis.
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { scaleLinear } from 'd3-scale';

import Chart from './chart/Chart';
import { useAutoplayOnView, useFrameLoop } from './useMotionClock';

const B = 1;
const START: Point = [1, 1];
const MAX_STEPS = 4000;
const LOSS_TOL = 1e-6;
/** Past this magnitude the run is not coming back; core/ would run to MAX_STEPS. */
const DIVERGED_AT = 1e6;

type Point = [number, number];

interface Run {
  history: Point[];
  steps: number | null;
  diverged: boolean;
  flips: number;
}

const loss = (A: number, [x, y]: Point) => 0.5 * (A * x * x + B * y * y);
const grad = (A: number, [x, y]: Point): Point => [A * x, B * y];

/** Sign flips on the steep axis, counted as `per_axis_progress` counts them. */
function signFlips(history: Point[]): number {
  const signs = history.slice(1, -1).map(([x]) => Math.sign(x));
  let flips = 0;
  for (let i = 1; i < signs.length; i += 1) {
    if (signs[i] !== signs[i - 1]) flips += 1;
  }
  return flips;
}

function integrate(A: number, step: (p: Point, n: number) => Point): Run {
  let p: Point = [...START] as Point;
  const history: Point[] = [p];
  for (let n = 1; n <= MAX_STEPS; n += 1) {
    p = step(p, n);
    history.push(p);
    if (!Number.isFinite(p[0]) || Math.abs(p[0]) > DIVERGED_AT) {
      return { history, steps: null, diverged: true, flips: signFlips(history) };
    }
    if (loss(A, p) < LOSS_TOL) {
      return { history, steps: n, diverged: false, flips: signFlips(history) };
    }
  }
  return { history, steps: null, diverged: false, flips: signFlips(history) };
}

function runSgd(A: number, lr: number): Run {
  return integrate(A, (p) => {
    const g = grad(A, p);
    return [p[0] - lr * g[0], p[1] - lr * g[1]];
  });
}

function runMomentum(A: number, lr: number, mu: number): Run {
  let v: Point = [0, 0];
  return integrate(A, (p) => {
    const g = grad(A, p);
    v = [mu * v[0] - lr * g[0], mu * v[1] - lr * g[1]];
    return [p[0] + v[0], p[1] + v[1]];
  });
}

function runAdam(A: number, lr: number, b1 = 0.9, b2 = 0.999, eps = 1e-8): Run {
  let m: Point = [0, 0];
  let v: Point = [0, 0];
  return integrate(A, (p, n) => {
    const g = grad(A, p);
    m = [b1 * m[0] + (1 - b1) * g[0], b1 * m[1] + (1 - b1) * g[1]];
    v = [b2 * v[0] + (1 - b2) * g[0] * g[0], b2 * v[1] + (1 - b2) * g[1] * g[1]];
    const c1 = 1 - b1 ** n;
    const c2 = 1 - b2 ** n;
    return [
      p[0] - (lr * (m[0] / c1)) / (Math.sqrt(v[0] / c2) + eps),
      p[1] - (lr * (m[1] / c1)) / (Math.sqrt(v[1] / c2) + eps),
    ];
  });
}

/** Learning rates are the run record's, held fixed so conditioning is the only variable. */
const OPTIMIZERS = [
  { id: 'sgd', name: 'SGD', detail: 'lr 0.019', dash: undefined, stroke: 'var(--rehearse-caution)' },
  { id: 'momentum', name: 'Momentum', detail: 'lr 0.01, mu 0.9', dash: '7 4', stroke: 'var(--rehearse-emphasis)' },
  { id: 'adam', name: 'Adam', detail: 'lr 0.1', dash: '2 4', stroke: 'var(--rehearse-action)' },
] as const;

interface Regime {
  A: number;
  label: string;
  recorded: boolean;
  note: string;
}

const REGIMES: Regime[] = [
  {
    A: 10,
    label: 'A = 10',
    recorded: false,
    note: 'Gentle bowl: eta*A = 0.19, so SGD’s steep axis shrinks by a factor of 0.81 every step and never crosses zero — zero sign flips. And yet SGD still needs the same 343 steps it needed at ten times the conditioning. The steep axis was never what held it up; the shallow axis, decaying by 0.981 a step, was.',
  },
  {
    A: 100,
    label: 'A = 100 (recorded)',
    recorded: true,
    note: 'The recorded run. eta*A = 1.9, just under the divergence threshold of 2, so every SGD step overshoots and lands on the far side of the minimum: 341 flips in 343 steps. Momentum’s velocity cancels most of that ringing, and Adam’s per-parameter normalisation nearly removes it — while the step count barely improves on the shallow axis, which is the axis actually setting the pace.',
  },
  {
    A: 1000,
    label: 'A = 1000',
    recorded: false,
    note: 'Exercise 3’s bowl. eta*A = 19, so SGD’s steep axis multiplies by -18 every step and leaves the plot in a handful of them. Momentum diverges too: its stability bound 2(1+mu)/A = 0.0038 is now below its learning rate of 0.01. Only Adam survives, because it divides each step by that parameter’s own running gradient scale instead of trusting a learning rate chosen for a different curvature.',
  },
];

/*
 * Both panels are drawn against the step index, not against each other.
 *
 * A phase portrait in (x, y) is the natural first thought and the wrong one: at
 * a condition number of 100 the steep axis collapses within a few dozen steps
 * while the shallow axis takes hundreds, so every trajectory folds onto the two
 * axis lines and the three optimizers become one smear. Plotting each coordinate
 * against the step index separates them, and it puts the chapter's actual claim
 * on screen — the top panel is where the oscillation lives, the bottom panel is
 * where the time goes, and they are not the same panel.
 */
const PADDING = { top: 30, right: 12, bottom: 32, left: 46 };
const GAP = 48;
const TOP_H = 86;
const BOT_H = 132;
const HEIGHT = PADDING.top + TOP_H + GAP + BOT_H + PADDING.bottom;

/** Panel offsets inside the plot area. */
const TOP_Y0 = 0;
const BOT_Y0 = TOP_H + GAP;

/** Steep-axis panel: clamped so a diverging run leaves the frame instead of flattening it. */
const X_CLAMP = 1.25;
/** Loss panel, log10. The floor sits just under the 1e-6 tolerance the run record used. */
const LOG_HI = 3.2;
const LOG_LO = -6.6;

/**
 * The steep axis is spent long before the run is. At A = 100 all 341 sign flips
 * happen inside the first ~50 steps, so drawn against the full 343-step axis the
 * ringing is a 7%-wide smudge followed by a flat line. The top panel therefore
 * has its own zoomed axis, labelled with the window it shows.
 */
const TOP_STEPS = 60;

const topY = scaleLinear().domain([-X_CLAMP, X_CLAMP]).range([TOP_Y0 + TOP_H, TOP_Y0]);
const botY = scaleLinear().domain([LOG_LO, LOG_HI]).range([BOT_Y0 + BOT_H, BOT_Y0]);

/**
 * A polyline over step index that stops where the run leaves the panel.
 *
 * The out-of-range point is drawn clamped to the edge before stopping, rather
 * than dropped. Dropping it renders a diverging arm as nothing at all — at
 * A = 1000 SGD is out of range by its first step, so the honest-looking "cut the
 * path" version showed an empty panel, which a reader reads as a broken widget
 * and not as a run that exploded. Running off the edge is the reading we want.
 */
function series(
  values: number[],
  count: number,
  x: (i: number) => number,
  toY: (v: number) => number,
  lo: number,
  hi: number,
): string {
  const parts: string[] = [];
  const n = Math.min(values.length, Math.max(2, count));
  for (let i = 0; i < n; i += 1) {
    const v = values[i];
    if (!Number.isFinite(v)) break;
    const clamped = Math.min(hi, Math.max(lo, v));
    parts.push(`${parts.length === 0 ? 'M' : 'L'}${x(i).toFixed(1)} ${toY(clamped).toFixed(1)}`);
    if (clamped !== v) break;
  }
  return parts.join(' ');
}

const SWEEP_MS = 4200;

export default function OptimizerTrajectory(): React.ReactElement {
  const [index, setIndex] = useState(1);
  /**
   * Starts complete rather than empty: with reduced motion the loop never runs,
   * and a widget whose static reading is a blank plot explains nothing. Autoplay
   * rewinds to 0 when, and only when, it is actually allowed to animate.
   */
  const [progress, setProgress] = useState(1);
  /**
   * The loop reads and writes this directly. Deriving the stop condition from
   * `progress` in a second effect instead is a race: on the render where autoplay
   * flips `playing` true, the rewind effect and the stop effect both see the old
   * progress of 1, so the sweep is cancelled on the frame it begins.
   */
  const progressRef = useRef(1);
  const setP = (v: number) => {
    progressRef.current = v;
    setProgress(v);
  };
  const { ref, playing, setPlaying } = useAutoplayOnView<HTMLDivElement>();

  const regime = REGIMES[index];
  const runs = useMemo(() => {
    const A = regime.A;
    return {
      sgd: runSgd(A, 0.019),
      momentum: runMomentum(A, 0.01, 0.9),
      adam: runAdam(A, 0.1),
    } as Record<string, Run>;
  }, [regime.A]);

  const longest = Math.max(...Object.values(runs).map((r) => r.history.length));

  useEffect(() => {
    if (playing && progressRef.current >= 1) setP(0);
    // setP is stable enough for this one-shot rewind; only `playing` should retrigger it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing]);

  useFrameLoop(playing, (dt) => {
    const next = Math.min(1, progressRef.current + dt / SWEEP_MS);
    setP(next);
    if (next >= 1) setPlaying(false);
  });

  /** Switching bowls shows the finished comparison; the sweep stays opt-in. */
  const select = (i: number) => {
    setIndex(i);
    setP(1);
    setPlaying(false);
  };

  const shownSteps = Math.round(progress * longest);
  const topWindow = Math.min(TOP_STEPS, longest - 1);
  const axisText = { fill: 'var(--rehearse-copy-muted)', fontSize: 13 };

  return (
    <div className="learning-widget" ref={ref}>
      <p>
        The same three update rules, the same start at (1,&nbsp;1), the same three learning
        rates from the run record. The only thing that changes is how much steeper the
        bowl is along <em>x</em> than along <em>y</em>.
      </p>

      <div className="widget-controls" role="group" aria-label="Condition number">
        {REGIMES.map((r, i) => (
          <button key={r.A} type="button" aria-pressed={i === index} onClick={() => select(i)}>
            {r.label}
          </button>
        ))}
      </div>

      <ul className="widget-legend">
        {OPTIMIZERS.map((o) => (
          <li key={o.id}>
            <svg width="26" height="8" aria-hidden="true">
              <line
                x1="0"
                y1="4"
                x2="26"
                y2="4"
                stroke={o.stroke}
                strokeWidth="2.5"
                strokeDasharray={o.dash}
              />
            </svg>
            {o.name} <span>{o.detail}</span>
          </li>
        ))}
      </ul>

      <Chart
        height={HEIGHT}
        padding={PADDING}
        label={`Steep-axis position and loss against step index at condition number ${regime.A}`}
      >
        {(frame) => {
          const { innerWidth } = frame;
          const xTop = scaleLinear().domain([0, Math.max(1, topWindow)]).range([0, innerWidth]);
          const xBot = scaleLinear().domain([0, Math.max(1, longest - 1)]).range([0, innerWidth]);

          return (
            <g transform={`translate(${PADDING.left},${PADDING.top})`}>
              <clipPath id="ot-top">
                <rect x={0} y={TOP_Y0} width={innerWidth} height={TOP_H} />
              </clipPath>
              <clipPath id="ot-bot">
                <rect x={0} y={BOT_Y0} width={innerWidth} height={BOT_H} />
              </clipPath>

              <text x={0} y={TOP_Y0 - 9} {...axisText}>
                steep axis x &mdash; first {topWindow} steps
              </text>
              <rect
                x={0}
                y={TOP_Y0}
                width={innerWidth}
                height={TOP_H}
                fill="none"
                stroke="var(--rehearse-rule)"
              />
              <line
                x1={0}
                x2={innerWidth}
                y1={topY(0)}
                y2={topY(0)}
                stroke="var(--rehearse-rule)"
                strokeDasharray="3 3"
              />
              <text x={-6} y={topY(0) + 4} textAnchor="end" {...axisText}>
                0
              </text>
              <text x={-6} y={TOP_Y0 + 10} textAnchor="end" {...axisText}>
                +1
              </text>
              <g clipPath="url(#ot-top)">
                {OPTIMIZERS.map((o) => (
                  <path
                    key={o.id}
                    d={series(
                      runs[o.id].history.slice(0, topWindow + 1).map(([x]) => x),
                      shownSteps,
                      xTop,
                      topY,
                      -X_CLAMP,
                      X_CLAMP,
                    )}
                    fill="none"
                    stroke={o.stroke}
                    strokeWidth="1.6"
                    strokeDasharray={o.dash}
                  />
                ))}
              </g>

              <text x={0} y={BOT_Y0 - 9} {...axisText}>
                loss (log scale)
              </text>
              <rect
                x={0}
                y={BOT_Y0}
                width={innerWidth}
                height={BOT_H}
                fill="none"
                stroke="var(--rehearse-rule)"
              />
              <line
                x1={0}
                x2={innerWidth}
                y1={botY(-6)}
                y2={botY(-6)}
                stroke="var(--rehearse-action)"
                strokeDasharray="4 3"
              />
              <text x={-6} y={botY(-6) + 4} textAnchor="end" {...axisText}>
                1e-6
              </text>
              <text x={-6} y={botY(0) + 4} textAnchor="end" {...axisText}>
                1
              </text>
              <g clipPath="url(#ot-bot)">
                {OPTIMIZERS.map((o) => (
                  <path
                    key={o.id}
                    d={series(
                      runs[o.id].history.map((p) => Math.log10(Math.max(loss(regime.A, p), 1e-30))),
                      shownSteps,
                      xBot,
                      botY,
                      LOG_LO,
                      LOG_HI,
                    )}
                    fill="none"
                    stroke={o.stroke}
                    strokeWidth="1.8"
                    strokeDasharray={o.dash}
                  />
                ))}
              </g>

              <text x={0} y={BOT_Y0 + BOT_H + 22} {...axisText}>
                step 0
              </text>
              <text x={innerWidth} y={BOT_Y0 + BOT_H + 22} textAnchor="end" {...axisText}>
                step {longest - 1}
              </text>
            </g>
          );
        }}
      </Chart>

      <div className="widget-controls">
        <button
          type="button"
          onClick={() => {
            if (progress >= 1) setProgress(0);
            setPlaying(!playing);
          }}
        >
          {playing ? 'Pause' : progress >= 1 ? 'Replay' : 'Play'}
        </button>
        <span className="widget-controls__status">
          step {Math.min(shownSteps, longest - 1)} of {longest - 1}
        </span>
      </div>

      {/* The learning-widget frame clips rather than scrolls, so a table wider than
          the frame loses its last column outright at 390px. The hyperparameters stay
          in the legend above instead of being repeated into this first column. */}
      <div className="widget-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Optimizer</th>
              <th scope="col">Steps to 1e-6</th>
              <th scope="col">Sign flips</th>
            </tr>
          </thead>
          <tbody>
            {OPTIMIZERS.map((o) => {
              const run = runs[o.id];
              return (
                <tr key={o.id}>
                  <th scope="row">{o.name}</th>
                  <td>{run.diverged ? 'diverged' : (run.steps ?? 'no convergence in 4000')}</td>
                  <td>{run.diverged ? '—' : run.flips}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="widget-swap">
        {REGIMES.map((r, i) => (
          <p className="widget-caption" key={r.A} data-shown={i === index}>
            {r.note}
          </p>
        ))}
      </div>

      <p>
        At A&nbsp;=&nbsp;100 the numbers above are 343, 138 and 82 steps with 341, 47 and 4
        sign flips &mdash; the values recorded in{' '}
        <code>runs/optimizer-comparison.json</code>, recomputed here from the same update
        rules. The other two columns are that same arithmetic with <em>A</em> changed; they
        are reproducible from <code>core/optimizers.py</code> but they are not in the run
        record, so treat them as the exercise they are rather than as measured results.
      </p>
    </div>
  );
}
