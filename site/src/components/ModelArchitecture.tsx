/**
 * The 88M decoder, drawn and animated, with the parameter arithmetic attached
 * to the parts.
 *
 * Two things are hard to see in a static block diagram: that the residual
 * stream is never overwritten, only added to, and that every sub-layer works on
 * a copy while the stream itself passes straight through. So one token is
 * animated down the stream and the sub-layers light up as they read from it and
 * write back into it.
 *
 * Every number defaults to the measured stage-02 configuration and is computed
 * from it rather than typed in: change the KV-head count and the attention
 * parameters, the total, and the KV cache all move together, because they are
 * the same arithmetic the model summary prints. Recorded in
 * missions/01-language-model-agent/02-pretrain/runs/2026-07-28-pretrain-3b.md.
 *
 * Colours come from the shared theme variables so the drawing follows the
 * page's light or dark mode instead of carrying its own palette.
 */
import React, { useCallback, useMemo, useRef, useState } from 'react';

import { useAutoplayOnView, useFrameLoop } from './useMotionClock';

const MEASURED = {
  vocab: 16512,
  dModel: 768,
  layers: 12,
  heads: 12,
  kvHeads: 4,
  dFf: 2048,
  blockSize: 1024,
  totalParams: 88_197_888,
};

const KV_CHOICES = [
  { value: 12, label: '12 (full multi-head)' },
  { value: 4, label: '4 (this run)' },
  { value: 2, label: '2' },
  { value: 1, label: '1 (multi-query)' },
];

const BYTES_PER_BF16 = 2;

/**
 * One pass through a block, as the reader should narrate it. `from` and `to`
 * are positions on the residual stream in the drawing's own coordinates; a
 * phase where they are equal is one where the stream waits while a sub-layer
 * computes on a copy of it.
 */
const PHASES = [
  {
    id: 'enter',
    from: 12,
    to: 89,
    ms: 700,
    lit: [] as string[],
    caption: 'The residual stream carries this token’s current representation into the block.',
  },
  {
    id: 'norm-a',
    from: 89,
    to: 89,
    ms: 800,
    lit: ['norm-a', 'branch-a'],
    caption: 'RMSNorm rescales a copy. The stream itself is not modified.',
  },
  {
    id: 'attend',
    from: 89,
    to: 89,
    ms: 950,
    lit: ['attn'],
    caption:
      'Attention mixes information across positions — the only place in the block where tokens see each other.',
  },
  {
    id: 'add-a',
    from: 89,
    to: 132,
    ms: 800,
    lit: ['return-a', 'add-a'],
    caption:
      'Its output is added back. Nothing is overwritten, which is why a gradient can still reach layer 1.',
  },
  {
    id: 'carry',
    from: 132,
    to: 223,
    ms: 700,
    lit: [],
    caption: 'The stream now means more and is exactly as wide as before: 768.',
  },
  {
    id: 'norm-b',
    from: 223,
    to: 223,
    ms: 800,
    lit: ['norm-b', 'branch-b'],
    caption: 'A second norm prepares a copy for the position-wise half.',
  },
  {
    id: 'mlp',
    from: 223,
    to: 223,
    ms: 950,
    lit: ['mlp'],
    caption:
      'SwiGLU transforms each position independently — no mixing, and more than twice the parameters of attention.',
  },
  {
    id: 'add-b',
    from: 223,
    to: 266,
    ms: 800,
    lit: ['return-b', 'add-b'],
    caption: 'Added back again. The block wrote two deltas and destroyed nothing.',
  },
  {
    id: 'exit',
    from: 266,
    to: 288,
    ms: 600,
    lit: [],
    caption: 'Out of the block, into an identical one.',
  },
];

