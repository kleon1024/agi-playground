/**
 * Mission 05 stage 01's fused vision+text decoder, drawn and animated.
 *
 * The one thing this diagram exists to correct: there is no separate
 * cross-attention module anywhere in `vlm_model.py`. A 32x32 image becomes 64
 * patch tokens (`VisionPatchEmbed`), those tokens are concatenated in front of
 * the text tokens into one sequence, and a single shared `FusedAttention`
 * block reads the whole thing -- vision positions attend to each other
 * bidirectionally, every text position sees the entire image, and text still
 * attends to itself causally (`build_mask`, `vlm_model.py:178-202`). The inset
 * mask diagram is that function's actual four quadrants, not an illustration
 * of a generic prefix-LM.
 *
 * Every number is computed from `Config(d_model=128, n_layer=4, n_head=4,
 * n_kv_head=2, d_ff=336)` and `vocab_size=36` rather than typed in, and the
 * toggle changes exactly the one variable mission 05's own ablation isolates
 * (`use_vision`): the vision lane and its 14,464 extra parameters (a 48x128
 * patch projection plus a 64x128 position table) either exist or do not.
 * Measured totals -- 732,928 (vision) and 718,464 (text-only) -- are recorded
 * in `runs/2026-07-31-vision-vs-text-only.md`.
 *
 * Colours come from the shared theme variables, matching `ModelArchitecture.tsx`.
 */
import React, { useCallback, useMemo, useRef, useState } from 'react';

import { useAutoplayOnView, useFrameLoop } from './useMotionClock';

const MEASURED = {
  vocabSize: 36,
  dModel: 128,
  layers: 4,
  heads: 4,
  kvHeads: 2,
  dFf: 336,
  numVisionTokens: 64,
  patchesPerSide: 8,
  patchDim: 48, // 4x4 patch, 3 channels
  totalParamsVision: 732_928,
  totalParamsTextOnly: 718_464,
};

const BLOCK_PHASES = [
  {
    id: 'norm-a',
    from: 90,
    to: 90,
    ms: 800,
    lit: ['norm-a', 'branch-a'],
    caption: 'RMSNorm rescales a copy of the concatenated sequence. The stream itself is untouched.',
  },
  {
    id: 'attend',
    from: 90,
    to: 90,
    ms: 1000,
    lit: ['attn', 'mask'],
    caption:
      'One shared attention reads the whole sequence. The mask (inset) is the only thing that makes it a vision prefix: vision sees vision, text sees everything, vision never sees text.',
  },
  {
    id: 'add-a',
    from: 90,
    to: 200,
    ms: 800,
    lit: ['return-a', 'add-a'],
    caption: 'Its output is added back into the stream at every position, vision and text alike.',
  },
  {
    id: 'carry',
    from: 200,
    to: 216,
    ms: 700,
    lit: [] as string[],
    caption: 'The stream carries forward, still 128 wide at every one of its positions.',
  },
  {
    id: 'norm-b',
    from: 216,
    to: 216,
    ms: 800,
    lit: ['norm-b', 'branch-b'],
    caption: 'A second RMSNorm prepares a copy for the position-wise half.',
  },
  {
    id: 'mlp',
    from: 216,
    to: 216,
    ms: 1000,
    lit: ['mlp'],
    caption: 'SwiGLU transforms each position independently -- no mixing between vision and text here.',
  },
  {
    id: 'add-b',
    from: 216,
    to: 312,
    ms: 800,
    lit: ['return-b', 'add-b'],
    caption: 'Added back again. One block, four times: nothing here changes between layers.',
  },
];

const VISION_ENTRY_PHASES = [
  {
    id: 'vision-in',
    from: 44,
    to: 90,
    ms: 750,
    lit: ['vision-embed', 'wire-vision'],
    caption: '64 patch tokens (8x8 grid, 4x4 pixels each) are projected to 128-d and enter the sequence first.',
  },
  {
    id: 'concat',
    from: 44,
    to: 90,
    ms: 750,
    lit: ['text-embed', 'wire-text', 'concat-point'],
    caption:
      'Text tokens, projected the same 128-d way, are concatenated right after -- one sequence, not two encoders.',
  },
];

