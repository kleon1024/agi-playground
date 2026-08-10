---
status: verified
level: applied
base: scratch
label: When the ID is a phrase
verified: 2026-08-07
---

# The ID is a phrase, and the phrase names too much

**Question:** [stage 35's generative retrieval](../) emits document IDs.
This chapter asks what the ID format decides, and answers: an atomic
ID is unambiguous, while a phrase ID reads naturally but can name many
documents at once.

**Before this:** [stage 35 — generative retrieval](../) and its executed
beam decode, and the [ID-space detour](../when-the-id-space-grows/) for
the vocabulary cost that phrase IDs are one answer to.

## The ambiguity, executed

The run ([record](runs/2026-08-07-phrase-id-read.md)) emits four phrases
against a corpus of eight titles and counts how many documents each
names:

| emitted phrase | docs named |
|---|---:|
| search | 5 |
| memory | 5 |
| transformer memory | 1 |
| sparse representations | 1 |

## The reading

The ID format decides how ambiguous a decode can be. The original
Differentiable Search Index (DSI; Tay et al., NeurIPS 2022) assigns one
atomic docid per document, so a correct decode names exactly one
document — but the model must learn to spell arbitrary IDs. Bevilacqua
et al. (NeurIPS 2022) instead make the ID a substring of the document,
so the model emits readable phrases that are easy to generate — and
ambiguous. "search" names five of eight documents in this corpus, so
the decode alone cannot say which one the query meant. The ambiguity is
pushed into a substring lookup that resolves the phrase against the
corpus, which is exactly the compressed full-text index SEAL
reintroduces alongside the autoregressive model. The no-index claim
softens: the index is gone from the scoring path, but a resolution
lookup returns through the back door the moment IDs are human-readable.

## The fix and its trade

The fix is an ID format matched to the decode's strength, with the
ambiguity resolved explicitly. The executed substring count prices the
choice: with phrase IDs, "search" names 5 of 8 documents and "memory"
names 5, while "transformer memory" and "sparse representations" each
name 1 — the decode alone cannot say which document the query meant.
The original DSI (Tay et al., NeurIPS 2022) assigns one atomic docid
per document, so a correct decode names exactly one document — but the
model must learn to spell arbitrary IDs. Bevilacqua et al. (NeurIPS
2022) instead make the ID a substring of the document, easy to generate
and ambiguous.

The trade, named: atomic IDs are unambiguous and hard to spell; phrase
IDs are easy to generate and ambiguous — and the ambiguity is pushed
into a substring lookup that resolves the phrase against the corpus,
which is exactly the compressed full-text index SEAL reintroduces
alongside the autoregressive model. The no-index claim softens: the
index is gone from the scoring path, but a resolution lookup returns
through the back door the moment IDs are human-readable.

## Who owns the loop

- **The generative-model team** owns the ID-format decision and its
  ambiguity measurement over the corpus.
- **The serving team** owns the resolution lookup that phrase IDs
  require, and its latency.
- **The evaluation team** owns the match-distribution read that shows
  how ambiguous a decode is per query class.

## Evidence boundary

The executed substring count over eight hand-built titles (illustrative,
deterministic). It demonstrates the shape; real ambiguity needs the
actual corpus and a measured match distribution over production queries.

## Check your mental model

Answer each before opening it.

**1. Why would a team choose phrase IDs when they are ambiguous?**

<details>
<summary>Answer</summary>

Because the model can emit them. Atomic IDs must be memorized exactly;
a phrase ID is text the model already knows how to produce, so decode
quality improves — the trade that SEAL's experiments show. The cost is
that a readable phrase can match several documents, and the resolution
needs a substring index. The ID format is a decode-quality-versus-
ambiguity decision, not a cosmetic one.

</details>

**2. Where does the index come back in when the ID is a phrase?**

<details>
<summary>Answer</summary>

In the resolution step. The model emits "search", and a compressed
full-text index maps that substring to the five candidate documents;
the candidate that ranks highest in the decode is the answer. The
scoring path has no scan, but the disambiguation path needs a lookup —
the no-index property of generative retrieval survives only while IDs
are atomic.

</details>

## Next

Back to [stage 35](../). The
[hallucination detour](../when-the-generator-hallucinates/) shows what
happens when the decode invents an ID that names nothing at all.
