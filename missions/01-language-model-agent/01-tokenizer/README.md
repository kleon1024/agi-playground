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

## Two substitutions you have to verify

Now run it, and hit the wall. The algorithm as described recounts every pair in
every word on every merge, which measured out at **2.4 seconds per merge** —
roughly ten hours for one tokenizer. So the trainer gets an index and finishes
in 8.8 minutes, and the slow Python encoder gets replaced by the Rust one from
`tokenizers` so encoding the corpus does not take a weekend.

Neither substitution is supposed to change a single token id, and "supposed to"
is not a check.
[Is it the same tokenizer?](is-it-the-same-tokenizer/) is the two checks: the
merge lists compared naive against indexed at 71x apart, the tie-breaking rule
that makes that comparison mean anything, and the 60,978-token export parity
run. Read it before freezing anything, because a diverging export does not
surface until stage 02, as a model that will not converge for reasons nobody
attributes to the tokenizer.

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

**3. The vocabulary has no `<UNK>`, so nothing is unrepresentable. Why is
`--vocab-size` still one of the most consequential numbers in this repository?**

<details>
<summary>Answer</summary>

Because it is frozen into the model's contract. Every id the tokenizer emits
needs an embedding row and a tied output column, so the number chosen here
fixes 14.4% of the 88M model's parameters before any architecture decision is
made — and changing it after stage 02 invalidates every checkpoint trained
against it.

It also fixes sequence length, and therefore attention cost and training
compute, for the entire mission. The absence of `<UNK>` removes the *failure*
mode; it does not remove the *cost* the number controls.

</details>

## Next

[Stage 02 — pretrain](../02-pretrain/) builds the model that consumes these
tokens. Take two things with you: the vocabulary needs one id more than it has
tokens, for the document separator, and padding that count up to a multiple of
128 is nearly free while making every matrix multiplication faster.
