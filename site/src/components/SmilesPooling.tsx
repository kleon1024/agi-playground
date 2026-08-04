/**
 * Which position a sequence classifier reads its answer from, and what that
 * position has actually seen.
 *
 * `core/smiles_model.py` pools with `x[arange, lengths - 1]` -- one line, easy
 * to write three other ways, and the three other ways fail differently rather
 * than obviously. Causal attention means position i has attended to positions 0
 * through i, so the choice decides how much of the molecule reaches the head,
 * and whether the vector it starts from is the token's own embedding or a
 * padding slot every molecule shares.
 *
 * The example is a real test-split molecule (`CCCC1CCOC(C)S1`, label 0), the
 * tokenizer is character-level, and MAX_LEN is 128 -- all from this stage's own
 * code and data. No accuracy is attached to the alternatives, because only the
 * shipped one was ever trained; what the widget reports is structural.
 */
import React, { useState } from 'react';

const SMILES = 'CCCC1CCOC(C)S1';
const MAX_LEN = 128;
const CHARS = [...SMILES];
const PADS = MAX_LEN - CHARS.length;

type Choice = 'last-real' | 'final-slot' | 'first';

interface Option {
  id: Choice;
  label: string;
  /** Index into the padded sequence. */
  index: number;
  code: string;
  starts: string;
  reads: string;
}

const OPTIONS: Option[] = [
  {
    id: 'last-real',
    label: 'Last real token',
    index: CHARS.length - 1,
    code: 'x[arange, lengths - 1]',
    starts: `the embedding of '${CHARS[CHARS.length - 1]}', the molecule's final character`,
    reads:
      'Every character of the molecule, and nothing else. This is what the stage ships, '
      + 'and it is the only choice whose position means the same thing for a 14-character '
      + 'molecule and a 90-character one.',
  },
  {
    id: 'final-slot',
    label: 'Final slot',
    index: MAX_LEN - 1,
    code: 'x[:, -1]',
    starts: 'the <pad> embedding, which is padding_idx=0 and therefore the zero vector',
    reads:
      'Every character too — causal masking lets a padding position attend backwards like '
      + 'any other. What it loses is the starting point: every molecule begins this position '
      + 'from the same zero vector, so only what attention carries in distinguishes them.',
  },
  {
    id: 'first',
    label: 'First token',
    index: 0,
    code: 'x[:, 0]',
    starts: `the embedding of '${CHARS[0]}', the molecule's first character`,
    reads:
      'One character. Causal attention means position 0 has attended to position 0 and '
      + 'nothing after it, so this pools a representation of the first atom and discards '
      + 'the rest of the molecule.',
  },
];

export default function SmilesPooling(): React.ReactElement {
  const [choice, setChoice] = useState<Choice>('last-real');
  const option = OPTIONS.find((o) => o.id === choice) as Option;
  const realSeen = Math.min(option.index + 1, CHARS.length);

  return (
    <div className="learning-widget">
      <p>
        One real test-split molecule, <code>{SMILES}</code>, tokenized one character
        per token and padded to {MAX_LEN}. The classifier reads its answer from a
        single position. Choose which one, and the strip shades everything that
        position has attended to.
      </p>

      <div className="widget-controls" role="group" aria-label="Which position to pool from">
        {OPTIONS.map((o) => (
          <button
            key={o.id}
            type="button"
            aria-pressed={o.id === choice}
            onClick={() => setChoice(o.id)}
          >
            {o.label}
          </button>
        ))}
      </div>

      <ol className="token-strip" aria-label={`Tokenized ${SMILES}, padded to ${MAX_LEN}`}>
        {CHARS.map((char, i) => (
          <li
            key={`${char}-${i}`}
            data-state={i === option.index ? 'pooled' : i < option.index ? 'attended' : 'idle'}
          >
            {char}
          </li>
        ))}
        <li
          className="token-strip__pad"
          data-state={option.index >= CHARS.length ? 'attended' : 'idle'}
        >
          + {PADS} &lt;pad&gt;
          {option.index === MAX_LEN - 1 && <b aria-hidden="true">pooled</b>}
        </li>
      </ol>

      <div className="objective-readout">
        <div>
          <span>Position pooled</span>
          <strong>{option.index}</strong>
        </div>
        <div>
          <span>Characters it has attended to</span>
          <strong>{realSeen} of {CHARS.length}</strong>
        </div>
        <div>
          <span>In code</span>
          <strong style={{ fontSize: 'var(--type-sm)' }}><code>{option.code}</code></strong>
        </div>
      </div>

      <div className="widget-caption widget-swap" aria-live="polite">
        {OPTIONS.map((o) => (
          <p key={o.id} data-shown={o.id === choice} aria-hidden={o.id !== choice}>
            Starts from {o.starts}. {o.reads}
          </p>
        ))}
      </div>

      <p>
        Two of these three positions have seen the whole molecule, so &ldquo;has it read
        everything?&rdquo; is not the question that separates them. What separates them is
        what the pooled vector starts as and whether that starting point carries
        information — which is why the shipped line indexes by length rather than
        taking the last column of the tensor.
      </p>
    </div>
  );
}
