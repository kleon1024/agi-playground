/**
 * Which web-cleaning implementation do you ship?
 *
 * Stage 00 runs the same 40,000-document input through two pipelines: the
 * from-scratch `core/pipeline.py` and datatrove's published FineWeb recipe.
 * The toggle is the ship decision, and every number it flips between is
 * measured in runs/2026-07-26-core-vs-datatrove.md.
 *
 * The first thing to notice is that "faster" and "cleaner" are different
 * axes. Ours keeps 9,184 documents (23.0%) at roughly 2ms/doc; datatrove
 * keeps 5,513 (13.8%) at 25ms/doc, and its extraction alone is 85% of its
 * runtime. The second is that the gap is not fussiness: GopherRepetitionFilter
 * removes 2,803 documents that repeat their own lines and n-grams, and
 * FineWebQualityFilter removes 932 more — failure modes our funnel is
 * structurally blind to, and exactly the documents that teach a model to loop.
 */
import React, { useState } from 'react';

type PipelineId = 'ours' | 'datatrove';

interface Gate {
  label: string;
  inCount: number;
  outCount: number;
  note: string;
}

const OURS: Gate[] = [
  { label: 'HTML responses', inCount: 20000, outCount: 20000, note: 'start' },
  { label: 'Text extraction (regex)', inCount: 20000, outCount: 18210, note: '1,790 pages stripped to under 200 characters of text' },
  { label: 'Language ID (stop-word ratio)', inCount: 18210, outCount: 7348, note: '10,862 removed — the single biggest cut in the funnel' },
  { label: 'Gopher quality rules', inCount: 7348, outCount: 6349, note: '999 removed: low alpha words, too short, mean word length, symbol ratios' },
  { label: 'C4 line filter', inCount: 6349, outCount: 4856, note: '1,493 pages reduced below 50 words after boilerplate lines dropped' },
  { label: 'MinHash dedup', inCount: 4856, outCount: 4592, note: '264 near-duplicates removed within this one file' },
];

const DATATROVE: Gate[] = [
  { label: 'WARC reader', inCount: 40000, outCount: 40000, note: 'start' },
  { label: 'URL filter', inCount: 40000, outCount: 39741, note: '259 removed from a blocklist' },
  { label: 'Trafilatura extraction', inCount: 39741, outCount: 38328, note: '1,413 removed; 25ms/doc — 85% of total runtime' },
  { label: 'Language filter (fastText, 0.65)', inCount: 38328, outCount: 13467, note: '24,861 removed — same dominant cut, different mechanism' },
  { label: 'Gopher repetition filter', inCount: 13467, outCount: 10664, note: '2,803 removed: pages repeating their own lines and n-grams' },
  { label: 'Gopher quality filter', inCount: 10664, outCount: 7129, note: '3,535 removed' },
  { label: 'C4 quality filter', inCount: 7129, outCount: 6445, note: '684 removed' },
  { label: 'FineWeb quality filter', inCount: 6445, outCount: 5513, note: '932 removed: character-duplication, line-punctuation, short-line ratios' },
];

const OUTCOMES = {
  ours: {
    kept: '9,184 (23.0%)',
    chars: '36.4M characters',
    charsPerDoc: '3,968 chars/doc',
    extraction: '~2ms/doc, one core',
    wall: '~80s, 1 core',
  },
  datatrove: {
    kept: '5,513 (13.8%)',
    chars: '21.1M characters',
    charsPerDoc: '3,833 chars/doc',
    extraction: '25ms/doc (85% of runtime)',
    wall: '2m27s, 8 workers',
  },
};

const maxIn = (gates: Gate[]) => Math.max(...gates.map((g) => g.inCount));

export default function ExtractionComparison(): React.ReactElement {
  const [pipeline, setPipeline] = useState<PipelineId>('ours');
  const gates = pipeline === 'ours' ? OURS : DATATROVE;
  const outcome = OUTCOMES[pipeline];

  return (
    <div className="learning-widget">
      <p>
        The same two WARC files, 40,000 HTML responses, run through each
        implementation. Pick the one you would ship and read what it keeps and
        what it costs.
      </p>

      <div
        role="group"
        aria-label="Choose an implementation"
        style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', margin: '0.9rem 0' }}
      >
        {(['ours', 'datatrove'] as PipelineId[]).map((id) => (
          <button
            key={id}
            type="button"
            aria-pressed={pipeline === id}
            onClick={() => setPipeline(id)}
            style={{
              background: pipeline === id ? 'var(--rehearse-action-soft)' : undefined,
              borderColor: pipeline === id ? 'var(--rehearse-action)' : undefined,
            }}
          >
            {id === 'ours' ? 'Our pipeline (core/pipeline.py)' : 'datatrove FineWeb recipe'}
          </button>
        ))}
      </div>

      <ol style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: '0.4rem' }}>
        {gates.map((gate, index) => {
          const width = (gate.outCount / maxIn(gates)) * 100;
          const dropped = gate.inCount - gate.outCount;
          return (
            <li key={gate.label} style={{ fontSize: 'var(--type-sm)' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: '0.8rem',
                  marginBottom: '0.15rem',
                }}
              >
                <span style={{ fontWeight: 600 }}>
                  {index + 1}. {gate.label}
                </span>
                <span>
                  {gate.inCount.toLocaleString()} to {gate.outCount.toLocaleString()}
                  {dropped > 0 ? ` (drop ${dropped.toLocaleString()})` : ''}
                </span>
              </div>
              <div style={{ background: 'var(--rehearse-rule)', height: 6, borderRadius: 3 }}>
                <div
                  style={{
                    width: `${width}%`,
                    height: '100%',
                    background: 'var(--rehearse-action)',
                    borderRadius: 3,
                  }}
                />
              </div>
              <p style={{ margin: '0.15rem 0 0', color: 'var(--rehearse-copy-muted)' }}>{gate.note}</p>
            </li>
          );
        })}
      </ol>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(11rem, 1fr))',
          gap: '0.7rem',
          margin: '1rem 0',
        }}
      >
        {[
          ['Documents kept', outcome.kept],
          ['Text kept', outcome.chars],
          ['Per document', outcome.charsPerDoc],
          ['Extraction cost', outcome.extraction],
          ['Wall clock', outcome.wall],
        ].map(([label, value]) => (
          <div key={label} style={{ border: '1px solid var(--rehearse-rule)', padding: '0.55rem 0.7rem' }}>
            <div style={{ fontSize: 'var(--type-xs)', opacity: 0.65 }}>{label}</div>
            <div style={{ fontWeight: 600 }}>{value}</div>
          </div>
        ))}
      </div>

      <p
        style={{
          marginTop: '0.75rem',
          paddingTop: '0.75rem',
          borderTop: '1px solid var(--rehearse-rule)',
          fontSize: 'var(--type-sm)',
        }}
      >
        {pipeline === 'ours'
          ? 'Fast and 40% too permissive: the funnel is blind to repetition, and the two filters that catch it — GopherRepetitionFilter (2,803 removed) and FineWebQualityFilter (932 removed) — are exactly what a production recipe adds on top of the same funnel. A faster pipeline is not a cleaner one.'
          : 'Stricter by 40% and every extra drop is a named failure mode — but the bill lands on extraction: trafilatura at 25ms/doc is 12x our regex stripper and 85% of total runtime, buying structural awareness (navigation, cookie banners, comment threads) that our extractor leaves in the output.'}
      </p>
    </div>
  );
}
