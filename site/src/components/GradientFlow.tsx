/**
 * The backward walk over this chapter's own graph, with the `+=` / `=` choice
 * as the control.
 *
 * Section 3 states that assigning instead of accumulating drops one of `a`'s
 * two contributions. What prose cannot show is the shape of the resulting
 * failure: the walk still completes, `b` and `c` still come out exactly right,
 * and only `a` is wrong -- wrong by a sign, so a training step would move it
 * the wrong way. That is why the bug is easy to write and hard to notice, and
 * it is what the learner watches here.
 *
 * Every number is recomputed in the browser from a = 0.7, b = -0.5, c = 1.2
 * and checked against the recorded gradients in
 * foundations/03-backpropagation/runs/gradient-check.json, which the widget
 * displays as the target it has to reproduce.
 */
import React, { useMemo, useState } from 'react';

import Chart from './chart/Chart';
import { useAutoplayOnView, useFrameLoop } from './useMotionClock';

/** foundations/03-backpropagation/runs/gradient-check.json */
const RECORDED = {
  a: 0.7,
  b: -0.5,
  c: 1.2,
  loss: 0.5334821284570855,
  da: 0.3576984093084489,
  db: 0.35054444112227984,
  dc: 0.5007777730318284,
};

const { a: A, b: B, c: C } = RECORDED;
const D = A * B;
const E = D + C;
const F = E * A;
const L = Math.tanh(F);

/** Local derivatives, in the reverse topological order `backward()` visits. */
const DF = 1 - Math.tanh(F) ** 2; // tanh'
const DE = DF * A; // f = e * a, so de = df * a
const A_FROM_F = DF * E; // ... and a's first contribution
const DD = DE; // e = d + c passes gradient straight through
const DC = DE;
const A_FROM_D = DD * B; // d = a * b, a's second contribution
const DB = DD * A;

type NodeId = 'a' | 'b' | 'c' | 'd' | 'e' | 'f' | 'L';

interface Step {
  /** The node whose `_backward` closure runs. */
  owner: NodeId | null;
  /** Gradient landing on each child, along the edge from `owner`. */
  pushes: { to: NodeId; value: number }[];
  caption: string;
}

const STEPS: Step[] = [
  {
    owner: null,
    pushes: [],
    caption: `The forward pass is done: d = a·b = ${D.toFixed(4)}, e = d + c = ${E.toFixed(
      4,
    )}, f = e·a = ${F.toFixed(4)}, L = tanh(f) = ${L.toFixed(
      4,
    )}. Every gradient is still zero, and every node remembers which operation produced it.`,
  },
  {
    owner: 'L',
    pushes: [{ to: 'f', value: DF }],
    caption: `Seed ∂L/∂L = 1 and run tanh's local rule, 1 − tanh²(f). One multiplication gives ∂L/∂f = ${DF.toFixed(
      4,
    )}. Nothing here knows anything about a, b or c.`,
  },
  {
    owner: 'f',
    pushes: [
      { to: 'e', value: DE },
      { to: 'a', value: A_FROM_F },
    ],
    caption: `f = e·a is a product, so each factor's share is the other factor's value times the gradient from above. e receives ${DE.toFixed(
      4,
    )}, and a receives its first contribution, ${A_FROM_F.toFixed(4)}.`,
  },
  {
    owner: 'e',
    pushes: [
      { to: 'd', value: DD },
      { to: 'c', value: DC },
    ],
    caption: `e = d + c is a sum, which passes gradient through untouched: d and c both receive ${DD.toFixed(
      4,
    )}. c is a leaf and consumed once, so ${DC.toFixed(4)} is its final answer.`,
  },
  {
    owner: 'd',
    pushes: [
      { to: 'a', value: A_FROM_D },
      { to: 'b', value: DB },
    ],
    caption: `d = a·b, another product. b receives ${DB.toFixed(
      4,
    )} and is finished. a receives ${A_FROM_D.toFixed(
      4,
    )} — its second contribution, arriving at a node that already holds one.`,
  },
];

const STEP_MS = 1500;

interface Box {
  id: NodeId;
  label: string;
  value: number;
  x: number;
  y: number;
  w: number;
  h: number;
}

const ROW_H = 74;
const BOX_H = 46;
/* A leaf carries three lines, not two: its gradient is the answer the chapter
   is after, and beside the value in a 88px box it overlapped it. */
const LEAF_H = 66;
const FIRST_OP_Y = 94;

