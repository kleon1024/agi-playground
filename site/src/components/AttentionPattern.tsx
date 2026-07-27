/**
 * Causal attention, computed live on whatever you type.
 *
 * Two things are hard to convey in prose and obvious in a picture: that the
 * mask makes the matrix strictly lower-triangular — every token sees only its
 * past — and that softmax is applied per row, so each row sums to one no matter
 * how many positions it can reach. The first token has exactly one option and
 * therefore always attends to itself with weight 1.
 *
 * Embeddings here are deterministic pseudo-random vectors rather than a trained
 * model's, so the pattern shows the mechanism, not learned linguistic
 * structure. Trained heads develop recognisable habits — previous-token,
 * delimiter, induction — but that belongs to a lesson with real weights.
 */
import React, { useMemo, useState } from 'react';

function hash(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function embed(token: string, dim: number): number[] {
  const v: number[] = [];
  let seed = hash(token);
  for (let i = 0; i < dim; i++) {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    v.push((seed / 4294967296) * 2 - 1);
  }
  const norm = Math.hypot(...v);
  return v.map((x) => x / norm);
}

export default function AttentionPattern(): React.ReactElement {
  const [text, setText] = useState('the cat sat on the mat because it was warm');
  const [scaled, setScaled] = useState(true);
  const [dim] = useState(32);

  const { tokens, weights } = useMemo(() => {
    const toks = text.trim().split(/\s+/).filter(Boolean).slice(0, 14);
    const vecs = toks.map((t) => embed(t.toLowerCase(), dim));
    const w: number[][] = [];
    for (let i = 0; i < toks.length; i++) {
      const scores: number[] = [];
      for (let j = 0; j < toks.length; j++) {
        if (j > i) {
          scores.push(-Infinity); // causal mask: the future is unavailable
        } else {
          const dot = vecs[i].reduce((a, x, k) => a + x * vecs[j][k], 0) * dim;
          scores.push(scaled ? dot / Math.sqrt(dim) : dot);
        }
      }
      const max = Math.max(...scores.filter((x) => isFinite(x)));
      const exp = scores.map((x) => (isFinite(x) ? Math.exp(x - max) : 0));
      const sum = exp.reduce((a, b) => a + b, 0);
      w.push(exp.map((x) => x / sum));
    }
    return { tokens: toks, weights: w };
  }, [text, scaled, dim]);

  const cell = Math.max(18, Math.min(34, Math.floor(420 / Math.max(tokens.length, 1))));

  return (
    <div className="learning-widget">
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        spellCheck={false}
        style={{
          width: '100%', padding: '0.6rem', borderRadius: 8,
          border: '1px solid var(--ifm-color-emphasis-300)',
          background: 'var(--ifm-background-surface-color)',
          color: 'var(--ifm-font-color-base)',
          fontFamily: 'var(--ifm-font-family-monospace)', fontSize: 'var(--type-sm)',
        }}
      />
      <label style={{ display: 'inline-block', margin: '0.6rem 0', cursor: 'pointer', fontSize: 'var(--type-sm)' }}>
        <input type="checkbox" checked={scaled} onChange={(e) => setScaled(e.target.checked)} />{' '}
        divide by √d<sub>k</sub>
      </label>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse', fontSize: 'var(--type-xs)' }}>
          <tbody>
            {weights.map((row, i) => (
              <tr key={i}>
                <td style={{ paddingRight: 6, textAlign: 'right', whiteSpace: 'nowrap', opacity: 0.7 }}>
                  {tokens[i]}
                </td>
                {row.map((w, j) => (
                  <td
                    key={j}
                    title={`${tokens[i]} → ${tokens[j]}: ${w.toFixed(3)}`}
                    style={{
                      width: cell, height: cell,
                      background: j > i
                        ? 'transparent'
                        : `color-mix(in srgb, var(--brand-chart-action) ${Math.min(w * 160, 100)}%, var(--rehearse-surface))`,
                      border: '1px solid var(--ifm-color-emphasis-200)',
                      transition: 'background 160ms',
                    }}
                  />
                ))}
              </tr>
            ))}
            <tr>
              <td />
              {tokens.map((t, j) => (
                <td key={j} style={{
                  fontSize: 'var(--type-xs)', opacity: 0.6, verticalAlign: 'top',
                  writingMode: 'vertical-rl', height: 54, paddingTop: 3,
                }}>{t}</td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75, marginTop: '0.6rem' }}>
        Rows are queries, columns are keys. The blank upper triangle is the
        causal mask — position <em>i</em> cannot see position <em>j &gt; i</em>,
        which is what lets one forward pass supply a training signal at every
        position without leaking the answer. Each row sums to 1, so the first
        token always attends fully to itself. Turn off the √d<sub>k</sub>
        division and watch rows collapse onto a single bright cell.
      </p>
    </div>
  );
}
