/**
 * Live BPE tokenizer, running this repository's own trained vocabulary.
 *
 * This is not a simulation or a re-implementation with different weights: it
 * loads the exact `tokenizer.json` produced by
 * 01-language-model/01-tokenizer and applies the same merge
 * rules, in the same learned order, that the training pipeline uses.
 *
 * The point is that BPE stops being abstract the moment you can type a word
 * and watch it fuse. Reading "merges are applied in the order they were
 * learned" teaches far less than seeing 'catastrophe' collapse from eleven
 * byte tokens into one, and seeing a misspelling refuse to.
 */
import useBaseUrl from '@docusaurus/useBaseUrl';
import React, { useEffect, useMemo, useState } from 'react';

type Merges = Map<string, { rank: number; id: number }>;

interface Tokenizer {
  merges: Merges;
  vocab: Map<number, number[]>; // id -> byte sequence
}

/**
 * Pre-tokenization split, ported from core/bpe.py's SPLIT_PATTERN.
 *
 * Python's pattern uses possessive quantifiers (`?+`, `++`) and an inline
 * case-insensitive group, neither of which JavaScript regex supports. The
 * alternation below is written out explicitly instead. Possessive quantifiers
 * are a backtracking optimization here rather than a semantic difference, so
 * the resulting split matches for ordinary text.
 */
const SPLIT_RE =
  /'(?:[sdmtSDMT]|ll|LL|ve|VE|re|RE)|[^\r\n\w]?\w+|\d{1,3}| ?[^\s\w]+[\r\n]*|\s*[\r\n]|\s+(?!\S)|\s+/gu;

function bytesOf(s: string): number[] {
  return Array.from(new TextEncoder().encode(s));
}

function decodeBytes(b: number[]): string {
  return new TextDecoder('utf-8', { fatal: false }).decode(new Uint8Array(b));
}

/** Apply merges to one pre-token, recording each step for the trace view. */
function encodePiece(
  piece: string,
  tok: Tokenizer,
): { ids: number[]; steps: { pair: string; result: number[] }[] } {
  let ids = bytesOf(piece);
  const steps: { pair: string; result: number[] }[] = [];

  // eslint-disable-next-line no-constant-condition
  while (ids.length >= 2) {
    // Find the applicable merge learned EARLIEST. Merge order is the
    // tokenizer's contract — applying them out of order yields a different
    // segmentation than training implied.
    let best: { rank: number; id: number; at: number } | null = null;
    for (let i = 0; i < ids.length - 1; i++) {
      const m = tok.merges.get(`${ids[i]},${ids[i + 1]}`);
      if (m && (best === null || m.rank < best.rank)) {
        best = { rank: m.rank, id: m.id, at: i };
      }
    }
    if (best === null) break;

    const pairKey = `${decodeBytes(tok.vocab.get(ids[best.at]) ?? [])}${decodeBytes(
      tok.vocab.get(ids[best.at + 1]) ?? [],
    )}`;

    const out: number[] = [];
    let i = 0;
    const a = ids[best.at];
    const b = ids[best.at + 1];
    while (i < ids.length) {
      if (i < ids.length - 1 && ids[i] === a && ids[i + 1] === b) {
        out.push(best.id);
        i += 2;
      } else {
        out.push(ids[i]);
        i += 1;
      }
    }
    ids = out;
    steps.push({ pair: pairKey, result: [...ids] });
    if (steps.length > 64) break; // guard against pathological input
  }
  return { ids, steps };
}

function encode(text: string, tok: Tokenizer) {
  const pieces = text.match(SPLIT_RE) ?? [];
  const all: { text: string; id: number }[] = [];
  let traced: { pair: string; result: number[] }[] = [];
  let tracedPiece = '';

  for (const piece of pieces) {
    const { ids, steps } = encodePiece(piece, tok);
    if (steps.length > traced.length) {
      traced = steps;
      tracedPiece = piece;
    }
    for (const id of ids) {
      all.push({ text: decodeBytes(tok.vocab.get(id) ?? []), id });
    }
  }
  return { tokens: all, traced, tracedPiece };
}

const PALETTE = [
  'var(--brand-chart-positive-fill)', 'var(--brand-chart-danger-fill)', 'var(--brand-chart-warning-fill)', 'var(--brand-chart-action-fill)',
  'var(--brand-chart-danger-fill)', 'var(--brand-chart-signal)', 'var(--brand-chart-positive-fill)', 'var(--brand-chart-warning-fill)',
];

