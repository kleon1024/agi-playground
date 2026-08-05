/**
 * The KV-cache tax across the attention variants, drawn and computed.
 *
 * Prose can say "GQA shares KV heads" and the reader still pictures twelve
 * separate caches. This widget draws the actual sharing pattern — 12 query
 * rows on the left, the KV blocks they read from on the right — and computes
 * the cache bill from the same arithmetic `core/kv_cache_anatomy.py` prints:
 * KV bytes per token = 2 * layers * KV heads * d_head * bytes. MLA is the one
 * row whose KV is a single low-rank latent (width 512) shared by every query
 * head, which is why its cache is small while its decode compute is high.
 *
 * Every number comes from the measured stage-02 configuration (d_model 768,
 * 12 layers, 12 query heads, d_head 64, bf16), the same defaults the
 * ModelArchitecture widget uses. Changing the variant or the context length
 * moves only the arithmetic; nothing here is a rounded example.
 */
import React, { useMemo, useState } from 'react';

const CONFIG = {
  dModel: 768,
  nLayer: 12,
  nHead: 12,
  bytes: 2, // bf16
  kvLatent: 512, // MLA (DeepSeek-V2)
};

type VariantId = 'mha' | 'gqa' | 'mqa' | 'mla';

const VARIANTS: Record<VariantId, { label: string; nKv: number; latent: number | null }> = {
  mha: { label: 'MHA — 12 KV heads', nKv: 12, latent: null },
  gqa: { label: 'GQA — 4 KV heads (this repo)', nKv: 4, latent: null },
  mqa: { label: 'MQA — 1 KV head', nKv: 1, latent: null },
  mla: { label: 'MLA — latent 512', nKv: 12, latent: 512 },
};

const CONTEXTS = [256, 1024, 4096, 8192, 16384, 32768, 65536];

function kvBytesPerToken(v: VariantId): number {
  const vv = VARIANTS[v];
  const dHead = CONFIG.dModel / CONFIG.nHead;
  if (vv.latent != null) {
    return 2 * CONFIG.nLayer * vv.latent * CONFIG.bytes;
  }
  return 2 * CONFIG.nLayer * vv.nKv * dHead * CONFIG.bytes;
}

function attnParams(v: VariantId): number {
  const vv = VARIANTS[v];
  const dHead = CONFIG.dModel / CONFIG.nHead;
  const kvWidth = vv.latent != null ? vv.latent : vv.nKv * dHead;
  return CONFIG.dModel * CONFIG.dModel + 2 * CONFIG.dModel * kvWidth + CONFIG.dModel * CONFIG.dModel;
}

function mbAt(v: VariantId, context: number): number {
  return (kvBytesPerToken(v) * context) / (1024 * 1024);
}

export default function AttentionAnatomy(): React.ReactElement {
  const [variant, setVariant] = useState<VariantId>('gqa');
  const [context, setContext] = useState(8192);

  const vv = VARIANTS[variant];
  const kvPerToken = kvBytesPerToken(variant);
  const mb = mbAt(variant, context);
  const ratio = kvPerToken / kvBytesPerToken('mha');
  const kvGroups = useMemo(() => {
    const nHead = CONFIG.nHead;
    const nKv = vv.latent != null ? 1 : vv.nKv;
    const per = nHead / nKv;
    const rows: { start: number; count: number }[] = [];
    for (let g = 0; g < nKv; g++) {
      rows.push({ start: g * per, count: per });
    }
    return rows;
  }, [variant, vv.latent, vv.nKv]);

  return (
    <div className="learning-widget">
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center' }}>
        <label>
          Variant
          <select
            value={variant}
            onChange={(e) => setVariant(e.target.value as VariantId)}
            style={{ display: 'block', marginTop: '0.25rem' }}
          >
            {(Object.keys(VARIANTS) as VariantId[]).map((id) => (
              <option key={id} value={id}>
                {VARIANTS[id].label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Context length
          <select
            value={context}
            onChange={(e) => setContext(Number(e.target.value))}
            style={{ display: 'block', marginTop: '0.25rem' }}
          >
            {CONTEXTS.map((c) => (
              <option key={c} value={c}>
                {c.toLocaleString()} tokens
              </option>
            ))}
          </select>
        </label>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', alignItems: 'stretch' }}>
        <div aria-hidden="true" style={{ flex: '1 1 8rem', maxWidth: '12rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--rehearse-copy-muted)', marginBottom: '0.25rem' }}>
            12 query heads
          </div>
          {Array.from({ length: CONFIG.nHead }, (_, i) => (
            <div
              key={i}
              style={{ height: '0.9rem', marginBottom: '0.15rem', background: 'var(--rehearse-action-soft)' }}
            />
          ))}
        </div>
        <div aria-hidden="true" style={{ flex: '1 1 6rem', maxWidth: '8rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--rehearse-copy-muted)', marginBottom: '0.25rem' }}>
            {vv.latent != null ? 'shared latent' : `${vv.nKv} KV ${vv.nKv === 1 ? 'head' : 'heads'}`}
          </div>
          {kvGroups.map((g, gi) => (
            <div
              key={gi}
              style={{
                height: `${g.count * 1.05}rem`,
                marginBottom: '0.15rem',
                background: 'var(--rehearse-action)',
              }}
            />
          ))}
        </div>
      </div>

      <p style={{ marginTop: '1rem', marginBottom: '0.25rem' }}>
        <strong>{vv.label}</strong> at {context.toLocaleString()} tokens:{' '}
        <strong>{mb.toFixed(1)} MB</strong> of KV cache — {ratio.toFixed(2)}x the MHA bill.
      </p>
      <p style={{ margin: 0, color: 'var(--rehearse-copy-muted)' }}>
        Attention parameters per layer: {(attnParams(variant) / 1e6).toFixed(2)}M. KV bytes per
        token: {kvPerToken.toLocaleString()} (bf16).
      </p>
    </div>
  );
}
