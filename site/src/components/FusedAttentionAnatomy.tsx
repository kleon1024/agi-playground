/**
 * The fused-attention mask, drawn as four quadrants in one block.
 *
 * Mission 05's vision pathway has no cross-attention module: 64 vision
 * tokens are concatenated in front of the text into one sequence, and a
 * single shared FusedAttention block reads the whole thing. The mask has
 * four quadrants — vision->vision bidirectional, vision->text blocked,
 * text->vision full, text->text causal. The toggle changes the one
 * variable the mission's own ablation isolates (use_vision), and the
 * parameter delta is the recorded stage-01 total (732,928 vs 718,464).
 */
import React, { useMemo, useState } from 'react';

const QUADRANTS = [
  { row: 'vision -> vision', col: 0, label: 'bidirectional', note: 'vision tokens see each other' },
  { row: 'vision -> text', col: 1, label: 'blocked', note: 'vision never writes into text' },
  { row: 'text -> vision', col: 2, label: 'full', note: 'every text position sees the whole image' },
  { row: 'text -> text', col: 3, label: 'causal', note: 'text stays a language model' },
];

const MEASURED = { vision: 732_928, textOnly: 718_464 };

export default function FusedAttentionAnatomy(): React.ReactElement {
  const [useVision, setUseVision] = useState(true);
  const params = useVision ? MEASURED.vision : MEASURED.textOnly;
  const delta = MEASURED.vision - MEASURED.textOnly;

  const grid = useMemo(
    () => (
      <div
        role="img"
        aria-label="Fused attention mask quadrants"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '0.4rem',
          margin: '1rem 0',
        }}
      >
        {QUADRANTS.map((q) => (
          <div
            key={q.row}
            style={{
              border: '1px solid var(--rehearse-rule)',
              padding: '0.5rem',
              background: 'var(--rehearse-paper)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: 'var(--type-xs)' }}>{q.row}</div>
            <strong>{q.label}</strong>
            <div style={{ fontSize: 'var(--type-xs)', color: 'var(--rehearse-copy-muted)' }}>
              {q.note}
            </div>
          </div>
        ))}
      </div>
    ),
    [],
  );

  return (
    <div className="learning-widget">
      <label style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <span>Vision pathway</span>
        <button type="button" onClick={() => setUseVision((v) => !v)}>
          {useVision ? 'on (measured 732,928 params)' : 'off (text-only 718,464)'}
        </button>
      </label>
      <p style={{ margin: '0.5rem 0' }}>
        64 vision tokens concatenated in front of the text; one shared{' '}
        <code>FusedAttention</code> block reads the whole sequence.
      </p>
      {grid}
      <p>
        The entire cost of sight is <strong>+{delta.toLocaleString()}</strong>{' '}
        parameters — the patch projection plus the position table. Nothing else
        changed from mission 01&apos;s decoder, which is the reuse claim mission
        05 exists to test. Current: <strong>{params.toLocaleString()}</strong>.
      </p>
    </div>
  );
}
