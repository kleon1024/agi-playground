/**
 * Why the KV cache, not the weights, decides how many users you can serve.
 *
 * The formula is easy to nod along to and hard to feel:
 *
 *   bytes = 2 · layers · kv_heads · head_dim · seq_len · batch · dtype
 *
 * Nothing in it shrinks with a smaller model — weights are a fixed cost, while
 * the cache grows with every token every user generates. Drag the batch size up
 * and watch the cache overtake the weights, which is the moment your serving
 * capacity stops being about the model at all.
 */
import React, { useEffect, useMemo, useState } from 'react';

const MODELS = {
  'this repo (88M)': { layers: 12, heads: 12, kvHeads: 4, headDim: 64, weightsGB: 0.176 },
  'GPT-2 (1.5B)': { layers: 48, heads: 25, kvHeads: 25, headDim: 64, weightsGB: 3.0 },
  'Llama-class 7B': { layers: 32, heads: 32, kvHeads: 32, headDim: 128, weightsGB: 14 },
  'Llama-class 70B (GQA-8)': { layers: 80, heads: 64, kvHeads: 8, headDim: 128, weightsGB: 140 },
};

export default function KVCacheGrowth(): React.ReactElement {
  const [model, setModel] = useState<keyof typeof MODELS>('Llama-class 7B');
  const [batch, setBatch] = useState(8);
  const [seq, setSeq] = useState(4096);
  const [gqa, setGqa] = useState(false);
  const [playing, setPlaying] = useState(false);

  // Animate context growth, which is what actually happens during decode: the
  // cache is not allocated once, it accretes one token at a time.
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setSeq((s) => (s >= 32768 ? 512 : Math.round(s * 1.35)));
    }, 420);
    return () => clearInterval(id);
  }, [playing]);

  const m = MODELS[model];
  const { cacheGB, ratio, mhaGB } = useMemo(() => {
    const kvHeads = gqa ? Math.max(1, Math.round(m.kvHeads / 4)) : m.kvHeads;
    const bytes = 2 * m.layers * kvHeads * m.headDim * seq * batch * 2; // bf16
    const mha = 2 * m.layers * m.heads * m.headDim * seq * batch * 2;
    return {
      cacheGB: bytes / 1e9,
      mhaGB: mha / 1e9,
      ratio: bytes / 1e9 / m.weightsGB,
    };
  }, [m, batch, seq, gqa]);

  const total = m.weightsGB + cacheGB;
  const weightPct = (m.weightsGB / total) * 100;
  const H80 = 80; // a large accelerator, for a sense of scale

  return (
    <div className="learning-widget">
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '0.9rem' }}>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value as keyof typeof MODELS)}
          style={{ padding: '0.3rem 0.5rem', borderRadius: 6 }}
        >
          {Object.keys(MODELS).map((k) => (
            <option key={k}>{k}</option>
          ))}
        </select>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          batch <strong>{batch}</strong>
          <input type="range" min={1} max={128} value={batch}
                 onChange={(e) => setBatch(Number(e.target.value))} style={{ width: 120 }} />
        </label>
        <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          context <strong>{seq.toLocaleString()}</strong>
          <input type="range" min={512} max={32768} step={512} value={seq}
                 onChange={(e) => setSeq(Number(e.target.value))} style={{ width: 120 }} />
        </label>
        <button onClick={() => setPlaying((p) => !p)}
                style={{ padding: '0.25rem 0.7rem', borderRadius: 6, cursor: 'pointer' }}>
          {playing ? '⏸ pause' : '▶ grow context'}
        </button>
        <label style={{ cursor: 'pointer' }}>
          <input type="checkbox" checked={gqa} onChange={(e) => setGqa(e.target.checked)} /> GQA ÷4
        </label>
      </div>

      <div style={{ display: 'flex', height: 42, borderRadius: 6, overflow: 'hidden', fontSize: 'var(--type-xs)' }}>
        <div style={{ width: `${weightPct}%`, background: 'var(--brand-chart-action-fill)', color: 'var(--rehearse-ink)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      transition: 'width 300ms ease-out' }}>
          {weightPct > 12 ? `weights ${m.weightsGB.toFixed(1)} GB` : ''}
        </div>
        <div style={{ width: `${100 - weightPct}%`, background: ratio > 1 ? 'var(--brand-chart-danger-fill)' : 'var(--brand-chart-positive-fill)',
                      color: 'var(--rehearse-ink)', display: 'flex', alignItems: 'center',
                      justifyContent: 'center', transition: 'width 300ms ease-out, background 300ms' }}>
          {100 - weightPct > 12 ? `KV cache ${cacheGB.toFixed(1)} GB` : ''}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1.4rem', fontSize: 'var(--type-sm)', marginTop: '0.7rem', flexWrap: 'wrap' }}>
        <span>cache / weights <strong>{ratio.toFixed(2)}×</strong></span>
        <span>total <strong>{total.toFixed(1)} GB</strong></span>
        {gqa && <span style={{ opacity: 0.8 }}>full MHA would be {mhaGB.toFixed(1)} GB</span>}
        <span style={{ color: total > H80 ? 'var(--brand-chart-danger)' : 'inherit' }}>
          {total > H80
            ? `exceeds an ${H80} GB accelerator — requests must be evicted or refused`
            : `fits in ${H80} GB`}
        </span>
      </div>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.7rem' }}>
        Weights are a fixed cost; the cache grows with batch × context. Push
        either up and the red bar takes over — at which point buying a bigger
        model is not your problem, and paging, eviction, or grouped-query
        attention is. This is the arithmetic behind every serving decision in
        the inference lesson.
      </p>
    </div>
  );
}
