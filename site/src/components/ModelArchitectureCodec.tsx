/**
 * The stage 01 video codec, drawn as the hourglass it actually is: a funnel
 * encoder collapsing one frame to a single latent vector, a 64-entry
 * codebook lookup at the narrowest point, and a mirrored funnel decoder
 * expanding back out.
 *
 * Every spatial size on the drawing is the real one from `CodecConfig` and
 * `Encoder`/`Decoder` in `01-video-tokenizer/core/video_codec.py`: three
 * stride-2 convolutions take a 32x32 frame to 16, 8, then 4, and a final
 * conv with no stride collapses that 4x4 grid to one 32-number vector. The
 * decoder is the exact mirror in `ConvTranspose2d`. A signal is animated
 * through encode, quantize, and decode in turn, so the reader sees the
 * bottleneck happen rather than infer it from a labeled box.
 *
 * The codebook-size control recomputes the embedding table's real parameter
 * count and bits-per-frame from `codebookSize * latentDim` and
 * `log2(codebookSize)` -- both exact for any size typed in. The measured
 * reconstruction numbers (0.0788 MSE, beating both baselines) belong only to
 * this codec's actual trained size, 64, and are labeled as such.
 *
 * Recorded in
 * 07-video-generation/01-video-tokenizer/runs/2026-07-31-codec-training.md.
 */
import React, { useCallback, useMemo, useRef, useState } from 'react';

import { useAutoplayOnView, useFrameLoop } from './useMotionClock';

const MEASURED = {
  height: 32,
  width: 32,
  channels: 3,
  hidden: 32,
  latentDim: 32,
  codebookSize: 64,
  codesUsed: 63,
  entropyRatio: 0.91,
  framesPerClip: 8,
  evalMseCodec: 0.0788,
  baselineBackground: 0.0944,
  baselineMeanFrame: 0.0858,
  shapePixelCodec: 1.194,
  shapePixelBaseline: 1.583,
};

const CODEBOOK_CHOICES = [
  { value: 16, label: '16' },
  { value: 64, label: '64 (this run)' },
  { value: 128, label: '128' },
  { value: 256, label: '256' },
];

type Phase = {
  id: string;
  ms: number;
  lit: string[];
  caption: string;
};

const PHASES: Phase[] = [
  {
    id: 'input',
    ms: 700,
    lit: ['input'],
    caption: 'One held-out clip frame enters the encoder: 32x32 pixels, 3 color channels.',
  },
  {
    id: 'enc1',
    ms: 750,
    lit: ['w-input-enc1', 'enc1'],
    caption:
      'First stride-2 Conv2d halves each spatial dimension, 32 -> 16, and expands to this codec’s hidden width of 32 channels.',
  },
  {
    id: 'enc2',
    ms: 750,
    lit: ['w-enc1-enc2', 'enc2'],
    caption: 'Second stride-2 Conv2d: 16 -> 8. Still no mixing across frames -- each frame is encoded independently.',
  },
  {
    id: 'enc3',
    ms: 750,
    lit: ['w-enc2-enc3', 'enc3'],
    caption: 'Third stride-2 Conv2d: 8 -> 4.',
  },
  {
    id: 'latent',
    ms: 800,
    lit: ['w-enc3-latent', 'latent'],
    caption:
      'A final conv with no stride collapses the remaining 4x4 grid to a single 32-number vector -- one continuous latent per frame.',
  },
  {
    id: 'quantize',
    ms: 950,
    lit: ['w-latent-codebook', 'codebook'],
    caption:
      'Vector quantization finds the nearest of the codebook’s entries by Euclidean distance. This run’s trained codebook holds 64 entries and actually uses 63 of them (codebook entropy ratio 0.91).',
  },
  {
    id: 'quant',
    ms: 700,
    lit: ['w-codebook-quant', 'quant'],
    caption: 'The frame is now one discrete token: a single integer between 0 and 63, snapped to that nearest entry.',
  },
  {
    id: 'dec1',
    ms: 750,
    lit: ['w-quant-dec1', 'dec1'],
    caption: 'The decoder mirrors the encoder exactly, in reverse: ConvTranspose2d 1 -> 4.',
  },
  {
    id: 'dec2',
    ms: 750,
    lit: ['w-dec1-dec2', 'dec2'],
    caption: 'ConvTranspose2d 4 -> 8.',
  },
  {
    id: 'dec3',
    ms: 750,
    lit: ['w-dec2-dec3', 'dec3'],
    caption: 'ConvTranspose2d 8 -> 16.',
  },
  {
    id: 'output',
    ms: 900,
    lit: ['w-dec3-output', 'output'],
    caption:
      'Final ConvTranspose2d, 16 -> 32: a full RGB frame again. This codec’s real reconstruction beats both baselines -- 0.0788 MSE against 0.0944 (background) and 0.0858 (mean-frame) -- though still a faint blur at this one-token-per-frame bit rate.',
  },
];