function budget(kvHeads: number) {
  const { vocab, dModel, layers, dFf, heads } = MEASURED;
  const dHead = dModel / heads;

  const embedding = vocab * dModel; // tied with the output head
  // q projects to all heads; k and v project to kvHeads only; o projects back.
  const attention = dModel * dModel + 2 * (dModel * kvHeads * dHead) + dModel * dModel;
  const swiglu = 3 * dModel * dFf; // gate, up, down
  // Two RMSNorm gains per block plus one final norm. Small enough to forget,
  // and forgetting them lands you 19,200 short of the number the model prints.
  const norms = 2 * dModel;
  const perLayer = attention + swiglu + norms;
  const total = embedding + layers * perLayer + dModel;

  // Two tensors (K and V) per layer, per token.
  const kvCacheBytes = 2 * layers * kvHeads * dHead * BYTES_PER_BF16;

  return { embedding, attention, swiglu, perLayer, total, kvCacheBytes, dHead };
}

function Bar({ parts }: { parts: { label: string; value: number; tone: string }[] }) {
  const total = parts.reduce((sum, part) => sum + part.value, 0);
  let offset = 0;
  return (
    <svg viewBox="0 0 100 8" width="100%" height="22" role="img" aria-label="Parameter composition">
      {parts.map((part) => {
        const width = (part.value / total) * 100;
        const x = offset;
        offset += width;
        return (
          <rect
            key={part.label}
            x={x}
            y={0}
            width={width}
            height={8}
            fill={part.tone}
            opacity={0.85}
          >
            <title>{`${part.label}: ${part.value.toLocaleString()} parameters`}</title>
          </rect>
        );
      })}
    </svg>
  );
}

