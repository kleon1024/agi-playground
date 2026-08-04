/**
 * What one `nn.Linear` actually does under weight-only INT8, drawn beside what
 * it did before.
 *
 * The chapter's result is counterintuitive enough that a table of tok/s invites
 * the reader to assume a measurement error: the model is 2.79x smaller and it
 * decodes slower. The reason is structural and it is a picture -- the int8 lane
 * is one stage longer, and the stage it adds rebuilds the full-width fp32
 * tensor the smaller weights were supposed to avoid. Seeing the two columns
 * side by side, with the taller one being the smaller model, is the whole
 * argument.
 *
 * Every byte count and rate is measured, from this chapter's own bench and
 * profile output. The regime selector changes which measured pair the readout
 * reports; it does not change the mechanism, which is the point.
 */
import React, { useState } from 'react';

import Chart from './chart/Chart';

const MEASURED = {
  /** Attention and SwiGLU Linear weights only; the tied embedding stays fp32. */
  layerBytesFp32: 301_989_888,
  layerBytesInt8: 75_829_248,
  wholeFp32: 352_791_552,
  wholeInt8: 126_554_112,
  eager: { fp32: 129.1, int8: 97.8, cudaMsFp32: 1.312, cudaMsInt8: 1.771 },
  graph: { fp32: 373.8, int8: 322.8 },
};

type Regime = 'eager' | 'graph';

const HEIGHT = 336;
const PADDING = { top: 26, right: 8, bottom: 16, left: 8 };
const BOX_H = 44;
const GAP = 14;

interface Stage {
  lines: [string, string?];
  /** The stage the int8 path pays for and the fp32 path does not. */
  added?: boolean;
}

const FP32_LANE: Stage[] = [
  { lines: ['fp32 weights', '302.0 MB'] },
  { lines: ['F.linear'] },
  { lines: ['activations out'] },
];

const INT8_LANE: Stage[] = [
  { lines: ['int8 weights', '75.8 MB'] },
  { lines: ['dequantize', 'w.float() * scale'], added: true },
  { lines: ['fp32 weights', '302.0 MB, rebuilt'], added: true },
  { lines: ['F.linear'] },
  { lines: ['activations out'] },
];

const mb = (bytes: number) => `${(bytes / 1_000_000).toFixed(1)} MB`;

