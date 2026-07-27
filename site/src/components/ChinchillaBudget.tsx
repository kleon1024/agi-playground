/**
 * The compute-optimal trade, and why production deliberately violates it.
 *
 * Training compute is roughly C = 6ND — six FLOPs per parameter per token.
 * Chinchilla's finding was that for a fixed C, loss is minimised near D ≈ 20N,
 * and most pre-2022 models were far off that line: too large, trained on too
 * little data.
 *
 * The part usually left out is that compute-optimal is not deployment-optimal.
 * Training happens once; inference happens forever, and inference cost scales
 * with N alone. So labs knowingly train smaller models past the optimal point,
 * spending extra training compute to buy permanently cheaper serving.
 */
import React, { useMemo, useState } from 'react';

const HOURS_PER_GPU_DAY = 24;
const EFFECTIVE_TFLOPS = 400e12; // a datacentre accelerator at realistic MFU

function fmt(x: number, unit: string): string {
  if (x >= 1e9) return `${(x / 1e9).toFixed(2)}B ${unit}`;
  if (x >= 1e6) return `${(x / 1e6).toFixed(0)}M ${unit}`;
  return `${x.toFixed(0)} ${unit}`;
}

export default function ChinchillaBudget(): React.ReactElement {
  const [params, setParams] = useState(88e6);
  const [tokens, setTokens] = useState(3.01e9);

  const { flops, gpuDays, ratio, optimalTokens, verdict, tone } = useMemo(() => {
    const c = 6 * params * tokens;
    const optimal = 20 * params;
    const r = tokens / optimal;
    let v: string;
    let t: string;
    if (r < 0.5) {
      v = 'undertrained — this model has capacity it never learned to use';
      t = 'var(--brand-chart-warning)';
    } else if (r < 1.5) {
      v = 'near compute-optimal — Chinchilla territory';
      t = 'var(--brand-chart-positive)';
    } else if (r < 6) {
      v = 'over-trained on purpose — paying training compute for cheaper inference';
      t = 'var(--brand-chart-action)';
    } else {
      v = 'heavily over-trained — the modern deployment-optimal regime';
      t = 'var(--brand-chart-signal)';
    }
    return {
      flops: c,
      gpuDays: c / EFFECTIVE_TFLOPS / 3600 / HOURS_PER_GPU_DAY,
      ratio: r,
      optimalTokens: optimal,
      verdict: v,
      tone: t,
    };
  }, [params, tokens]);

  // Log sliders: the interesting range spans six orders of magnitude.
  const pExp = Math.log10(params);
  const tExp = Math.log10(tokens);

  return (
    <div style={{ margin: '1.5rem 0' }}>
      <div style={{ display: 'grid', gap: '0.7rem', marginBottom: '1rem' }}>
        <label style={{ display: 'flex', gap: '0.7rem', alignItems: 'center' }}>
          <span style={{ minWidth: '9rem' }}>parameters <strong>{fmt(params, '')}</strong></span>
          <input type="range" min={6} max={12} step={0.05} value={pExp}
                 onChange={(e) => setParams(10 ** Number(e.target.value))}
                 style={{ flex: 1, maxWidth: 260 }} />
        </label>
        <label style={{ display: 'flex', gap: '0.7rem', alignItems: 'center' }}>
          <span style={{ minWidth: '9rem' }}>tokens <strong>{fmt(tokens, '')}</strong></span>
          <input type="range" min={7} max={14} step={0.05} value={tExp}
                 onChange={(e) => setTokens(10 ** Number(e.target.value))}
                 style={{ flex: 1, maxWidth: 260 }} />
        </label>
      </div>

      <div style={{ display: 'flex', height: 10, borderRadius: 5, overflow: 'hidden', marginBottom: '0.6rem' }}>
        <div style={{ width: `${Math.min(ratio / 20, 1) * 100}%`, background: tone, transition: 'width 200ms, background 200ms' }} />
        <div style={{ flex: 1, background: 'var(--ifm-color-emphasis-200)' }} />
      </div>

      <div style={{ display: 'flex', gap: '1.4rem', flexWrap: 'wrap', fontSize: '0.85rem' }}>
        <span>compute <strong>{(flops / 1e21).toFixed(2)}×10²¹ FLOPs</strong></span>
        <span>≈ <strong>{gpuDays < 1 ? `${(gpuDays * 24).toFixed(1)} GPU-hours` : `${gpuDays.toFixed(1)} GPU-days`}</strong></span>
        <span>tokens/param <strong>{ratio.toFixed(1)}×</strong> optimal</span>
      </div>
      <p style={{ color: tone, fontSize: '0.85rem', margin: '0.5rem 0 0' }}>{verdict}</p>

      <p style={{ fontSize: '0.8rem', opacity: 0.75, marginTop: '0.7rem' }}>
        Compute-optimal for {fmt(params, 'parameters')} is about{' '}
        {fmt(optimalTokens, 'tokens')}. Slide left and the model is starved;
        slide right and you are deliberately overspending on training to make
        every future inference cheaper — training is paid once, serving is paid
        forever. The repo&apos;s own 88M model sits at ~34×, well into that
        deliberate over-training regime.
      </p>
    </div>
  );
}
