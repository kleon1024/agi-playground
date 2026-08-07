---
status: draft
level: applied
---

# The search track

Search is the same loop as recommendation with one input changed: instead of
ranking with no query, the system ranks with an explicit query. That changes
what the first stages must decide — the query itself has to be understood
before anything can be retrieved — and it changes the evaluation: relevance to
the query replaces the implicit engagement objective, and NDCG and MRR replace
the click-based metrics.

## The build track (stages 10-13)

| Stage | What it decides | Evidence |
|---|---|---|
| [`10-query-understanding`](10-query-understanding/) | The key space retrieval must serve | [verified](10-query-understanding/runs/) |
| [`11-search-retrieval`](11-search-retrieval/) | The lexical index, and the vocabulary-mismatch gap | [verified](11-search-retrieval/runs/) |
| [`12-search-ranking`](12-search-ranking/) | Pointwise vs pairwise over the candidate set | [verified](12-search-ranking/runs/) |
| [`13-search-evaluation`](13-search-evaluation/) | NDCG@k and MRR, and their blind spots | [verified](13-search-evaluation/runs/) |

## The advanced track (stages 19-24)

| Stage | What it decides | Evidence |
|---|---|---|
| [`19-query-expansion`](19-query-expansion/) | Query correction as retrieval pre-processing | [verified](19-query-expansion/runs/) |
| [`20-dense-retrieval`](20-dense-retrieval/) | The two-tower index that closes the mismatch gap | [verified](20-dense-retrieval/runs/) |
| [`21-hybrid-fusion`](21-hybrid-fusion/) | Keeping the union when lexical and dense disagree | [verified](21-hybrid-fusion/runs/) |
| [`22-reranking`](22-reranking/) | The second ranker, inside its latency split | [verified](22-reranking/runs/) |
| [`23-personalized-search`](23-personalized-search/) | The query with a user attached | [verified](23-personalized-search/runs/) |
| [`24-search-measurement`](24-search-measurement/) | The zero-result rate and the coverage signal | [verified](24-search-measurement/runs/) |

## The frontier track (stages 35-37)

| Stage | What it decides | Evidence |
|---|---|---|
| [`35-generative-retrieval`](35-generative-retrieval/) | Retrieval as a decode with a recall curve | [verified](35-generative-retrieval/runs/) |
| [`36-conversational-search`](36-conversational-search/) | Session context as the resolution signal | [verified](36-conversational-search/runs/) |
| [`37-llm-query-understanding`](37-llm-query-understanding/) | Intent-slot parsing with a confidence floor | [verified](37-llm-query-understanding/runs/) |
