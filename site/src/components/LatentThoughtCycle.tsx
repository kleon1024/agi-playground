/**
 * The generation cycle, and the two links a continuous thought removes.
 *
 * The chapter's mechanism is a single edit -- `embeds[:, slot] = hidden[:, slot - 1]`
 * -- and its consequence is entirely about which links that edit skips. Written
 * as prose, "it does hidden to embedding directly" is four words the reader has
 * to hold against a cycle they are also holding. Drawn, the shortcut is the
 * diagram: two boxes go dark and the state that arrives at the next step stops
 * being a token.
 *
 * Sizes come from the model that actually ran (`core/model.py` at d_model 128,
 * `core/task.py` at 51 tokens), and the accuracies from
 * `runs/2026-07-30-arm-comparison-reduced.json`. Both arms landed at chance,
 * and the readout says so rather than letting the drawing imply the shortcut
 * won something.
 */
import React, { useState } from 'react';

import Chart from './chart/Chart';

const MEASURED = {
  dModel: 128,
  vocab: 51,
  /** Reduced-budget run, 3 seeds. A balanced yes/no task, so 0.50 is the floor. */
  cotAccuracy: 0.5013,
  latentAccuracy: 0.5007,
  chance: 0.5,
};

type Arm = 'written' | 'continuous';

const HEIGHT = 250;
const PADDING = { top: 18, right: 8, bottom: 30, left: 8 };
const NODE_H = 62;

interface NodeSpec {
  id: 'hidden' | 'logits' | 'token' | 'embedding';
  lines: [string, string];
  /** Column and row in the 2x2 cycle. */
  col: 0 | 1;
  row: 0 | 1;
}

const NODES: NodeSpec[] = [
  { id: 'hidden', lines: ['Hidden state', `${MEASURED.dModel} numbers`], col: 0, row: 0 },
  { id: 'logits', lines: ['Logits', `over ${MEASURED.vocab} tokens`], col: 1, row: 0 },
  { id: 'token', lines: ['One token', `1 of ${MEASURED.vocab}`], col: 1, row: 1 },
  { id: 'embedding', lines: ['Next input', `${MEASURED.dModel} numbers`], col: 0, row: 1 },
];

/** Links the continuous arm does not traverse. */
const CUT = new Set(['hidden-logits', 'logits-token', 'token-embedding']);