const TEXT_ONLY_ENTRY_PHASES = [
  {
    id: 'text-in-only',
    from: 44,
    to: 90,
    ms: 800,
    lit: ['text-embed', 'wire-text-only'],
    caption: 'use_vision=False: no vision lane exists at all. Only text tokens enter the sequence.',
  },
];

function budget(useVision: boolean) {
  const { dModel, layers, dFf, heads, kvHeads, vocabSize, numVisionTokens, patchDim } = MEASURED;
  const dHead = dModel / heads;
  const embedding = vocabSize * dModel; // tied with the output head
  const attention = dModel * dModel + 2 * (dModel * kvHeads * dHead) + dModel * dModel;
  const swiglu = 3 * dModel * dFf; // gate, up, down
  const norms = 2 * dModel; // two RMSNorm gains per block
  const perLayer = attention + swiglu + norms;
  const layersTotal = layers * perLayer;
  const finalNorm = dModel;
  const patchProj = patchDim * dModel + dModel; // weight + bias
  const patchPos = numVisionTokens * dModel;
  const visionExtra = useVision ? patchProj + patchPos : 0;
  const total = embedding + layersTotal + finalNorm + visionExtra;
  return { embedding, attention, swiglu, perLayer, layersTotal, finalNorm, patchProj, patchPos, visionExtra, total, dHead };
}

function MaskDiagram({ lit }: { lit: boolean }) {
  const open = 'var(--rehearse-action)';
  const blocked = 'var(--rehearse-rule)';
  const ink = 'var(--rehearse-ink)';
  return (
    <svg
      viewBox="0 0 72 80"
      width="86"
      height="96"
      role="img"
      aria-label="Attention mask: vision queries attend only to vision keys; text queries attend to all vision keys and to earlier text keys; vision queries never attend to text keys"
    >
      <text x="36" y="10" textAnchor="middle" fontSize="7" fill={ink}>
        key: V | T
      </text>
      <g transform="translate(4,14)">
        <rect x="0" y="0" width="28" height="28" fill={open} opacity={lit ? 0.6 : 0.3} />
        <rect x="28" y="0" width="28" height="28" fill={blocked} opacity={lit ? 0.45 : 0.2} />
        <rect x="0" y="28" width="28" height="28" fill={open} opacity={lit ? 0.6 : 0.3} />
        <rect x="28" y="28" width="28" height="28" fill={blocked} opacity={lit ? 0.25 : 0.12} />
        <polygon
          points="28,28 56,28 56,56"
          fill={open}
          opacity={lit ? 0.6 : 0.3}
        />
        <line x1="28" y1="0" x2="28" y2="56" stroke={ink} strokeWidth="0.6" />
        <line x1="0" y1="28" x2="56" y2="28" stroke={ink} strokeWidth="0.6" />
        <line x1="28" y1="28" x2="56" y2="56" stroke={ink} strokeWidth="0.5" strokeDasharray="1.5,1" />
        <text x="14" y="17" textAnchor="middle" fontSize="6" fill={ink}>V</text>
        <text x="14" y="45" textAnchor="middle" fontSize="6" fill={ink}>V</text>
        <text x="42" y="45" textAnchor="middle" fontSize="6" fill={ink}>T</text>
      </g>
      <text x="8" y="78" textAnchor="middle" fontSize="7" fill={ink} transform="rotate(-90 8 60)">
        query
      </text>
    </svg>
  );
}

type PhaseStep = (typeof BLOCK_PHASES)[number];

