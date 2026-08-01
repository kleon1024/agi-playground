import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  { id: 'warc', carries: '20,000 HTML responses', label: 'WARC reading', owns: "Pulling HTML responses out of Common Crawl's archive container format.", handoff: 'Raw HTML pages, headers and redirects stripped away.' },
  { id: 'extract', carries: '18,210 documents', label: 'Text extraction', owns: 'Stripping tags, entities, scripts, and navigation out of each page.', handoff: 'Plain text, 91.0% of the raw responses survive.' },
  { id: 'language', carries: '7,348 documents', label: 'Language ID', owns: 'Keeping English via a stop-word ratio.', handoff: 'The single biggest cut in the funnel — 10,862 documents removed, more than every quality heuristic combined.' },
  { id: 'gopher', carries: '6,349 documents', label: 'Gopher quality', owns: 'Length, mean word length, symbol ratios, bullet and ellipsis ratios, stop-word presence.', handoff: 'Keyword stuffing, navigation dumps, and link farms removed.' },
  { id: 'c4', carries: '4,856 documents', label: 'C4 line filter', owns: 'Dropping boilerplate lines while keeping sentences.', handoff: 'A document that reads as prose, not menu items and calls to action.' },
  { id: 'dedup', carries: '4,592 documents', label: 'MinHash dedup', owns: 'Near-duplicate detection via LSH banding and union-find.', handoff: '23.0% of the original 20,000 responses, kept as training text.' },
];

export default function CorpusCleaningPipeline(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="One WARC file, six gates"
      question="Which gate does a document actually die at, and why?"
      steps={STEPS}
      loop="Run a second, disjoint WARC file through the same six gates and the funnel lands within a point or two of this one — the shape is a property of Common Crawl at this vintage, not this particular sample. Deduplication looks cheapest here (5%) precisely because 20,000 documents are compared only against each other; a full crawl's repetition lives between shards, which is why production dedup runs as a distributed job instead of one pipeline pass."
    />
  );
}
