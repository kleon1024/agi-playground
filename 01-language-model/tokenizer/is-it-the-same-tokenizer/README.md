---
status: verified
level: foundation
base: none
verified: 2026-07-26
label: Is it the same tokenizer
---

# How do you know the fast version learned the same vocabulary?

You are about to make two substitutions, and both of them can be wrong in a way
that stays invisible for hours. The trainer gets an index so it finishes in
minutes instead of ten hours. The encoder gets replaced by a Rust
implementation so encoding the corpus does not take a weekend. Neither
substitution is supposed to change a single token id.

"Supposed to" is not a check. This chapter is the two checks.

**Before this:** [how does text become the numbers a model sees?](../README.md),
through the vocabulary trade. You need to know what BPE merges are and why
16,384 of them exist before it matters whether two programs produce the same
ones.

## Your training run is going to take ten hours

The algorithm as described — and as every explanation of BPE presents it —
recounts every pair in every word on every merge. That is O(vocabulary x
corpus), and `core/bpe.py --naive` is exactly that, kept in the repository
because it is the readable, obviously-correct version.

Measured mid-run, it was taking **2.4 seconds per merge**. At 16,128 merges,
that is roughly **ten hours** for a tokenizer.

The fix follows from noticing what a merge actually changes: merging
`('t','h')` can only affect words that contain `th`. So keep a running pair
count plus a map from each pair to the words containing it, and a merge touches
only what changed. Same run, indexed: **8.8 minutes**.

## The speedup has to produce the identical vocabulary

On a smaller comparison where both implementations finish:

| Implementation | Time | Merges | chars/token |
|---|---|---|---|
| reference (`--naive`) | 21.3s | 1,744 | 3.002 |
| indexed | 0.3s | 1,744 | 3.002 |

Identical merge lists, 71x apart. **Identical** is the load-bearing word — a
speedup that changed the vocabulary would not be a speedup, it would be a
different tokenizer.

One detail makes the comparison possible at all: both break ties by pair
ordering rather than insertion order. Without that they diverge on equal-count
pairs, and you can no longer tell a real bug from an ordering artifact.

## Do not trust your two encoders to agree

Now the second substitution. The pure-Python encoder is slow, so the sensible
move is to export the learned merges into the `tokenizers` format and let the
Rust encoder apply them at speed. The vocabulary stays the one your code
learned; only the encoding is accelerated.

That substitution is safe **only if the two encoders produce identical ids**,
and there is no reason to assume they do — off-by-one merge ordering, different
whitespace pre-tokenization, or a byte-mapping difference would all still
produce plausible-looking output.

So check, rather than assume:

```
documents verified                60
tokens compared               60,978
mismatched documents               0
```

Think about what the alternative costs. A silently diverging export corrupts
every token in the training corpus, and the symptom does not appear until
[stage 02](../../02-pretrain/) as a model that mysteriously will not converge —
hours of GPU time later, with the tokenizer being the last thing anyone
suspects. The assertion is cheap. Finding that bug afterwards is not.

## The fix and its trade

The fix is the two checks, each guarding one substitution. The trainer
substitution is guarded by identical merge lists: the indexed trainer is
only a bookkeeping trick for finding the same most-frequent pair faster, so
a run where the two lists differ by even one merge is a bug, and the
comparison only works because both implementations break ties by pair
ordering. The encoder substitution is guarded by the id-parity check — 60
documents, 60,978 tokens, zero mismatches before the corpus is encoded —
because a silently diverging export corrupts every token in the training
corpus and does not surface until [stage 02](../../02-pretrain/) as a model
that will not converge, hours of GPU later, with the tokenizer the last
thing anyone suspects.

The trade is coverage for confidence. The parity check proves agreement on
60 documents, not on every input, and the naive-versus-indexed comparison
ran at 1,744 merges rather than the full 16,128 because the full naive run
is the ten-hour wall this chapter exists to remove. The check also holds the
tie-break rule fixed, which is its hidden assumption: the moment a library
swap changes that rule, both checks pass on a vocabulary that is still not
the one the previous run learned — [the same corpus, the same rule — why two
vocabularies?](when-the-tie-break-matters/) measures how far that convention
can carry a divergence that neither check sees. The engineering trade is
equally named: the indexed implementation pays for its 71x speedup in
complexity (the pair map must be kept consistent through every merge), and
the parity test pays for its assurance in a small per-export verification
run that a team in a hurry is tempted to skip exactly when it matters most.

