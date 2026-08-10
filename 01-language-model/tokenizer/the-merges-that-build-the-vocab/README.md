---
status: verified
level: applied
base: scratch
label: The merges that build the vocab
verified: 2026-08-06
---

# The merge sequence IS the tokenizer's logic

**Question:** [stage 01's tokenizer](../) trains a 16,384-vocab BPE. This
chapter reads the recorded merge sequence and asks what it shows about
how a vocabulary is actually built.

**Before this:** [stage 01's tokenizer](../) and its recorded BPE run.

## The merges, read

The run ([record](runs/2026-08-06-merge-read.md)) reads the recorded
sequence:

| merge | pair | result | count |
|---:|---|---:|---:|
| 256 | 32, 116 | ' t' | 1,015,622 |
| 257 | 32, 97 | ' a' | 795,862 |
| 258 | 104, 101 | 'he' | 777,146 |
| 1000 | 265, 97 | 'ata' | 5,031 |
| 11000 | 2393, 1435 | 'sequently' | 157 |
| 16000 | 10024, 12303 | ' catastrophe' | 88 |

## Two readings

**Early merges collapse frequent characters and bigrams; late merges keep
rare whole words.** The first merges are space+letter and the most common
bigrams — the vocabulary's foundation. By merge 11,000 the pairs are
word fragments ('sequently'), and by 16,000 entire rare words
('catastrophe'). The merge order is the tokenizer's logic made visible:
frequency decides what gets a token first.

**The sequence is what the 16,384-vocab tokenizer is built from.** Every
merge is a learned decision about which byte pair to collapse next, and
the recorded list is the audit trail of those 16,000 decisions. The
result — 4.497 chars/token on the held-out text — is the compression the
vocabulary buys, and the merge table is what produced it.

## The fix and its trade

The fix is to keep the merge sequence, not just the vocabulary it produces.
The aggregate (4.497 chars/token) is a sum that hides which decisions were
made; the sequence is the audit trail of the 16,000 decisions themselves —
space-plus-letter bigrams at merges 256-258, word fragments by merge 11,000,
whole rare words at 16,000. A vocabulary that ships without its merge record
is a vocabulary whose logic cannot be reviewed, and the failure the record
guards against is the same one the parity chapter catches: two tokenizers
with identical aggregate compression can be built from different decisions,
and only the sequence exposes that.

The trade is vocabulary size against both sides of the ledger at once. A
16,384-vocab BPE merges by frequency, so frequent subwords get tokens first
and rare whole words only when the budget has room — the 4.497 chars/token
is the compression the budget buys, and the embedding rows are the memory
it costs. Going larger buys rare-word coverage and pays in embedding memory
and slower convergence on the long tail; going smaller forces every rare
word through fragments, which is where the number-fragmentation and
byte-fallback edges the tie-break detour measures come from. The sequence
itself is cheap to keep — one log per training run — which is why the record
is a discipline cost, not a compute cost.

## Who owns the loop

- **The tokenizer team** owns the merge record: the sequence is written
  beside the frozen `tokenizer.json` at every training run, so the
  vocabulary's decisions stay reviewable after the corpus changes.
- **The model team** owns the vocabulary-size decision: embedding memory,
  compression, and the rare-word edges are one policy, and it is made
  before training, not after a model shows the symptom.
- **The eval team** owns the edge checks: rare-word coverage and number
  handling are properties of the merge sequence, and the chars/token
  aggregate cannot see them — the boundary suite tests pieces, not
  compression.

## Evidence boundary

The recorded BPE run (10,000 FineWeb-Edu documents, 16,384 vocab, one
sample). It reads that artifact; it does not re-train and the merge
sequence characterizes this corpus.

## Check your mental model

Answer each before opening it.

**1. Why does frequency, not meaning, drive the merges?**

<details>
<summary>Answer</summary>

Because BPE is purely statistical. The algorithm merges the most frequent
byte pair at each step — ' t' and ' a' collapse first because they appear
a million times; 'catastrophe' only becomes a token at merge 16,000
because it is rare. The vocabulary is an optimization of compression, not
a list of words, which is why the merge sequence is the right way to read
it.

</details>

**2. What does 4.497 chars/token actually measure?**

<details>
<summary>Answer</summary>

Compression: on the held-out text, each token represents about 4.5
characters on average. It is the concrete payoff of the 16,384 merges —
the model sees ~4.5 chars per position instead of one. A smaller vocab
would score lower; a larger one would score higher but cost more
embedding memory, which is the trade the vocabulary size encodes.

</details>

## Next

Back to [stage 01](../), or to
[how do you know the fast version learned the same vocabulary](../is-it-the-same-tokenizer/)
which reads the same stage's parity check.
