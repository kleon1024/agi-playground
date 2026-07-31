import React, { useState } from 'react';

const CACHE_LEN = 6;

function topLeftAllowed(row: number, col: number): boolean {
  // is_causal=True convention: query row i (0-indexed within the new block)
  // sits at absolute position CACHE_LEN + i; sees keys 0..(CACHE_LEN + i).
  return col <= CACHE_LEN + row;
}

function bottomRightAllowed(row: number, col: number, queryLen: number): boolean {
  // causal_lower_right: query row i sees cached keys 0..CACHE_LEN-1 plus
  // new-block keys 0..i.
  if (col < CACHE_LEN) return true;
  return col - CACHE_LEN <= row;
  void queryLen;
}

export default function DecodeMaskShape(): React.ReactElement {
  const [queryLen, setQueryLen] = useState<1 | 4>(1);
  const totalKeys = CACHE_LEN + queryLen;
  let mismatches = 0;
  const rows = Array.from({ length: queryLen }, (_, row) =>
    Array.from({ length: totalKeys }, (_, col) => {
      const a = topLeftAllowed(row, col);
      const b = bottomRightAllowed(row, col, queryLen);
      if (a !== b) mismatches += 1;
      return { a, b, mismatch: a !== b };
    })
  );
  return (
    <div className="learning-widget">
      <label>
        query length{' '}
        <select value={queryLen} onChange={(e) => setQueryLen(Number(e.target.value) as 1 | 4)}>
          <option value={1}>1 (single-token decode)</option>
          <option value={4}>4 (probe's multi-token query)</option>
        </select>
      </label>
      <p>cache length: {CACHE_LEN}, mismatched cells: <strong>{mismatches}</strong></p>
      <table style={{ borderCollapse: 'collapse', fontSize: 'var(--type-xs)' }}>
        <tbody>
          {rows.map((r, ri) => (
            <tr key={ri}>
              {r.map((cell, ci) => (
                <td
                  key={ci}
                  style={{
                    border: '1px solid var(--rehearse-rule)',
                    padding: '0.2rem 0.35rem',
                    background: cell.mismatch ? 'var(--brand-chart-warning-fill)' : undefined,
                  }}
                  title={`top-left: ${cell.a ? 'allowed' : 'masked'}, bottom-right: ${cell.b ? 'allowed' : 'masked'}`}
                >
                  {cell.mismatch ? '!=' : '='}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ fontSize: 'var(--type-sm)', opacity: 0.75 }}>
        At query length 1 the two conventions agree everywhere (0 mismatches) -- single-token
        decode looks safe. At query length 4 (the probe's actual test) they disagree, which is
        the direct cause of haiku's 1.2e-3/4.2e-2/1.2e-3 measured errors.
      </p>
    </div>
  );
}