export default function LatentThoughtCycle(): React.ReactElement {
  const [arm, setArm] = useState<Arm>('written');
  const continuous = arm === 'continuous';

  return (
    <div className="learning-widget">
      <p>
        One step of generation is a cycle with four links. A continuous thought
        replaces three of them with one assignment. Switch the arm and watch which
        boxes the state still has to pass through.
      </p>

      <div className="widget-controls" role="group" aria-label="Which arm to draw">
        <button type="button" aria-pressed={!continuous} onClick={() => setArm('written')}>
          Written thought
        </button>
        <button type="button" aria-pressed={continuous} onClick={() => setArm('continuous')}>
          Continuous thought
        </button>
      </div>

      <Chart
        height={HEIGHT}
        padding={PADDING}
        label={
          continuous
            ? `The generation cycle with the logits and token steps removed: the hidden state, ${MEASURED.dModel} numbers, is written straight into the next input slot.`
            : `The generation cycle: hidden state to logits over ${MEASURED.vocab} tokens, to one sampled token, to the next input embedding.`
        }
      >
        {(frame) => {
          const { padding, innerWidth, innerHeight } = frame;
          const nodeW = Math.min(160, (innerWidth - 26) / 2);
          const colX = [0, innerWidth - nodeW];
          const rowY = [0, innerHeight - NODE_H];
          const centre = (n: NodeSpec) => ({
            x: colX[n.col] + nodeW / 2,
            y: rowY[n.row] + NODE_H / 2,
          });
          const byId = Object.fromEntries(NODES.map((n) => [n.id, n])) as Record<string, NodeSpec>;
          const dim = (id: string) => continuous && (id === 'logits' || id === 'token');

          /* In the continuous arm two arrows share the left column, running in
             opposite directions. Drawn on the same axis they read as one
             confused line, so the forward pass steps aside for the assignment. */
          const LANE = 20;
          const edge = (fromId: string, toId: string, shift = 0) => {
            const a = centre(byId[fromId]);
            const b = centre(byId[toId]);
            const cut = continuous && CUT.has(`${fromId}-${toId}`);
            const horizontal = a.y === b.y;
            const x1 = horizontal ? a.x + nodeW / 2 : a.x + shift;
            const x2 = horizontal ? b.x - nodeW / 2 : b.x + shift;
            const y1 = horizontal ? a.y : a.y + (b.y > a.y ? NODE_H / 2 : -NODE_H / 2);
            const y2 = horizontal ? b.y : b.y + (b.y > a.y ? -NODE_H / 2 : NODE_H / 2);
            return (
              <line
                key={`${fromId}-${toId}`}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={cut ? 'var(--rehearse-rule)' : 'var(--rehearse-action)'}
                strokeWidth={cut ? 1.5 : 2.5}
                strokeDasharray={cut ? '4 4' : undefined}
                markerEnd={cut ? undefined : 'url(#latent-arrow)'}
              />
            );
          };

          const hidden = centre(byId.hidden);
          const embedding = centre(byId.embedding);

          return (
            <g transform={`translate(${padding.left},${padding.top})`}>
              <defs>
                <marker
                  id="latent-arrow"
                  viewBox="0 0 8 8"
                  refX={7}
                  refY={4}
                  markerWidth={7}
                  markerHeight={7}
                  orient="auto"
                >
                  <path d="M0,0 L8,4 L0,8 z" fill="var(--rehearse-action)" />
                </marker>
                <marker
                  id="latent-assign"
                  viewBox="0 0 8 8"
                  refX={7}
                  refY={4}
                  markerWidth={7}
                  markerHeight={7}
                  orient="auto"
                >
                  <path d="M0,0 L8,4 L0,8 z" fill="var(--rehearse-emphasis)" />
                </marker>
              </defs>

              {edge('hidden', 'logits')}
              {edge('logits', 'token')}
              {edge('token', 'embedding')}
              {edge('embedding', 'hidden', continuous ? -LANE : 0)}

              {/* The shortcut: one assignment, down its own lane in the same column. */}
              {continuous && (
                <>
                  <line
                    x1={hidden.x + LANE}
                    y1={hidden.y + NODE_H / 2}
                    x2={embedding.x + LANE}
                    y2={embedding.y - NODE_H / 2}
                    stroke="var(--rehearse-emphasis)"
                    strokeWidth={2.5}
                    markerEnd="url(#latent-assign)"
                  />
                  <text
                    x={hidden.x + LANE + 8}
                    y={(hidden.y + embedding.y) / 2 + 4}
                    fill="var(--rehearse-emphasis)"
                    fontSize={13}
                    fontWeight={600}
                  >
                    assigned
                  </text>
                </>
              )}

              {NODES.map((node) => (
                <g key={node.id} opacity={dim(node.id) ? 0.32 : 1}>
                  <rect
                    x={colX[node.col]}
                    y={rowY[node.row]}
                    width={nodeW}
                    height={NODE_H}
                    rx={4}
                    fill={dim(node.id) ? 'var(--rehearse-paper)' : 'var(--rehearse-warm-white)'}
                    stroke={dim(node.id) ? 'var(--rehearse-rule)' : 'var(--rehearse-ink)'}
                    strokeDasharray={dim(node.id) ? '4 4' : undefined}
                  />
                  <text
                    x={colX[node.col] + nodeW / 2}
                    y={rowY[node.row] + 26}
                    textAnchor="middle"
                    fill="var(--rehearse-ink)"
                    fontSize={14}
                    fontWeight={600}
                  >
                    {node.lines[0]}
                  </text>
                  <text
                    x={colX[node.col] + nodeW / 2}
                    y={rowY[node.row] + 45}
                    textAnchor="middle"
                    fill="var(--rehearse-copy-muted)"
                    fontSize={13}
                  >
                    {node.lines[1]}
                  </text>
                </g>
              ))}
            </g>
          );
        }}
      </Chart>

      <div className="objective-readout">
        <div>
          <span>Links per generated step</span>
          <strong>{continuous ? 2 : 4}</strong>
        </div>
        <div>
          <span>What reaches the next step</span>
          <strong>{continuous ? `${MEASURED.dModel} numbers` : `1 of ${MEASURED.vocab}`}</strong>
        </div>
        <div>
          <span>Measured accuracy, 3 seeds</span>
          <strong>
            {(continuous ? MEASURED.latentAccuracy : MEASURED.cotAccuracy).toFixed(4)}
          </strong>
        </div>
      </div>

      <p className="widget-caption">
        {continuous ? (
          <>
            The hidden state is written straight into the next input slot, so nothing
            is sampled and nothing is discarded. It is also{' '}
            <strong>{MEASURED.latentAccuracy.toFixed(4)}</strong> accurate on this task
            against a chance floor of {MEASURED.chance.toFixed(2)} — the mechanism runs,
            and at this scale it buys nothing measurable.
          </>
        ) : (
          <>
            Sampling collapses {MEASURED.dModel} continuous numbers into one choice out of{' '}
            {MEASURED.vocab}. Everything the model was weighing and did not pick is gone
            before the next step begins. This arm scored{' '}
            <strong>{MEASURED.cotAccuracy.toFixed(4)}</strong>, also at chance.
          </>
        )}
      </p>

      <p>
        Both arms sit on the floor, so this drawing is a picture of a mechanism, not
        of a win. It shows what the edit changes about the cycle — and the honest
        reading of the numbers beside it is that a 1.2M-parameter model on this task
        cannot tell you whether removing the collapse helps.
      </p>
    </div>
  );
}