export default function ModelArchitectureVLM(): React.ReactElement {
  const [useVision, setUseVision] = useState(true);
  const [frameIndex, setFrameIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const { ref: rootRef, playing, setPlaying } = useAutoplayOnView<HTMLDivElement>();

  const frameRef = useRef(0);
  const progressRef = useRef(0);

  // The vision/text merge happens once, before layer 1; the same attention
  // + SwiGLU block then repeats for all 4 layers before the whole thing loops.
  const frames = useMemo(() => {
    const entry = useVision ? VISION_ENTRY_PHASES : TEXT_ONLY_ENTRY_PHASES;
    const out: { step: PhaseStep; layer: number }[] = entry.map((step) => ({ step, layer: 1 }));
    for (let l = 1; l <= MEASURED.layers; l += 1) {
      BLOCK_PHASES.forEach((step) => out.push({ step, layer: l }));
    }
    return out;
  }, [useVision]);

  // One caption per distinct step id (not per repeated layer iteration), so the
  // widget-swap box is sized once and "shown" is matched by id, not frame index.
  const captionSteps = useMemo(
    () => [...(useVision ? VISION_ENTRY_PHASES : TEXT_ONLY_ENTRY_PHASES), ...BLOCK_PHASES],
    [useVision],
  );

  const b = useMemo(() => budget(useVision), [useVision]);
  const measuredTotal = useVision ? MEASURED.totalParamsVision : MEASURED.totalParamsTextOnly;
  const arithmeticMatches = b.total === measuredTotal;

  const resetAnimation = useCallback(() => {
    frameRef.current = 0;
    progressRef.current = 0;
    setFrameIndex(0);
    setProgress(0);
  }, []);

  const advance = useCallback(() => {
    frameRef.current = (frameRef.current + 1) % frames.length;
    progressRef.current = 0;
    setFrameIndex(frameRef.current);
    setProgress(0);
  }, [frames.length]);

  useFrameLoop(playing, (dt) => {
    const { step } = frames[frameRef.current] ?? frames[0];
    const next = progressRef.current + dt / step.ms;
    if (next >= 1) {
      advance();
      return;
    }
    progressRef.current = next;
    setProgress(next);
  });

  const { step, layer } = frames[frameIndex] ?? frames[0];
  const streamY = step.from + (step.to - step.from) * progress;
  const lit = (id: string) => step.lit.includes(id);

  const ink = 'var(--rehearse-ink)';
  const action = 'var(--rehearse-action)';
  const rule = 'var(--rehearse-rule)';

  const wire = (id: string, points: string) => (
    <polyline
      key={id}
      points={points}
      fill="none"
      stroke={lit(id) ? action : rule}
      strokeWidth={lit(id) ? 2.5 : 1.5}
    />
  );

  const box = (id: string, x: number, y: number, w: number, h: number, label: string, fill: string, fontSize = 12) => (
    <g key={id}>
      <rect
        x={x}
        y={y}
        width={w}
        height={h}
        rx={4}
        fill={fill}
        opacity={lit(id) ? 0.34 : 0.12}
        stroke={lit(id) ? action : fill}
        strokeWidth={lit(id) ? 2 : 1}
      />
      <text x={x + w / 2} y={y + h / 2 + fontSize * 0.35} textAnchor="middle" fontSize={fontSize} fill={ink}>
        {label}
      </text>
    </g>
  );

  const adder = (id: string, cy: number) => (
    <g key={id}>
      <circle
        cx="26"
        cy={cy}
        r={lit(id) ? 10 : 8}
        fill={lit(id) ? action : 'none'}
        fillOpacity={lit(id) ? 0.25 : 0}
        stroke={action}
        strokeWidth={lit(id) ? 2.5 : 1.5}
      />
      <text x="26" y={cy + 5} textAnchor="middle" fontSize="15" fill={ink}>
        +
      </text>
    </g>
  );

  return (
    <div className="learning-widget" ref={rootRef}>
      <p>
        {MEASURED.numVisionTokens} vision-patch tokens and the text tokens are concatenated into{' '}
        <strong>one sequence</strong>, then one shared attention block reads all of it -- repeated{' '}
        {MEASURED.layers} times. There is no separate cross-attention module anywhere in this model.
      </p>

      <div className="widget-controls">
        <button
          type="button"
          onClick={() => {
            setUseVision((v) => !v);
            resetAnimation();
          }}
        >
          {useVision ? 'use_vision=True' : 'use_vision=False'}
        </button>
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
          Layer {layer} of {MEASURED.layers}
        </span>
      </div>

      <svg
        viewBox="0 0 320 340"
        width="100%"
        style={{ display: 'block', maxWidth: '28rem', margin: '0 auto' }}
        role="img"
        aria-label={`Fused vision-language decoder: ${useVision ? '64 vision patch tokens concatenated with' : 'only'} text tokens, one shared attention block with grouped-query attention (${MEASURED.kvHeads} key-value heads), RMSNorm, SwiGLU, residual additions`}
      >
        {useVision ? (
          <>
            {box('vision-embed', 8, 8, 118, 32, `${MEASURED.numVisionTokens} vision patches (8x8, 48-d each)`, action, 8.5)}
            {box('text-embed', 138, 8, 118, 32, 'text tokens', action, 10)}
            {wire('wire-vision', '67,40 67,58 26,58 26,90')}
            {wire('wire-text', '197,40 197,66 26,66 26,90')}
            <g opacity={lit('concat-point') ? 1 : 0.55}>
              <circle cx="26" cy="70" r={lit('concat-point') ? 5 : 3.5} fill={action} />
              <text x="36" y="73" fontSize="8" fill={ink}>
                concat
              </text>
            </g>
          </>
        ) : (
          <>
            {box('text-embed', 73, 8, 118, 32, 'text tokens only', action, 10)}
            {wire('wire-text-only', '132,40 132,58 26,58 26,90')}
          </>
        )}

        {/* residual stream: grey is the whole block, blue is how far the token has travelled */}
        <line x1="26" y1="90" x2="26" y2="326" stroke={rule} strokeWidth="2.5" />
        <line x1="26" y1="90" x2="26" y2={streamY} stroke={action} strokeWidth="2.5" />

        {box('norm-a', 60, 96, 100, 26, 'RMSNorm', rule)}
        {box('attn', 60, 140, 170, 44, `Fused attention (${MEASURED.kvHeads} kv heads)`, action, 10)}
        {wire('branch-a', '26,90 26,112 60,112')}
        {wire('return-a', '230,162 250,162 250,200 34,200')}
        {adder('add-a', 200)}

        {box('norm-b', 60, 216, 100, 26, 'RMSNorm', rule)}
        {box('mlp', 60, 260, 170, 34, 'SwiGLU', action, 11)}
        {wire('branch-b', '26,216 26,233 60,233')}
        {wire('return-b', '230,277 250,277 250,312 34,312')}
        {adder('add-b', 312)}

        <circle cx="26" cy={streamY} r="6" fill={action} />
        <circle cx="26" cy={streamY} r="11" fill={action} opacity="0.2" />

        <foreignObject x="232" y="128" width="86" height="96">
          <MaskDiagram lit={lit('mask')} />
        </foreignObject>
      </svg>

      <div className="widget-caption widget-swap" aria-live="polite">
        {captionSteps.map((phaseStep) => (
          <p key={phaseStep.id} data-shown={phaseStep.id === step.id} aria-hidden={phaseStep.id !== step.id}>
            {phaseStep.caption}
          </p>
        ))}
      </div>

      <p>
        Per layer: attention <strong>{b.attention.toLocaleString()}</strong> parameters ({MEASURED.heads} query
        heads sharing {MEASURED.kvHeads} key/value heads); SwiGLU <strong>{b.swiglu.toLocaleString()}</strong>{' '}
        across gate, up, and down projections. {MEASURED.layers} layers ={' '}
        <strong>{b.layersTotal.toLocaleString()}</strong>.
      </p>

      {useVision && (
        <p>
          The vision lane itself adds <strong>{b.patchProj.toLocaleString()}</strong> parameters for the
          48-to-128 patch projection and <strong>{b.patchPos.toLocaleString()}</strong> for the 64-slot position
          table -- a learned lookup, not RoPE, since an 8x8 grid of patches has no left-to-right order for RoPE's
          relative-position math to encode. Total vision extra:{' '}
          <strong>{b.visionExtra.toLocaleString()}</strong>.
        </p>
      )}

      <p>
        Total ({useVision ? 'vision' : 'text-only'}): <strong>{b.total.toLocaleString()}</strong> parameters
        {arithmeticMatches ? (
          <>
            {' '}-- matches the {measuredTotal.toLocaleString()} `param_report()` printed for the run recorded in{' '}
            <code>runs/2026-07-31-vision-vs-text-only.md</code>.
          </>
        ) : (
          <> (measured run: {measuredTotal.toLocaleString()}).</>
        )}{' '}
        Toggling <code>use_vision</code> is the entire difference between the two models this stage compares:{' '}
        {(MEASURED.totalParamsVision - MEASURED.totalParamsTextOnly).toLocaleString()} parameters, exactly the
        patch projection plus the position table above.
      </p>
    </div>
  );
}