/** Laid out from the measured width, so the same code fits a phone and a laptop. */
function layout(width: number) {
  const leafW = Math.max(70, Math.min(110, (width - 24) / 3));
  const leafGap = (width - leafW * 3) / 2;
  const opW = Math.min(190, Math.max(130, width * 0.52));
  const boxes: Box[] = [
    { id: 'a', label: 'a', value: A, x: 0, y: 0, w: leafW, h: LEAF_H },
    { id: 'b', label: 'b', value: B, x: leafW + leafGap, y: 0, w: leafW, h: LEAF_H },
    { id: 'c', label: 'c', value: C, x: (leafW + leafGap) * 2, y: 0, w: leafW, h: LEAF_H },
    { id: 'd', label: 'd = a·b', value: D, x: 26, y: FIRST_OP_Y, w: opW, h: BOX_H },
    { id: 'e', label: 'e = d + c', value: E, x: 26, y: FIRST_OP_Y + ROW_H, w: opW, h: BOX_H },
    { id: 'f', label: 'f = e·a', value: F, x: 26, y: FIRST_OP_Y + ROW_H * 2, w: opW, h: BOX_H },
    { id: 'L', label: 'L = tanh(f)', value: L, x: 26, y: FIRST_OP_Y + ROW_H * 3, w: opW, h: BOX_H },
  ];
  const at = Object.fromEntries(boxes.map((box) => [box.id, box])) as Record<NodeId, Box>;
  return { boxes, at };
}

const DIAGRAM_H = FIRST_OP_Y + ROW_H * 3 + BOX_H;

