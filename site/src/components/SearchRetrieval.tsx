import React from 'react';
import ProcessDiagram, { type ProcessStep } from './ProcessDiagram';

const STEPS: ProcessStep[] = [
  {
    id: 'bm25',
    carries: 'doc1 1.9592 top',
    label: 'The lexical index',
    owns: 'BM25 scores documents by IDF times a sublinear term-frequency factor, length-normalized; exact terms and entities rank first.',
    handoff: 'Documents without the exact query words score 0.0000.',
  },
  {
    id: 'gap',
    carries: 'aggregate recall 0.90',
    label: 'The lexical gap',
    owns: 'Across the audit corpus, "cheap headphones" loses d6 (affordable bluetooth earbuds) because it shares no query term and scores 0.0000.',
    handoff: 'A zero-overlap document is cut before ranking — no ranker downstream can recover it.',
  },
  {
    id: 'partial',
    carries: 'one term keeps d7',
    label: 'The partial match',
    owns: 'The grading is visible in the contrast: "running shoes" keeps d7 (sneakers athletic footwear) because one term, "running", still hits.',
    handoff: 'Zero overlap is an absolute miss; partial overlap is a ranking matter.',
  },
  {
    id: 'fix',
    carries: 'hybrid retrieval',
    label: 'The fix',
    owns: 'Lexical for exact terms and entities, dense for meaning, fused into one candidate set — at the price of a dense index and a fusion rule.',
    handoff: 'Widening the retrieval net trades recall for precision the reranker pays downstream.',
  },
];

export default function SearchRetrieval(): React.ReactElement {
  return (
    <ProcessDiagram
      eyebrow="A lexical first stage that dense retrieval has to beat"
      question="Where does the recall loss hide in a lexical index?"
      steps={STEPS}
      loop="BM25 ranks exact terms and entities first, and documents without the query words score 0.0000. Aggregate recall@3 is 0.90, but the cheap-headphones query loses d6 because it shares no query term — cut before ranking, so no ranker downstream can recover it. The partial match keeps d7 via one shared term, so zero overlap is the hard gate, and hybrid retrieval is the fix."
    />
  );
}