export default function TokenizerPlayground(): React.ReactElement {
  const dataUrl = useBaseUrl('/data/tokenizer.json');
  const [tok, setTok] = useState<Tokenizer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [text, setText] = useState(
    'The catastrophe was subsequently reviewed by Anderson.',
  );
  const [showTrace, setShowTrace] = useState(false);

  useEffect(() => {
    fetch(dataUrl)
      .then((r) => r.json())
      .then((raw: { merges: [number, number, number][] }) => {
        const merges: Merges = new Map();
        const vocab = new Map<number, number[]>();
        for (let i = 0; i < 256; i++) vocab.set(i, [i]);
        raw.merges.forEach(([a, b, id], rank) => {
          merges.set(`${a},${b}`, { rank, id });
          vocab.set(id, [...(vocab.get(a) ?? []), ...(vocab.get(b) ?? [])]);
        });
        setTok({ merges, vocab });
      })
      .catch((e) => setError(String(e)));
  }, [dataUrl]);

  const result = useMemo(
    () => (tok ? encode(text, tok) : null),
    [text, tok],
  );

  if (error) return <p>Could not load the tokenizer: {error}</p>;
  if (!tok || !result) return <p>Loading the trained vocabulary…</p>;

  const chars = [...text].length;
  const ratio = result.tokens.length ? chars / result.tokens.length : 0;

  return (
    <div className="learning-widget">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        spellCheck={false}
        style={{
          width: '100%',
          padding: '0.75rem',
          fontFamily: 'var(--ifm-font-family-monospace)',
          fontSize: 'var(--type-base)',
          borderRadius: 8,
          border: '1px solid var(--ifm-color-emphasis-300)',
          background: 'var(--ifm-background-surface-color)',
          color: 'var(--ifm-font-color-base)',
          resize: 'vertical',
        }}
      />

      <div
        style={{
          display: 'flex',
          gap: '1.5rem',
          margin: '0.75rem 0',
          fontSize: 'var(--type-sm)',
          flexWrap: 'wrap',
        }}
      >
        <span><strong>{chars}</strong> characters</span>
        <span><strong>{result.tokens.length}</strong> tokens</span>
        <span><strong>{ratio.toFixed(2)}</strong> chars/token</span>
        <label style={{ marginLeft: 'auto', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={showTrace}
            onChange={(e) => setShowTrace(e.target.checked)}
          />{' '}
          show merge trace
        </label>
      </div>

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 3,
          padding: '0.75rem',
          borderRadius: 8,
          background: 'var(--ifm-code-background)',
          minHeight: '3rem',
        }}
      >
        {result.tokens.map((t, i) => (
          <span
            key={i}
            title={`id ${t.id}`}
            style={{
              background: PALETTE[i % PALETTE.length],
              color: 'var(--rehearse-ink)',
              padding: '2px 5px',
              borderRadius: 4,
              fontFamily: 'var(--ifm-font-family-monospace)',
              fontSize: 'var(--type-sm)',
              whiteSpace: 'pre',
            }}
          >
            {t.text === ' ' ? '␣' : t.text.replace(/\n/g, '⏎')}
          </span>
        ))}
      </div>

      {showTrace && result.traced.length > 0 && (
        <div style={{ marginTop: '1rem', fontSize: 'var(--type-sm)' }}>
          <p style={{ marginBottom: '0.5rem' }}>
            Merges applied to <code>{result.tracedPiece}</code>, in the order
            they were learned during training:
          </p>
          <ol style={{ fontFamily: 'var(--ifm-font-family-monospace)' }}>
            {result.traced.map((s, i) => (
              <li key={i}>
                merge <code>{s.pair}</code> → {s.result.length} token
                {s.result.length === 1 ? '' : 's'}
              </li>
            ))}
          </ol>
        </div>
      )}

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.75rem' }}>
        Running the actual 16,384-token vocabulary trained in{' '}
        <a href="https://github.com/kleon1024/agi-playground/tree/main/01-language-model/01-tokenizer">
          mission 01 stage 01
        </a>
        . Try a rare word, an emoji, or a misspelling — byte-level BPE has no{' '}
        <code>&lt;UNK&gt;</code>, so nothing is ever unrepresentable, only
        expensive.
      </p>
    </div>
  );
}