export default function GradientFlow(): React.ReactElement {
  const [accumulate, setAccumulate] = useState(true);
  const [step, setStep] = useState(0);
  const { ref, playing, setPlaying } = useAutoplayOnView<HTMLDivElement>();

  useFrameLoop(playing, (dt) => {
    setStep((current) => {
      const next = current + dt / STEP_MS;
      if (next >= STEPS.length) {
        setPlaying(false);
        return STEPS.length - 1;
      }
      return next;
    });
  });

  const index = Math.min(STEPS.length - 1, Math.floor(step));
  const current = STEPS[index];

  /* Replaying the pushes from the start is what makes the toggle honest: the
     gradients are produced by the rule the learner selected, not patched. */
  const grads = useMemo(() => {
    const totals: Partial<Record<NodeId, number>> = {};
    for (let i = 0; i <= index; i += 1) {
      for (const push of STEPS[i].pushes) {
        totals[push.to] = accumulate ? (totals[push.to] ?? 0) + push.value : push.value;
      }
    }
    return totals;
  }, [index, accumulate]);

  const done = index === STEPS.length - 1;
  const daNow = grads.a ?? 0;
  const wrong = done && Math.abs(daNow - RECORDED.da) > 1e-9;

  const ink = 'var(--rehearse-ink)';
  const rule = 'var(--rehearse-rule)';
  const action = 'var(--rehearse-action)';
  const caution = 'var(--rehearse-caution-strong)';

  return (
    <div className="learning-widget" ref={ref}>
      <p>
        The same graph, walked backward one operation at a time. Watch node <code>a</code>,
        which two different operations push into.
      </p>

      <div className="widget-controls">
        <button type="button" onClick={() => setPlaying((value) => !value)}>
          {playing ? 'Pause' : 'Play'}
        </button>
        <button
          type="button"
          onClick={() => {
            setPlaying(false);
            setStep((value) => (Math.floor(value) + 1) % STEPS.length);
          }}
        >
          Step
        </button>
        <button
          type="button"
          onClick={() => {
            setPlaying(false);
            setStep(0);
          }}
        >
          Restart
        </button>
        <span className="widget-controls__status">
          {index === 0 ? 'forward pass done' : `backward ${index} of ${STEPS.length - 1}`}
        </span>
      </div>

      <label style={{ userSelect: 'none' }}>
        <input
          type="checkbox"
          checked={!accumulate}
          onChange={(event) => setAccumulate(!event.target.checked)}
        />
        <span style={{ marginLeft: '0.5rem' }}>
          the bug: <code>=</code> instead of <code>+=</code>
        </span>
      </label>

      <Chart
        height={DIAGRAM_H + 16}
        padding={{ top: 8, right: 8, bottom: 8, left: 8 }}
        label="Computation graph for L = tanh(a squared b plus a c), walked backward from L to the leaves a, b and c"
      >
        {(frame) => {
          const { padding, innerWidth } = frame;
          const { boxes, at } = layout(innerWidth);
          const chipX = at.d.x + at.d.w + 10;

          /* An edge is live on the step whose owner sits at its head. */
          const live = (from: NodeId, to: NodeId) =>
            current.owner === from && current.pushes.some((push) => push.to === to);

          const edge = (from: NodeId, to: NodeId, d: string) => (
            <path
              key={`${from}-${to}`}
              d={d}
              fill="none"
              stroke={live(from, to) ? action : rule}
              strokeWidth={live(from, to) ? 3 : 1.5}
              markerEnd={live(from, to) ? 'url(#gf-head)' : undefined}
            />
          );

          const bottom = (id: NodeId) => at[id].y + at[id].h;
          const midX = (id: NodeId) => at[id].x + at[id].w / 2;

          return (
            <g transform={`translate(${padding.left},${padding.top})`}>
              <defs>
                <marker id="gf-head" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">
                  <path d="M0 0 L7 3.5 L0 7 z" fill={action} />
                </marker>
              </defs>

              {/* a and b into d, d and c into e, e into f, f into L */}
              {edge('d', 'a', `M${midX('a')} ${bottom('a')} L${midX('a')} ${at.d.y}`)}
              {edge('d', 'b', `M${midX('b')} ${bottom('b')} L${at.d.x + at.d.w - 24} ${at.d.y}`)}
              {edge('e', 'd', `M${midX('d')} ${bottom('d')} L${midX('d')} ${at.e.y}`)}
              {edge(
                'e',
                'c',
                `M${midX('c')} ${bottom('c')} L${midX('c')} ${at.e.y - 16} L${
                  at.e.x + at.e.w
                } ${at.e.y - 16} L${at.e.x + at.e.w - 24} ${at.e.y}`,
              )}
              {edge('f', 'e', `M${midX('e')} ${bottom('e')} L${midX('e')} ${at.f.y}`)}
              {edge('L', 'f', `M${midX('f')} ${bottom('f')} L${midX('f')} ${at.L.y}`)}
              {/* The second use of a: the long edge is the whole point of the graph. */}
              {edge(
                'f',
                'a',
                `M${at.a.x + 6} ${bottom('a')} L6 ${bottom('a') + 12} L6 ${at.f.y + BOX_H / 2} L${
                  at.f.x
                } ${at.f.y + BOX_H / 2}`,
              )}

              {boxes.map((box) => {
                const owned = current.owner === box.id;
                const receiving = current.pushes.some((push) => push.to === box.id);
                const grad = grads[box.id];
                const overwritten =
                  !accumulate && box.id === 'a' && index >= 4;
                return (
                  <g key={box.id}>
                    <rect
                      x={box.x}
                      y={box.y}
                      width={box.w}
                      height={box.h}
                      rx={4}
                      fill={owned || receiving ? action : rule}
                      opacity={owned ? 0.3 : receiving ? 0.2 : 0.1}
                      stroke={owned || receiving ? action : rule}
                      strokeWidth={owned || receiving ? 2 : 1}
                    />
                    <text x={box.x + 8} y={box.y + 19} fontSize={13} fill={ink}>
                      {box.label}
                    </text>
                    <text x={box.x + 8} y={box.y + 37} fontSize={13} fill="var(--rehearse-copy-muted)">
                      {box.value.toFixed(4)}
                    </text>
                    {grad !== undefined && (
                      <text
                        x={box.h === LEAF_H ? box.x + 8 : chipX}
                        y={box.h === LEAF_H ? box.y + 55 : box.y + 29}
                        fontSize={13}
                        fontWeight={600}
                        fill={overwritten ? caution : action}
                      >
                        {grad >= 0 ? '+' : '−'}
                        {Math.abs(grad).toFixed(4)}
                      </text>
                    )}
                  </g>
                );
              })}
            </g>
          );
        }}
      </Chart>

      <p className="widget-caption">{current.caption}</p>

      <div className="objective-readout">
        <div>
          <span>∂L/∂a</span>
          <strong style={{ color: wrong ? caution : undefined }}>{daNow.toFixed(10)}</strong>
        </div>
        <div>
          <span>∂L/∂b</span>
          <strong>{(grads.b ?? 0).toFixed(10)}</strong>
        </div>
        <div>
          <span>∂L/∂c</span>
          <strong>{(grads.c ?? 0).toFixed(10)}</strong>
        </div>
      </div>

      <p className="widget-caption">
        {!done
          ? `Recorded target: ∂L/∂a = ${RECORDED.da.toFixed(10)}, ∂L/∂b = ${RECORDED.db.toFixed(
              10,
            )}, ∂L/∂c = ${RECORDED.dc.toFixed(10)}.`
          : accumulate
            ? `All three match runs/gradient-check.json to every printed digit, which is what "exact agreement" in the results table means.`
            : `b and c are still exactly right, and only a is wrong: ${daNow.toFixed(
                4,
              )} against the recorded ${RECORDED.da.toFixed(
                4,
              )}. The sign flipped, so a gradient step would move a in the wrong direction — and nothing about the walk looks broken while it happens.`}
      </p>

      <p>
        Values recomputed in the browser from a = {A}, b = {B}, c = {C} and checked against{' '}
        <code>runs/gradient-check.json</code>, the CPU run this chapter records. The accumulate
        path reproduces its three gradients exactly; the assign path is the same walk with one
        operator changed, not a separately measured result.
      </p>
    </div>
  );
}