## Who owns the loop

- **The tokenizer team** owns the implementation contract: the indexed
  trainer must produce byte-identical merge lists under a pinned tie-break
  rule, and the frozen `tokenizer.json` is the artifact both substitutions
  are checked against.
- **The data-pipeline team** owns the export gate: the id-parity check runs
  before the corpus is encoded, because once ids are in `train.bin` a
  mismatch is a two-day debugging cycle instead of a zero-second test.
- **The model team** owns the symptom and its escalation: a loss curve that
  falls slowly and never gets good is the fingerprint of a diverging
  export, and the first diagnostic is re-running the parity check — not
  blaming the optimizer or the data, which is where the failure is usually
  attributed first.

## Evidence boundary

60 documents and 60,978 tokens show the encoders agree **on this corpus**, not
that they agree on every input. The naive-versus-indexed comparison ran at 1,744
merges, not the full 16,128, because the naive trainer at full size is the
ten-hour run this chapter exists to avoid. Both checks are strong evidence of
equivalence and neither is a proof of it.

The comparison also holds the tie-break rule fixed on purpose. When a team
swaps tokenizer libraries, that rule is not guaranteed to be the same — and
[the same corpus, the same rule — why two vocabularies?](when-the-tie-break-matters/)
trains the same indexed BPE under two deterministic tie rules to show what
actually diverges, which aggregate metric stays blind to it, and where the
difference lands.

## Check your mental model

Answer each before opening it.

**1. The naive and indexed trainers must produce identical merge lists. What
would you conclude from a run where they were 99% identical?**

<details>
<summary>Answer</summary>

That there is a bug, and that the 1% is where it lives — not that the result is
"close enough". The two implementations compute the same function by
construction; the index is only a bookkeeping trick for finding the same
most-frequent pair faster.

The most likely cause is tie-breaking. When two pairs have equal counts, the
heap and the linear scan can reach them in different orders, and one divergent
merge changes every subsequent count. That is why a 99% match is worse news
than it sounds: the lists agree on the frequent merges nobody was worried about
and disagree exactly where the ordering rule is doing work.

</details>

**2. Why does tie-breaking by pair ordering matter, when either rule is
self-consistent?**

<details>
<summary>Answer</summary>

Because self-consistency is not enough to make two implementations comparable.
Insertion order depends on how the data structure happened to enumerate the
corpus, which differs between the naive scan and the indexed heap; pair
ordering depends only on the pair itself, so both implementations reach the
same answer.

The point is diagnostic. With a deterministic rule, a difference between the
two runs means a bug. Without it, a difference might mean a bug or might mean
nothing, and you have destroyed your ability to tell — which is the same reason
seeds are fixed everywhere else in this repository.

</details>

**3. A model trained on this vocabulary converges badly. Name one
tokenizer-side cause and the check from this chapter that would have caught
it.**

<details>
<summary>Answer</summary>

The likeliest cause is a diverging export: the corpus was encoded with the Rust
encoder while the vocabulary was learned by the Python one, and a mismatch in
merge ordering or whitespace pre-tokenization means the ids in `train.bin` do
not mean what the tokenizer says they mean. The model is then learning a
consistent but scrambled language, which produces a loss curve that falls
slowly and never gets good.

The export check catches it: 60 documents, 60,978 tokens, zero mismatches. A
second candidate is a vocabulary-size mismatch — the model configured with
16,384 rows when the corpus contains a separator id of 16,384 — which surfaces
as an index error or a dead embedding row rather than as slow convergence.

</details>

## Next

Return to [freeze it before you go on](../README.md#freeze-it-before-you-go-on).
Both checks passing is what makes the frozen `tokenizer.json` worth freezing;
without them you would be committing a contract you had not verified.