type Stage = {
  id: string;
  w: number;
  h: number;
  lines: string[];
};

/* The funnel narrows to show the collapse, but no box may narrow past its own
   label: at the old widths the two middle stages held 13px text in 40 units, so
   the labels were set at 11 and rendered at 10.8px. The tensor shapes on the
   second line carry the collapse anyway — the box width only illustrates it. */
const STAGES: Stage[] = [
  { id: 'input', w: 150, h: 44, lines: ['Frame', '32x32x3'] },
  { id: 'enc1', w: 132, h: 38, lines: ['Conv2d s2', '16x16x32'] },
  { id: 'enc2', w: 116, h: 36, lines: ['Conv2d s2', '8x8x32'] },
  { id: 'enc3', w: 100, h: 36, lines: ['Conv2d s2', '4x4x32'] },
  { id: 'latent', w: 84, h: 34, lines: ['z', '1x1x32'] },
  { id: 'quant', w: 84, h: 34, lines: ['z_q', '1x1x32'] },
  { id: 'dec1', w: 100, h: 36, lines: ['ConvT s2', '4x4x32'] },
  { id: 'dec2', w: 116, h: 36, lines: ['ConvT s2', '8x8x32'] },
  { id: 'dec3', w: 132, h: 38, lines: ['ConvT s2', '16x16x32'] },
  { id: 'output', w: 150, h: 44, lines: ['Reconstruction', '32x32x3'] },
];

const GAP = 30;
const CENTER_X = 130;

function layout() {
  const positions: Record<string, { x: number; y: number; w: number; h: number }> = {};
  let y = 14;
  for (const stage of STAGES) {
    positions[stage.id] = { x: CENTER_X - stage.w / 2, y, w: stage.w, h: stage.h };
    y += stage.h + GAP;
  }
  return { positions, totalHeight: y - GAP + 14 };
}

function embeddingParams(codebookSize: number) {
  return codebookSize * MEASURED.latentDim;
}

function bitsPerFrame(codebookSize: number) {
  return Math.log2(codebookSize);
}

