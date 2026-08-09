/**
 * What model size changes about SFT.
 *
 * The main SFT stage ends with one point: an 88M model whose fine-tune
 * changed the form of its output and nothing about what it knows. A single
 * point cannot tell you whether that is what SFT does at every scale or
 * what 88M specifically can and cannot hold. This ladder runs the same
 * recipe at 5M (measured here, 2026-08-05), reads the recorded 88M run
 * (2026-07-28), and extends the axis with dated external results where this
 * repository cannot run (Zhou et al., LIMA, arXiv:2305.11206, 2023).
 *
 * The mechanism is the same at every size: SFT moves the output toward the
 * fine-tuning data's surface, and how far it can move depends on the room
 * the model has — capacity to hold the new surface without destroying the
 * prior, and a prior rich enough to be surfaced.
 */
import React, { useState } from 'react';

interface Rung {
  id: string;
  size: string;
  provenance: string;
  pretraining: string;
  sft: string;
  sample: string;
  verdict: string;
}

const RUNGS: Rung[] = [
  {
    id: '5m',
    size: '5M',
    provenance: 'Measured here — runs/2026-08-05-sft-model-size.md',
    pretraining: '4,941,504 parameters, pretrained on Tiny Shakespeare (~330k tokens)',
    sft: 'Same 9,500 conversations, 357 steps: val 9.5188 to 8.6496 from the pretrained base; 9.7475 to 8.8015 from random init',
    sample: '"dal off a I of the the was and the to not not in that know:,,al"',
    verdict: 'Format does not land. There is not enough capacity to hold the chat template, the dialogue distribution, and fluent English at once — the loss lands where it can, a shallow imitation of the surface, and the residual is degenerate text.',
  },
  {
    id: '88m',
    size: '88M',
    provenance: 'Measured here — runs/2026-07-28-sft-no-robots.md',
    pretraining: '88,197,888 parameters, 3.0B tokens of FineWeb-Edu',
    sft: '9,500 conversations, 3 epochs, 92.5s: val 3.1829 to a best of 2.7828',
    sample: '"Candy, chocolate, and chocolate, are the two popular desserts for children."',
    verdict: 'Format lands, content does not. The model had room for the form or the knowledge and spent the room on form — an answer-shaped sentence with no content, which is what 9.8M tokens of instruction data can and cannot do to a model that saw 3.0B tokens of pretraining.',
  },
  {
    id: '65b',
    size: '65B+',
    provenance: 'External, dated — Zhou et al., LIMA, arXiv:2305.11206 (2023)',
    pretraining: 'Frontier-scale pretraining, a prior rich enough that the knowledge already lives in the base',
    sft: '1,000 curated demonstrations matched far more heavily trained systems on style-following',
    sample: 'Style-following behaviour, not a token-level sample',
    verdict: 'Format is almost free. At this scale SFT is mostly surface — and with the right data it can push new facts in (token-scaled versus fact-scaled SFT data changes whether new facts land, arXiv:2509.16596, 2025), while its format-stabilizing role persists and RL builds on it (SFT Memorizes, RL Generalizes, ICML 2025).',
  },
];

export default function SftSizeLadder(): React.ReactElement {
  const [activeId, setActiveId] = useState('88m');
  const active = RUNGS.find((r) => r.id === activeId) ?? RUNGS[1];

  return (
    <div className="learning-widget">
      <p>
        Three points on the model-size axis. The two small ones are this
        repository's own runs; the large one is a dated published result.
        Select a rung and read what SFT could and could not move there.
      </p>

      <div
        role="group"
        aria-label="Model size"
        style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', margin: '0.9rem 0' }}
      >
        {RUNGS.map((rung) => (
          <button
            key={rung.id}
            type="button"
            aria-pressed={activeId === rung.id}
            onClick={() => setActiveId(rung.id)}
            style={{
              padding: '0.6rem 0.4rem',
              textAlign: 'center',
              background: activeId === rung.id ? 'var(--rehearse-action-soft)' : undefined,
              borderColor: activeId === rung.id ? 'var(--rehearse-action)' : undefined,
            }}
          >
            <strong style={{ display: 'block', fontSize: 'var(--type-base)' }}>{rung.size}</strong>
            <span style={{ fontSize: 'var(--type-xs)', opacity: 0.7 }}>{rung.provenance.includes('external') ? 'external' : 'measured'}</span>
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gap: '0.7rem' }}>
        {[
          ['Provenance', active.provenance],
          ['Pretraining', active.pretraining],
          ['SFT result', active.sft],
          ['Sample output', active.sample],
        ].map(([label, value]) => (
          <div key={label} style={{ border: '1px solid var(--rehearse-rule)', padding: '0.6rem 0.75rem' }}>
            <div style={{ fontSize: 'var(--type-xs)', opacity: 0.65, marginBottom: '0.15rem' }}>{label}</div>
            <div style={{ fontSize: 'var(--type-sm)' }}>{value}</div>
          </div>
        ))}
      </div>

      <p>
        {active.verdict}
      </p>

      <p>
        The two small rungs are not head-to-head — different tokenizer, corpus,
        and device — and the ladder never presents them as such. What the axis
        licenses is the mechanism, not a ranking: SFT moves the surface, and how
        much surface it can move is set by capacity and prior, which is why the
        same recipe produces fragments at 5M, fluent-but-wrong at 88M, and
        near-free formatting at 65B-plus.
      </p>
    </div>
  );
}
