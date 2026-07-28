/**
 * The 88M decoder, drawn, with the parameter arithmetic attached to the parts.
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
import React, { useMemo, useState } from 'react';

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
  const b = useMemo(() => budget(kvHeads), [kvHeads]);
  const measuredB = useMemo(() => budget(MEASURED.kvHeads), []);
  const isMeasured = kvHeads === MEASURED.kvHeads;

  const ink = 'var(--rehearse-ink)';
  const action = 'var(--rehearse-action)';
  const rule = 'var(--rehearse-rule)';
  const muted = 'var(--rehearse-copy-muted)';

  const box = (
    x: number,
    y: number,
    w: number,
    h: number,
    label: string,
    fill: string,
    sub?: string,
  ) => (
    <g key={`${label}-${y}`}>
      <rect x={x} y={y} width={w} height={h} rx={4} fill={fill} opacity={0.16} stroke={fill} />
      <text x={x + w / 2} y={y + (sub ? h / 2 - 2 : h / 2 + 4)} textAnchor="middle" fontSize="11" fill={ink}>
        {label}
      </text>
      {sub && (
        <text x={x + w / 2} y={y + h / 2 + 12} textAnchor="middle" fontSize="9" fill={muted}>
          {sub}
        </text>
      )}
    </g>
  );

  return (
    <div className="learning-widget">
      <p>
        One block, repeated {MEASURED.layers} times. The residual stream runs down the left at width{' '}
        {MEASURED.dModel}; every sub-layer reads from it, writes back into it, and never changes its
        width — which is why depth can be added without touching anything else.
      </p>

      <svg
        viewBox="0 0 320 300"
        width="100%"
        role="img"
        aria-label={`Decoder block: RMSNorm, grouped-query attention with ${kvHeads} key-value heads, RMSNorm, SwiGLU, with residual additions`}
      >
        {/* residual stream */}
        <line x1="26" y1="12" x2="26" y2="288" stroke={action} strokeWidth="2.5" />
        <text x="8" y="152" fontSize="9" fill={muted} transform="rotate(-90 8 152)" textAnchor="middle">
          residual stream, d=768
        </text>

        {/* attention half */}
        {box(60, 18, 100, 30, 'RMSNorm', rule)}
        {box(60, 62, 230, 54, `Grouped-query attention`, action, `${MEASURED.heads} Q heads share ${kvHeads} KV head${kvHeads === 1 ? '' : 's'} · ${b.attention.toLocaleString()} params`)}
        <circle cx="26" cy="132" r="8" fill="none" stroke={action} strokeWidth="1.5" />
        <text x="26" y="136" textAnchor="middle" fontSize="11" fill={ink}>+</text>
        <line x1="26" y1="89" x2="60" y2="89" stroke={rule} strokeWidth="1.5" />
        <line x1="290" y1="116" x2="290" y2="132" stroke={action} strokeWidth="1.5" />
        <line x1="290" y1="132" x2="34" y2="132" stroke={action} strokeWidth="1.5" />

        {/* mlp half */}
        {box(60, 152, 100, 30, 'RMSNorm', rule)}
        {box(60, 196, 230, 54, 'SwiGLU', action, `gate, up, down · ${b.swiglu.toLocaleString()} params`)}
        <circle cx="26" cy="266" r="8" fill="none" stroke={action} strokeWidth="1.5" />
        <text x="26" y="270" textAnchor="middle" fontSize="11" fill={ink}>+</text>
        <line x1="26" y1="223" x2="60" y2="223" stroke={rule} strokeWidth="1.5" />
        <line x1="290" y1="250" x2="290" y2="266" stroke={action} strokeWidth="1.5" />
        <line x1="290" y1="266" x2="34" y2="266" stroke={action} strokeWidth="1.5" />
      </svg>

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
