---
status: verified
level: foundation
base: none
verified: 2026-07-26
---

> **[Read this online](https://rehearse.maestro.onl/playground/missions/01-language-model-agent/01-tokenizer)** — type text into the tokenizer and watch these merges fire in order.

# How does text become the numbers a model sees?

You have a folder of cleaned text from [stage 00](../00-corpus/). A neural
network takes vectors, not strings, so something has to turn "What causes
seasons on Earth?" into a list of integers. That translator is the tokenizer,
and by the end of this chapter you will have trained one, know what its
vocabulary size costs you, and be able to prove it does not corrupt your corpus.

Start by making the choice yourself. There are two obvious ways to do it, and
walking into both dead ends is the fastest way to understand why the real answer
looks so strange.

## Try the two obvious answers first

**One id per character.** Simple, and nothing can break it — every string is
representable. The problem is length. Every model cost you care about scales
with the number of tokens: attention is quadratic in sequence length, and your
compute budget is spent per token. Spelling out `catastrophe` as twelve
positions means paying twelve times to say one thing.

**One id per word.** Far shorter sequences. But now decide what happens when the
model meets `catastrophes`, or `Anderson`, or an emoji, or a byte sequence that
is not valid UTF-8. You need an `<UNK>` token, and every distinct word you did
not anticipate collapses into it — **a model cannot learn a distinction its
tokenizer has already erased.** Your vocabulary also becomes unbounded: this
chapter's corpus has 252,259 unique words in 9,025,172 total, and an embedding
row for each is most of a small model.

So one is too long and the other is lossy. What you want is a vocabulary that
spends short ids on frequent things and can still spell out anything at all.

## Build the vocabulary out of what the corpus repeats

Byte-pair encoding gets there by starting at the bottom and merging upward.
Begin with the 256 byte values — that alone guarantees every possible string is
representable, so there is never an `<UNK>` — then repeatedly find the most
frequent adjacent pair in the corpus and add it to the vocabulary as one new
token. Do that 16,128 times and you have 16,384 tokens.

Nothing linguistic is supplied. Word shapes appear because frequent byte pairs
keep occurring together, which you can watch happen:

<!-- interactive: BPEMergeStepper -->

Reduce the merge count to a few hundred, then advance slowly. The first merges
are `' t'`, `' a'`, `'he'`, `'in'` — pure bigram frequency, no notion of words.
By merge 11,000 the vocabulary is learning `'sequently'`, `' Anderson'`,
`' catastrophe'`. Watch where the useful merges stop arriving; that flattening
is the whole argument about vocabulary size, and you will meet it again in a
moment.

`core/bpe.py` implements this, and [`prod/hf_tokenizer.py`](prod/hf_tokenizer.py)
trains the same thing with HuggingFace `tokenizers` for comparison.

## What the vocabulary bought, and what it cost

Trained on 10,000 FineWeb-Edu documents, the result is **4.497 characters per
token**. Against the character-level tokenizer in
[foundations](../../../foundations/01-first-training-loop/), the same text now
costs 4.5x fewer positions — and since context length, attention cost, and
training compute all scale with token count, that is a 4.5x discount on all
three, bought once, here.

The cost is on the other side of the ledger. Every token needs an embedding row
and an output projection column, so a bigger vocabulary means more parameters
and fewer examples per rare token. That is the trade the merge stepper's
flattening curve is showing you: past the knee, more vocabulary buys very little
compression and keeps charging full price in parameters.

Type your own text below and watch it split. Try a word you invented, a Chinese
sentence, an emoji — all of them encode, because the byte floor means the worst
case is *expensive*, never *impossible*.

<!-- interactive: TokenizerPlayground -->

## Your training run is going to take ten hours

Now run it, and hit the wall this chapter exists to warn you about.

The algorithm as described — and as every explanation of BPE presents it —
recounts every pair in every word on every merge. That is O(vocabulary x corpus),
and `core/bpe.py --naive` is exactly that, kept in the repository because it is
the readable, obviously-correct version.

Measured mid-run, it was taking **2.4 seconds per merge**. At 16,128 merges,
that is roughly **ten hours** for a tokenizer.

The fix follows from noticing what a merge actually changes: merging `('t','h')`
can only affect words that contain `th`. So keep a running pair count plus a map
from each pair to the words containing it, and a merge touches only what
changed. Same run, indexed: **8.8 minutes**.

On a smaller comparison where both finish, the two implementations agree
exactly:

| Implementation | Time | Merges | chars/token |
|---|---|---|---|
| reference (`--naive`) | 21.3s | 1,744 | 3.002 |
| indexed | 0.3s | 1,744 | 3.002 |

Identical merge lists, 71x apart. Identical is the load-bearing word — a
speedup that changed the vocabulary would not be a speedup, it would be a
different tokenizer. One detail makes the comparison possible at all: both
break ties by pair ordering rather than insertion order. Without that they
diverge on equal-count pairs, and you can no longer tell a real bug from an
ordering artifact.

## Do not trust your two encoders to agree

You now have a problem you did not ask for. The pure-Python encoder is slow, so
the sensible move is to export the learned merges into the `tokenizers` format
and let the Rust encoder apply them at speed. The vocabulary stays the one your
code learned; only the encoding is accelerated.

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
every token in the training corpus, and the symptom does not appear until stage
02 as a model that mysteriously will not converge — hours of GPU time later,
with the tokenizer being the last thing anyone suspects. The assertion is cheap.
Finding that bug afterwards is not.

This is also the chapter's evidence boundary: 60 documents and 60,978 tokens
show the encoders agree on this corpus, not that they agree on every input.

## Freeze it before you go on

The tokenizer is now part of the model's contract. Changing it after stage 02
changes what every id means, which invalidates the embedding table and every
checkpoint trained against it. So it is committed as
[`tokenizer.json`](tokenizer.json), and stage 02 loads that file rather than
retraining.

```bash
# train (indexed by default; --checkpoint makes it resumable)
python core/bpe.py train <corpus-dir> --vocab-size 16384 --docs 10000 \
    --out tokenizer.json --checkpoint tokenizer.ckpt.json

# see for yourself what the naive version costs
python core/bpe.py train <corpus-dir> --vocab-size 2000 --docs 500 --naive

# export to the fast encoder and prove the ids match
python prod/hf_tokenizer.py export tokenizer.json tokenizer_hf.json \
    --corpus <corpus-dir>
```

Exact commands, hardware, and wall-clock are in [`runs/`](runs/).

## Check your mental model

Answer each before opening it.

**1. Byte-level BPE has no `<UNK>`. What happens instead when it meets an emoji,
and why is that "expensive but not impossible"?**

<details>
<summary>Answer</summary>

The emoji decomposes into the byte tokens that spell it in UTF-8 — usually four
of them, none of which the vocabulary merged because emoji were too rare in
FineWeb-Edu to become frequent pairs. So it costs four positions instead of one.

That is the whole difference between expensive and impossible. A word-level
tokenizer maps it to `<UNK>`, and every distinct unknown becomes the *same*
token, so the model cannot tell two of them apart no matter how much data you
give it. Here the model sees the actual bytes, and can in principle learn from
them; it is simply paying more context to do so.

</details>

**2. You double the vocabulary and chars/token barely improves. Which side of the
trade got worse, and by how much?**

<details>
<summary>Answer</summary>

The parameter side, and it worsened in proportion — doubling the vocabulary
doubles both the embedding table and the tied output projection, which at
`d_model = 768` is `2 x 16,384 x 768` growing to `2 x 32,768 x 768`.

The compression side gained almost nothing, because you are past the knee the
merge stepper shows: the remaining merges are rare whole words that appear in a
small fraction of documents. You also made every one of those new tokens rarer,
so each gets fewer training examples. Paying twice for less.

</details>

**3. The naive and indexed trainers must produce identical merge lists. What
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

**4. Why does tie-breaking by pair ordering matter, when either rule is
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

**5. A model trained on this vocabulary converges badly. Name one tokenizer-side
cause and the check from this chapter that would have caught it.**

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

[Stage 02 — pretrain](../02-pretrain/) builds the model that consumes these
tokens. Take two things with you: the vocabulary needs one id more than it has
tokens, for the document separator, and padding that count up to a multiple of
128 is nearly free while making every matrix multiplication faster.