export default function ModelArchitectureCodec(): React.ReactElement {
  const [codebookSize, setCodebookSize] = useState(MEASURED.codebookSize);
  const [phase, setPhase] = useState(0);
  const [progress, setProgress] = useState(0);
  const { ref: rootRef, playing, setPlaying } = useAutoplayOnView<HTMLDivElement>();

  const phaseRef = useRef(0);
  const progressRef = useRef(0);

  const isMeasured = codebookSize === MEASURED.codebookSize;
  const { positions, totalHeight } = useMemo(layout, []);

  const advance = useCallback(() => {
    const next = phaseRef.current + 1 >= PHASES.length ? 0 : phaseRef.current + 1;
    phaseRef.current = next;
    progressRef.current = 0;
    setPhase(next);
    setProgress(0);
  }, []);

  useFrameLoop(playing, (dt) => {
    const step = PHASES[phaseRef.current];
    const next = progressRef.current + dt / step.ms;
    if (next >= 1) {
      advance();
      return;
    }
    progressRef.current = next;
    setProgress(next);
  });

  const step = PHASES[phase];
  const lit = (id: string) => step.lit.includes(id);

  const ink = 'var(--rehearse-ink)';
  const action = 'var(--rehearse-action)';
  const rule = 'var(--rehearse-rule)';

  const wire = (id: string, fromId: string, toId: string) => {
    const from = positions[fromId];
    const to = positions[toId];
    const x1 = from.x + from.w / 2;
    const y1 = from.y + from.h;
    const x2 = to.x + to.w / 2;
    const y2 = to.y;
    return (
      <line
        key={id}
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={lit(id) ? action : rule}
        strokeWidth={lit(id) ? 2.5 : 1.5}
      />
    );
  };

  const box = (stage: Stage) => {
    const p = positions[stage.id];
    const on = lit(stage.id);
    return (
      <g key={stage.id}>
        <rect
          x={p.x}
          y={p.y}
          width={p.w}
          height={p.h}
          rx={4}
          fill={action}
          opacity={on ? 0.34 : 0.12}
          stroke={on ? action : ink}
          strokeWidth={on ? 2 : 1}
        />
        <text x={p.x + p.w / 2} y={p.y + p.h / 2 - 4} textAnchor="middle" fontSize="14" fill={ink}>
          {stage.lines[0]}
        </text>
        <text
          x={p.x + p.w / 2}
          y={p.y + p.h / 2 + 14}
          textAnchor="middle"
          fontSize="14"
          fill={ink}
          fontWeight={600}
        >
          {stage.lines[1]}
        </text>
      </g>
    );
  };

  const codebookX = CENTER_X + 130;
  const codebookY = positions.latent.y - 34;
  const codebookSide = 8;
  const cellGap = 2;
  const cellSize = 10;
  const codebookBoxW = codebookSide * (cellSize + cellGap) + 16;
  /* The caption sits above the box, not inside it: inside, it overlapped the
     first row of cells and ran past the right edge of the drawing. */
  const codebookBoxH = codebookSide * (cellSize + cellGap) + 20;
  const nearestIndex = 41; // fixed illustrative index within the 8x8 grid

  return (
    <div className="learning-widget" ref={rootRef}>
      <p>
        Stage 01&rsquo;s codec turns one frame into one discrete token and back: a funnel
        encoder collapses 32x32 pixels to a single 32-number vector, a codebook lookup snaps
        that vector to the nearest of 64 learned entries, and a mirrored funnel decoder
        expands the result back to a full frame.
      </p>

      <div className="widget-controls">
        <button type="button" onClick={() => setPlaying((value) => !value)}>
          {playing ? 'Pause' : 'Play'}
        </button>
        <button
          type="button"
          onClick={() => {
            setPlaying(false);
            advance();
          }}
        >
          Step
        </button>
        <span className="widget-controls__status">
          {phase + 1} of {PHASES.length}
        </span>
      </div>

      <svg
        viewBox={`0 0 ${codebookX + codebookBoxW / 2 + 14} ${totalHeight}`}
        width="100%"
        style={{ display: 'block', maxWidth: '24rem', margin: '0 auto' }}
        role="img"
        aria-label="Video codec: a funnel encoder into a 64-entry codebook lookup, then a mirrored funnel decoder"
      >
        {wire('w-input-enc1', 'input', 'enc1')}
        {wire('w-enc1-enc2', 'enc1', 'enc2')}
        {wire('w-enc2-enc3', 'enc2', 'enc3')}
        {wire('w-enc3-latent', 'enc3', 'latent')}
        {wire('w-quant-dec1', 'quant', 'dec1')}
        {wire('w-dec1-dec2', 'dec1', 'dec2')}
        {wire('w-dec2-dec3', 'dec2', 'dec3')}
        {wire('w-dec3-output', 'dec3', 'output')}

        {/* side excursion into the codebook, between latent and quant */}
        <line
          x1={positions.latent.x + positions.latent.w}
          y1={positions.latent.y + positions.latent.h / 2}
          x2={codebookX - codebookBoxW / 2}
          y2={codebookY + codebookBoxH / 2}
          stroke={lit('w-latent-codebook') ? action : rule}
          strokeWidth={lit('w-latent-codebook') ? 2.5 : 1.5}
        />
        <line
          x1={codebookX - codebookBoxW / 2}
          y1={codebookY + codebookBoxH / 2 + 16}
          x2={positions.quant.x + positions.quant.w}
          y2={positions.quant.y + positions.quant.h / 2}
          stroke={lit('w-codebook-quant') ? action : rule}
          strokeWidth={lit('w-codebook-quant') ? 2.5 : 1.5}
        />

        {STAGES.map(box)}

        {/* codebook: a real 8x8 grid standing in for the 64 learned entries */}
        <g>
          <rect
            x={codebookX - codebookBoxW / 2}
            y={codebookY}
            width={codebookBoxW}
            height={codebookBoxH}
            rx={4}
            fill={action}
            opacity={lit('codebook') ? 0.22 : 0.08}
            stroke={lit('codebook') ? action : ink}
            strokeWidth={lit('codebook') ? 2 : 1}
          />
          <text
            x={codebookX + codebookBoxW / 2}
            y={codebookY - 8}
            textAnchor="end"
            fontSize="14"
            fill={ink}
            fontWeight={600}
          >
            Codebook, {MEASURED.codebookSize} entries
          </text>
          {Array.from({ length: codebookSide * codebookSide }).map((_, i) => {
            const row = Math.floor(i / codebookSide);
            const col = i % codebookSide;
            const cx = codebookX - codebookBoxW / 2 + 8 + col * (cellSize + cellGap);
            const cy = codebookY + 10 + row * (cellSize + cellGap);
            const isNearest = i === nearestIndex && lit('codebook');
            return (
              <rect
                key={i}
                x={cx}
                y={cy}
                width={cellSize}
                height={cellSize}
                fill={isNearest ? action : 'none'}
                opacity={isNearest ? 0.9 : 1}
                stroke={isNearest ? action : rule}
                strokeWidth={isNearest ? 2 : 1}
              />
            );
          })}
        </g>
      </svg>

      <div className="widget-caption widget-swap" aria-live="polite">
        {PHASES.map((phaseStep, index) => (
          <p key={phaseStep.id} data-shown={index === phase} aria-hidden={index !== phase}>
            {phaseStep.caption}
          </p>
        ))}
      </div>

      <label>
        Codebook size
        <select
          aria-label="Codebook size"
          value={codebookSize}
          onChange={(event) => setCodebookSize(Number(event.target.value))}
        >
          {CODEBOOK_CHOICES.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>
      </label>

      <p>
        Embedding table: <strong>{embeddingParams(codebookSize).toLocaleString()}</strong> parameters
        (<code>codebook_size x latent_dim</code>, {codebookSize} x {MEASURED.latentDim}). Each frame
        becomes <strong>{bitsPerFrame(codebookSize).toFixed(2)} bits</strong>, so this mission&rsquo;s
        {' '}
        {MEASURED.framesPerClip}-frame clips would need{' '}
        {(bitsPerFrame(codebookSize) * MEASURED.framesPerClip).toFixed(1)} bits total to name which
        codes were used.
      </p>

      <p>
        {isMeasured ? (
          <>
            This is the codebook size that actually trained:{' '}
            <strong>{MEASURED.codesUsed} of {MEASURED.codebookSize}</strong> entries used, codebook
            entropy ratio <strong>{MEASURED.entropyRatio}</strong>.
          </>
        ) : (
          <>
            Hypothetical -- this codec was never retrained at {codebookSize} entries, so there is no
            measured usage count or reconstruction number at this size, only the embedding-table
            arithmetic above.
          </>
        )}
      </p>

      <div className="budget-axis">
        {[
          { name: 'Background baseline', value: MEASURED.baselineBackground, best: false },
          { name: 'Mean-frame baseline', value: MEASURED.baselineMeanFrame, best: false },
          { name: 'This codec (measured)', value: MEASURED.evalMseCodec, best: true },
        ].map((row) => {
          const maxValue = MEASURED.baselineBackground;
          const width = (row.value / maxValue) * 100;
          return (
            <div className="budget-axis__row" key={row.name}>
              <span className="budget-axis__name">
                <strong>{row.name}</strong>
              </span>
              <span className="budget-axis__track">
                <span
                  className="budget-axis__band"
                  data-best={row.best}
                  style={{ left: '0%', width: `${width}%` }}
                />
                <span className="budget-axis__mean" data-best={row.best} style={{ left: `${width}%` }} />
              </span>
              <span className="budget-axis__value">{row.value.toFixed(4)}</span>
            </div>
          );
        })}
        <p className="budget-axis__scale">
          Held-out reconstruction MSE, lower is better. On shape pixels specifically (excluding the
          94% of every frame that is plain background), the gap is real signal, not background
          matching: {MEASURED.shapePixelCodec} vs {MEASURED.shapePixelBaseline}, 24.6% better.
        </p>
      </div>
    </div>
  );
}
