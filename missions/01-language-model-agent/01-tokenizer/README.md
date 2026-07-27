---
status: verified
base: none
verified: 2026-07-26
---

> **[Read this online](https://rehearse.maestro.onl/playground/missions/01-language-model-agent/01-tokenizer)** — type text into the tokenizer and watch these merges fire in order.

# Stage 01 — Tokenizer

**Goal:** turn the corpus into integers, using a vocabulary you trained
yourself, and prove your encoder agrees exactly with the production one.

A tokenizer is the model's entire interface to language. Get it wrong and every
downstream number is quietly wrong with it — a model cannot learn a distinction
its tokenizer erases, and it pays context length for every distinction the
tokenizer makes needlessly.

## What you build

`core/bpe.py` — byte-level BPE, trained from scratch, in two implementations
that produce identical output:

- **the reference** (`--naive`): recount every pair, every merge. This is how
  BPE is explained, and it is correct.
- **the indexed version** (default): the same algorithm with a pair → words
  index and a lazy heap, because a merge only changes the words containing the
  merged pair.

`prod/hf_tokenizer.py` — trains the same thing with HuggingFace `tokenizers`
for comparison, and exports our learned merges into that format so the Rust
encoder can apply *our* vocabulary at speed.

**Byte-level** matters: with a vocabulary built over the 256 byte values, every
possible string is representable and there is no `<UNK>`, ever. A Chinese
character, an emoji, or a corrupt byte all decompose into byte tokens the model
has seen. The worst case is expensive, never impossible.

## What we measured

Trained on 10,000 FineWeb-Edu documents — 9,025,172 words, 252,259 unique
(a 36× collapse, which is what makes pure-Python training feasible at all):

```
vocabulary          16,384
merges learned      16,128
training time        529.8s   (indexed)
chars/token           4.497
round-trip            ok
```

Compression is the number that matters. At **4.497 characters per token**, the
same text costs 4.5× fewer positions than the character-level tokenizer in
[the foundations lesson](../../../foundations/01-first-training-loop/). Context
length, attention cost, and training compute all scale with token count, so
this is a 4.5× discount on all three, bought once.

First inspect the artifact the next stage will consume. Type text below to see
the trained 16,384-token vocabulary turn it into stable IDs and measure its
compression. Then use the merge stepper to see how that vocabulary was learned.

<!-- interactive: TokenizerPlayground -->

The artifact view tells you what the finished vocabulary does, but not how it
was produced. Now reduce the merge count, advance it slowly, and identify the
point where recurring byte pairs become reusable language fragments.

<!-- interactive: BPEMergeStepper -->

### The index is worth 71×

Same corpus, same vocabulary target, same tie-breaking:

| Implementation | Time | Merges | chars/token |
|---|---|---|---|
| reference (`--naive`) | 21.3s | 1,744 | 3.002 |
| indexed | 0.3s | 1,744 | 3.002 |

**Identical merge lists**, 71× apart. The reference recounts every pair in every
word on every merge — O(vocab × corpus). The indexed version keeps a running
count plus a map from each pair to the words containing it, so a merge touches
only what changed.

That gap is not academic. At the naive rate, the 16k vocabulary above was
measured mid-run at 2.4 seconds per merge — **roughly ten hours**. Indexed, it
took **8.8 minutes**.

One detail makes the comparison possible: both break ties by pair ordering
rather than insertion order. Without that they diverge on equal-count pairs, and
you cannot tell a real bug from an ordering artifact.

### The export is verified, not assumed

Our pure-Python encoder is slow; the Rust one is not. So we export our merges
into the `tokenizers` format and let it encode the corpus — the vocabulary stays
the one our code learned, and only the encoding is accelerated.

That substitution is safe only if the two encoders agree exactly:

```
documents verified                60
tokens compared               60,978
mismatched documents               0
export verified: identical ids on every document.
```

A silently-diverging export would corrupt every token in the training corpus and
surface only as a model that mysteriously fails to converge, hours later. The
assertion is cheap; finding that bug afterwards is not.

## Reproducing

```bash
# train (indexed by default; --checkpoint makes it resumable)
python core/bpe.py train <corpus-dir> --vocab-size 16384 --docs 10000 \
    --out tokenizer.json --checkpoint tokenizer.ckpt.json

# see what the naive version costs
python core/bpe.py train <corpus-dir> --vocab-size 2000 --docs 500 --naive

# export to the fast encoder and prove the ids match
python prod/hf_tokenizer.py export tokenizer.json tokenizer_hf.json \
    --corpus <corpus-dir>
```

The trained vocabulary is committed as [`tokenizer.json`](tokenizer.json) so the
next stage is reproducible without retraining. Details in [`runs/`](runs/).

## Exercises

1. **Watch the vocabulary learn English.** The first merges are `' t'`, `' a'`,
   `'he'`, `'in'` — pure bigram frequency. By merge 11,000 they are
   `'sequently'`, `' Anderson'`, `' catastrophe'`. Plot merge index against
   token length.
2. **Find the compression knee.** Train at 4k, 8k, 16k, 32k and plot
   chars/token. It flattens; the embedding table does not.
3. **Break the round-trip.** Feed text containing byte sequences that are not
   valid UTF-8. Byte-level BPE should survive it — confirm it does.
4. **Measure fertility per language.** Encode equivalent English and Chinese
   text. An English-trained vocabulary is far less efficient on Chinese, which
   is why multilingual models train multilingual tokenizers.
5. **Profile the index.** As the vocabulary grows, which dominates — heap
   operations or word rewriting?

## Next

[Stage 02 — pretrain](../02-pretrain/): the model that consumes these tokens.
Note that the vocabulary needs one id more than it has tokens, for the document
separator, and that padding it to a multiple of 128 is nearly free.