export default function ModelArchitecture(): React.ReactElement {
  const [kvHeads, setKvHeads] = useState(MEASURED.kvHeads);
  const [phase, setPhase] = useState(0);
  const [progress, setProgress] = useState(0);
  const [layer, setLayer] = useState(1);
  const { ref: rootRef, playing, setPlaying } = useAutoplayOnView<HTMLDivElement>();

  const phaseRef = useRef(0);
  const progressRef = useRef(0);
  const layerRef = useRef(1);

  const b = useMemo(() => budget(kvHeads), [kvHeads]);
  const measuredB = useMemo(() => budget(MEASURED.kvHeads), []);
  const isMeasured = kvHeads === MEASURED.kvHeads;

  const advance = useCallback(() => {
    const next = phaseRef.current + 1;
    if (next >= PHASES.length) {
      phaseRef.current = 0;
      layerRef.current = layerRef.current >= MEASURED.layers ? 1 : layerRef.current + 1;
      setLayer(layerRef.current);
    } else {
      phaseRef.current = next;
    }
    progressRef.current = 0;
    setPhase(phaseRef.current);
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

  /* Labels stay in the drawing; every number lives in HTML underneath, where it
     inherits the shared type scale instead of being scaled by the viewBox. */
  const box = (id: string, x: number, y: number, w: number, h: number, label: string, fill: string) => (
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
      <text x={x + w / 2} y={y + h / 2 + 5} textAnchor="middle" fontSize="15" fill={ink}>
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
        One block, repeated {MEASURED.layers} times. The residual stream runs down the left at width{' '}
        {MEASURED.dModel}; every sub-layer reads from it, writes back into it, and never changes its
        width — which is why depth can be added without touching anything else.
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
          Layer {layer} of {MEASURED.layers}
        </span>
      </div>

      <svg
        viewBox="0 0 320 300"
        width="100%"
        style={{ display: 'block', maxWidth: '26rem', margin: '0 auto' }}
        role="img"
        aria-label={`Decoder block: RMSNorm, grouped-query attention with ${kvHeads} key-value heads, RMSNorm, SwiGLU, with residual additions`}
      >
        {/* residual stream: the grey line is the whole block, the blue line is
            how far this token has travelled through it */}
        <line x1="26" y1="12" x2="26" y2="288" stroke={rule} strokeWidth="2.5" />
        <line x1="26" y1="12" x2="26" y2={streamY} stroke={action} strokeWidth="2.5" />

        {/* attention half */}
        {box('norm-a', 60, 18, 100, 30, 'RMSNorm', rule)}
        {box('attn', 60, 62, 230, 54, 'Grouped-query attention', action)}
        {wire('branch-a', '26,89 60,89')}
        {wire('return-a', '290,116 290,132 34,132')}
        {adder('add-a', 132)}

        {/* position-wise half */}
        {box('norm-b', 60, 152, 100, 30, 'RMSNorm', rule)}
        {box('mlp', 60, 196, 230, 54, 'SwiGLU', action)}
        {wire('branch-b', '26,223 60,223')}
        {wire('return-b', '290,250 290,266 34,266')}
        {adder('add-b', 266)}

        {/* the token itself */}
        <circle cx="26" cy={streamY} r="6" fill={action} />
        <circle cx="26" cy={streamY} r="11" fill={action} opacity="0.2" />
      </svg>

      <p className="widget-caption" aria-live="polite">
        {step.caption}
      </p>

      <p>
        Per layer: attention <strong>{b.attention.toLocaleString()}</strong> parameters, with{' '}
        {MEASURED.heads} query heads sharing {kvHeads} key/value head
        {kvHeads === 1 ? '' : 's'}; SwiGLU <strong>{b.swiglu.toLocaleString()}</strong> across its
        gate, up, and down projections; two RMSNorm gains 1,536.
      </p>

      <label>
        Key/value heads
        <select
          aria-label="Key/value heads"
          value={kvHeads}
          onChange={(event) => setKvHeads(Number(event.target.value))}
        >
          {KV_CHOICES.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>
      </label>

      <p>
        Total: <strong>{b.total.toLocaleString()}</strong> parameters. KV cache:{' '}
        <strong>{b.kvCacheBytes.toLocaleString()} bytes per token</strong> in bf16 — at the{' '}
        {MEASURED.blockSize.toLocaleString()}-token context that is{' '}
        {((b.kvCacheBytes * MEASURED.blockSize) / 1024 / 1024).toFixed(1)} MB for one sequence.
      </p>

      <Bar
        parts={[
          { label: 'Embedding (tied with head)', value: b.embedding, tone: 'var(--rehearse-copy-muted)' },
          { label: `Attention x${MEASURED.layers}`, value: MEASURED.layers * b.attention, tone: 'var(--rehearse-action)' },
          { label: `SwiGLU x${MEASURED.layers}`, value: MEASURED.layers * b.swiglu, tone: 'var(--rehearse-action-strong)' },
        ]}
      />
      <p>
        Embedding {((b.embedding / b.total) * 100).toFixed(1)}% · attention{' '}
        {(((MEASURED.layers * b.attention) / b.total) * 100).toFixed(1)}% · SwiGLU{' '}
        {(((MEASURED.layers * b.swiglu) / b.total) * 100).toFixed(1)}%. The feed-forward block holds
        most of the parameters, which is the usual shape and the reason mixture-of-experts designs
        attack that block rather than attention.
      </p>

      <p>
        {isMeasured ? (
          <>
            This is the configuration that trained: <strong>{MEASURED.totalParams.toLocaleString()}</strong>{' '}
            parameters, confirmed by both <code>core/model.py</code> and its HuggingFace counterpart.
          </>
        ) : (
          <>
            Hypothetical. Against the run&rsquo;s 4 KV heads this changes parameters by{' '}
            {(b.total - measuredB.total >= 0 ? '+' : '') + (b.total - measuredB.total).toLocaleString()} and
            the KV cache by {(b.kvCacheBytes / measuredB.kvCacheBytes).toFixed(2)}x. Grouped-query
            attention buys serving memory at pretraining time: the cache shrinks with the KV-head
            count, and the parameter change is small enough to be nearly free.
          </>
        )}
      </p>
    </div>
  );
}
