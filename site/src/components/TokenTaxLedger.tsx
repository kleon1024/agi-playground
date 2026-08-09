/**
 * What the aggregate chars-per-token number cannot see.
 *
 * The tokenizer reports one number — 4.497 characters per token on its
 * English-heavy corpus — and every product decision that consumes tokens
 * treats a token as equal. The per-class ledger from
 * runs/2026-08-08-token-tax.md shows that the aggregate is blind: English
 * costs 0.24 tokens per character, CJK 2.96, emoji 4.00. Move the window
 * size and watch what each class actually fits: a fixed token window holds
 * an order of magnitude less CJK text than English text.
 *
 * The chars-in-window column is arithmetic on the measured rates (window
 * divided by tokens-per-character); the rates themselves are the recorded
 * run's values, measured on the frozen 16,384-id tokenizer.
 */
import React, { useMemo, useState } from 'react';

const CLASSES = [
  { name: 'English prose', rate: 0.24 },
  { name: 'Code', rate: 0.44 },
  { name: 'Phone', rate: 0.54 },
  { name: 'Date', rate: 0.6 },
  { name: 'Big integer', rate: 0.6 },
  { name: 'Decimal', rate: 0.62 },
  { name: 'Accented Latin', rate: 0.72 },
  { name: 'CJK sentence', rate: 2.96 },
  { name: 'Emoji', rate: 4.0 },
];

const WINDOW_MIN = 1024;
const WINDOW_MAX = 16384;
const WINDOW_STEP = 256;

export default function TokenTaxLedger(): React.ReactElement {
  const [windowTokens, setWindowTokens] = useState(4096);

  const rows = useMemo(
    () =>
      CLASSES.map((c) => ({
        ...c,
        chars: Math.round(windowTokens / c.rate),
      })),
    [windowTokens],
  );

  const maxChars = rows[0].chars;
  const englishChars = rows[0].chars;
  const cjk = rows.find((r) => r.name === 'CJK sentence')?.chars ?? 0;
  const emoji = rows.find((r) => r.name === 'Emoji')?.chars ?? 0;

  return (
    <div className="learning-widget">
      <p>
        A fixed token window is not a fixed amount of text. Slide the window
        and watch each class's capacity move — the rates are the measured
        ones, so the shape of this chart is the tokenizer you froze.
      </p>

      <label style={{ display: 'flex', gap: '0.8rem', alignItems: 'center', margin: '0.9rem 0' }}>
        <span style={{ minWidth: '9.5rem' }}>
          context window = <strong>{windowTokens.toLocaleString()}</strong> tokens
        </span>
        <input
          type="range"
          min={WINDOW_MIN}
          max={WINDOW_MAX}
          step={WINDOW_STEP}
          value={windowTokens}
          onChange={(e) => setWindowTokens(Number(e.target.value))}
          style={{ width: '100%', maxWidth: 260 }}
        />
      </label>

      <div style={{ display: 'grid', gap: '0.35rem', margin: '0.9rem 0' }}>
        {rows.map((row) => (
          <div key={row.name} style={{ display: 'grid', gridTemplateColumns: '9rem 1fr 5.5rem', gap: '0.6rem', alignItems: 'center' }}>
            <span style={{ fontSize: 'var(--type-sm)', textAlign: 'right' }}>{row.name}</span>
            <div style={{ background: 'var(--rehearse-rule)', height: 12, borderRadius: 3, position: 'relative' }}>
              <div
                style={{
                  width: `${Math.max((row.chars / maxChars) * 100, 1.5)}%`,
                  height: '100%',
                  background:
                    row.rate > 1.5
                      ? 'var(--brand-chart-danger-fill)'
                      : 'var(--brand-chart-positive-fill)',
                  borderRadius: 3,
                }}
              />
            </div>
            <span style={{ fontSize: 'var(--type-sm)', fontWeight: 600 }}>
              {row.chars.toLocaleString()} chars
            </span>
          </div>
        ))}
      </div>

      <p>
        The window holds {englishChars.toLocaleString()} characters of English
        prose but {cjk.toLocaleString()} of a CJK sentence and {emoji.toLocaleString()}
        of emoji — the 4,096-token window is a 1,382-CJK-character window, and
        token pricing has the same shape: the same product text costs about
        twelve times more in tokens per character for a Chinese user.
      </p>

      <p>
        The aggregate cannot see this because averages hide tails. In the
        mixed-document ledger the same run recorded, CJK is 4.3% of the
        characters but 23.5% of the tokens, emoji 1.1% of the characters but
        7.8% of the tokens — digit, CJK, and emoji runs together are 17% of
        the characters and 47% of the tokens. That is why the ledger is part
        of the freeze decision: the per-class cost is a data-pipeline and
        pricing contract, not a tokenizer footnote.
      </p>
    </div>
  );
}
