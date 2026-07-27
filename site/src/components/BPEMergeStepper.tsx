/**
 * The vocabulary forming, one merge at a time.
 *
 * TokenizerPlayground shows the finished tokenizer applied to text. This shows
 * the other half — how the merge list came to exist. Watching ' t', ' a', 'he',
 * 'in' arrive first and ' catastrophe' arrive at merge 16,000 makes two things
 * obvious that a paragraph struggles with:
 *
 *   * BPE is pure frequency. Nothing linguistic is supplied; word-like units
 *     emerge because letters that co-occur get merged, repeatedly.
 *   * The long tail is where the vocabulary budget actually goes. The first
 *     hundred merges buy enormous compression; the last thousand buy very
 *     little, which is why the compression curve flattens while the embedding
 *     table keeps growing.
 *
 * Merges are read from the same tokenizer.json the training pipeline produced.
 */
import useBaseUrl from '@docusaurus/useBaseUrl';
import React, { useEffect, useMemo, useState } from 'react';

interface Loaded {
  pieces: string[]; // learned token text, in merge order
  counts: number[]; // token length, a proxy for what the merge captured
}

const STOPS = [0, 50, 200, 500, 1000, 2000, 4000, 8000, 16128];

export default function BPEMergeStepper(): React.ReactElement {
  const dataUrl = useBaseUrl('/data/tokenizer.json');
  const [data, setData] = useState<Loaded | null>(null);
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    fetch(dataUrl)
      .then((r) => r.json())
      .then((raw: { merges: [number, number, number][] }) => {
        const vocab = new Map<number, string>();
        const dec = new TextDecoder();
        for (let i = 0; i < 256; i++) vocab.set(i, dec.decode(new Uint8Array([i])));
        const pieces: string[] = [];
        for (const [a, b, id] of raw.merges) {
          const s = (vocab.get(a) ?? '') + (vocab.get(b) ?? '');
          vocab.set(id, s);
          pieces.push(s);
        }
        setData({ pieces, counts: pieces.map((p) => p.length) });
      })
      .catch(() => setData(null));
  }, [dataUrl]);

  useEffect(() => {
    if (!playing || !data) return;
    const id = setInterval(() => {
      setIdx((i) => {
        const next = i + 1;
        if (next >= STOPS.length) {
          setPlaying(false);
          return i;
        }
        return next;
      });
    }, 1100);
    return () => clearInterval(id);
  }, [playing, data]);

  const view = useMemo(() => {
    if (!data) return null;
    const upto = STOPS[idx];
    const window = data.pieces.slice(Math.max(0, upto - 12), Math.max(12, upto));
    const lens = data.counts.slice(0, Math.max(1, upto));
    const avg = lens.reduce((a, b) => a + b, 0) / Math.max(lens.length, 1);
    return { upto, window, avg };
  }, [data, idx]);

  if (!data || !view) return <p>Loading the merge list…</p>;

  return (
    <div className="learning-widget">
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <button
          onClick={() => {
            if (idx >= STOPS.length - 1) setIdx(0);
            setPlaying((p) => !p);
          }}
          style={{ padding: '0.3rem 0.8rem', borderRadius: 6, cursor: 'pointer' }}
        >
          {playing ? '⏸ pause' : '▶ watch it learn'}
        </button>
        <input
          type="range"
          min={0}
          max={STOPS.length - 1}
          value={idx}
          onChange={(e) => {
            setPlaying(false);
            setIdx(Number(e.target.value));
          }}
          style={{ flex: 1, minWidth: 160, maxWidth: 280 }}
        />
        <span style={{ fontVariantNumeric: 'tabular-nums' }}>
          after <strong>{view.upto.toLocaleString()}</strong> merges
        </span>
      </div>

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 5,
          marginTop: '0.9rem',
          padding: '0.8rem',
          borderRadius: 8,
          background: 'var(--ifm-code-background)',
          minHeight: '4.2rem',
          alignContent: 'flex-start',
        }}
      >
        {view.window.map((p, i) => (
          <span
            key={`${idx}-${i}`}
            style={{
              background: 'var(--brand-chart-positive-fill)',
              color: 'var(--rehearse-ink)',
              padding: '3px 7px',
              borderRadius: 4,
              fontFamily: 'var(--ifm-font-family-monospace)',
              fontSize: 'var(--type-sm)',
              whiteSpace: 'pre',
              animation: 'none',
            }}
          >
            {p.replace(/ /g, '␣').replace(/\n/g, '⏎')}
          </span>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '1.4rem', fontSize: 'var(--type-sm)', marginTop: '0.7rem', flexWrap: 'wrap' }}>
        <span>mean token length <strong>{view.avg.toFixed(2)}</strong> chars</span>
        <span style={{ opacity: 0.75 }}>
          {view.upto <= 200
            ? 'frequent letter pairs — pure bigram statistics'
            : view.upto <= 2000
            ? 'common morphemes and short words'
            : 'rare whole words: the long tail of the vocabulary budget'}
        </span>
      </div>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.7rem' }}>
        These are the actual merges learned by this repository&apos;s tokenizer,
        in the order they were learned. Nothing linguistic was supplied — word
        shapes emerge because frequently adjacent bytes get merged, over and
        over. Notice how much the first few hundred merges buy, and how little
        the last few thousand do: that flattening is the compression knee, and
        it is why vocabulary size is a trade-off rather than a value to
        maximise.
      </p>
    </div>
  );
}