export default function QuantizedDecodePath(): React.ReactElement {
  const [regime, setRegime] = useState<Regime>('eager');
  const rates = regime === 'eager' ? MEASURED.eager : MEASURED.graph;
  const ratio = rates.int8 / rates.fp32;

  return (
    <div className="learning-widget">
      <p>
        Both columns are the same layer, one weight format apart. Read them
        top to bottom: the shorter column is the larger model.
      </p>

      <Chart
        height={HEIGHT}
        padding={PADDING}
        label={
          'Two data paths through one Linear layer. The fp32 path reads 302.0 MB of weights and '
          + 'calls F.linear. The int8 path reads 75.8 MB, rebuilds the same 302.0 MB as fp32, and '
          + 'then calls F.linear.'
        }
      >
        {(frame) => {
          const { padding, innerWidth } = frame;
          const colW = Math.min(190, (innerWidth - 16) / 2);
          const colX = [0, innerWidth - colW];

          const lane = (stages: Stage[], col: 0 | 1, heading: string) => (
            <g key={heading}>
              <text
                x={colX[col] + colW / 2}
                y={-8}
                textAnchor="middle"
                fill="var(--rehearse-ink)"
                fontSize={14}
                fontWeight={700}
              >
                {heading}
              </text>
              {stages.map((stage, i) => {
                const y = i * (BOX_H + GAP);
                return (
                  <g key={stage.lines[0]}>
                    {i > 0 && (
                      <line
                        x1={colX[col] + colW / 2}
                        y1={y - GAP}
                        x2={colX[col] + colW / 2}
                        y2={y - 3}
                        stroke="var(--rehearse-ink)"
                        strokeWidth={1.5}
                        markerEnd="url(#quant-arrow)"
                      />
                    )}
                    <rect
                      x={colX[col]}
                      y={y}
                      width={colW}
                      height={BOX_H}
                      rx={4}
                      fill={stage.added ? 'var(--rehearse-caution-soft)' : 'var(--rehearse-warm-white)'}
                      stroke={stage.added ? 'var(--rehearse-caution)' : 'var(--rehearse-ink)'}
                    />
                    <text
                      x={colX[col] + colW / 2}
                      y={y + (stage.lines[1] ? 19 : 27)}
                      textAnchor="middle"
                      fill="var(--rehearse-ink)"
                      fontSize={14}
                      fontWeight={600}
                    >
                      {stage.lines[0]}
                    </text>
                    {stage.lines[1] && (
                      <text
                        x={colX[col] + colW / 2}
                        y={y + 36}
                        textAnchor="middle"
                        fill="var(--rehearse-copy-muted)"
                        fontSize={13}
                      >
                        {stage.lines[1]}
                      </text>
                    )}
                  </g>
                );
              })}
            </g>
          );

          return (
            <g transform={`translate(${padding.left},${padding.top})`}>
              <defs>
                <marker
                  id="quant-arrow"
                  viewBox="0 0 8 8"
                  refX={7}
                  refY={4}
                  markerWidth={6}
                  markerHeight={6}
                  orient="auto"
                >
                  <path d="M0,0 L8,4 L0,8 z" fill="var(--rehearse-ink)" />
                </marker>
              </defs>
              {lane(FP32_LANE, 0, 'fp32')}
              {lane(INT8_LANE, 1, 'int8 weight-only')}
            </g>
          );
        }}
      </Chart>

      <p className="objective-note">
        The two amber stages are what INT8 adds. Neither exists in the fp32 path,
        and the second one materializes exactly the tensor the smaller weights
        were meant to avoid.
      </p>

      <div className="widget-controls" role="group" aria-label="Which execution regime to report">
        <button type="button" aria-pressed={regime === 'eager'} onClick={() => setRegime('eager')}>
          Eager
        </button>
        <button type="button" aria-pressed={regime === 'graph'} onClick={() => setRegime('graph')}>
          CUDA graph
        </button>
      </div>

      <div className="objective-readout">
        <div>
          <span>Weights on the card</span>
          <strong>{mb(MEASURED.layerBytesInt8)}</strong>
        </div>
        <div>
          <span>fp32 decode, {regime === 'eager' ? 'eager' : 'graph replay'}</span>
          <strong>{rates.fp32.toFixed(1)} tok/s</strong>
        </div>
        <div>
          <span>int8 decode, same regime</span>
          <strong>{rates.int8.toFixed(1)} tok/s</strong>
        </div>
      </div>

      <p className="widget-caption">
        {regime === 'eager' ? (
          <>
            Eager: <strong>{ratio.toFixed(2)}x</strong> the fp32 rate. The profile says where it
            went — device time per step rose from {MEASURED.eager.cudaMsFp32.toFixed(3)} ms to{' '}
            {MEASURED.eager.cudaMsInt8.toFixed(3)} ms, up 35%, because the dequant kernel runs in
            addition to the matmul rather than instead of anything.
          </>
        ) : (
          <>
            Under CUDA-graph replay: <strong>{ratio.toFixed(2)}x</strong> the fp32 rate. Capturing
            the graph removes launch overhead from both paths and lifts both by about 2.9x, but the
            gap between them survives, because the extra work is arithmetic the replay still has to
            perform.
          </>
        )}
      </p>

      <p>
        The model is {(MEASURED.wholeFp32 / MEASURED.wholeInt8).toFixed(2)}x smaller whole and{' '}
        {(MEASURED.layerBytesFp32 / MEASURED.layerBytesInt8).toFixed(2)}x smaller across the layers
        that were quantized, and it is slower in both regimes. Fewer bytes only buys speed when
        moving bytes is what the step is waiting on — and at batch 1 on this model, it is not.
      </p>
    </div>
  );
}
