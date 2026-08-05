# Run — SFT at two 5M-arm settings, against the recorded 88M anchor

**Date:** 2026-08-05
**Hardware:** macOS 15.6.1, MacBookPro18,3 (Apple M1 Pro, arm64). MPS device
(fp32 — the bf16 autocast in `core/sft.py` is CUDA-gated); CPU for
tokenization.
**Software:** Python 3.11.14; torch 2.13.0; `tokenizers` via uv ephemeral
environment; the repo's own `core/` pipeline unchanged except model-size flags.
**Cost:** \$0 (local lane).

## Purpose

The main SFT stage (recorded 2026-07-28) shows an 88M model whose SFT changed
the *form* of its output and nothing about what it knows. This run asks the
next question: does SFT's effect change with model size? It trains a ~5M base
on Tiny Shakespeare (the same corpus `foundations/01-first-training-loop`
uses), then runs the exact same SFT recipe (`core/sft.py`) from that base and
from random initialization, so the size axis has a measured low end next to
the recorded 88M point.

## Tokenization

```bash
uv run --with tokenizers python ../../01-tokenizer/prod/hf_tokenizer.py export \
    ../../01-tokenizer/tokenizer.json /tmp/shakespeare/tok.json \
    --corpus /tmp/shakespeare/corpus.jsonl.gz --verify-docs 1
uv run --with tokenizers python runs/tokenize_shakespeare.py \
    /tmp/shakespeare/input.txt /tmp/shakespeare/tok.json \
    --out-dir /tmp/shakespeare/tokens --val-tokens 30000
```

Export verified identical ids on the sample document (1,447 tokens, 0
mismatches). Tiny Shakespeare tokenizes to **32,777 documents, 363,501 tokens**
(30,004 reserved as a val prefix).

## Pretraining the ~5M base

```bash
uv run --group torch python ../../02-pretrain/core/train.py \
    --data /tmp/shakespeare/tokens --out /tmp/shakespeare/base \
    --tokens 6e6 --device mps --batch 16 --grad-accum 8 --lr 6e-4 \
    --eval-every 500 --checkpoint-every 5000 \
    --n-layer 4 --n-head 4 --n-kv-head 4 --d-model 192 --d-ff 512 --block-size 1024
```

Architecture: **4,941,504 params** (embedding tied with head, 4 GQA layers).
45 steps at 131,072 tokens/step (18 epochs over the corpus), **done in 0.09h**.
`history.json` records only step 0 (val 9.7423) because `--eval-every 500`
never fired again; the end-of-run checkpoint was saved.

## The two SFT arms

```bash
uv run --group torch --with datasets python ../../03-sft/core/sft.py train \
    --tokenizer /tmp/shakespeare/tok.json \
    --init-checkpoint /tmp/shakespeare/base/ckpt.pt \
    --out /tmp/shakespeare/sft-pretrained \
    --dataset HuggingFaceH4/no_robots --epochs 3 \
    --device mps --block-size 256 --batch 8 --grad-accum 4 --lr 2e-5 \
    --eval-every 100 --checkpoint-every 200 \
    --n-layer 4 --n-head 4 --n-kv-head 4 --d-model 192 --d-ff 512

uv run --group torch --with datasets python ../../03-sft/core/sft.py train \
    --tokenizer /tmp/shakespeare/tok.json \
    --init-checkpoint /tmp/shakespeare/rand/ckpt.pt \
    --out /tmp/shakespeare/sft-rand \
    --dataset HuggingFaceH4/no_robots --epochs 3 \
    --device mps --block-size 256 --batch 8 --grad-accum 4 --lr 2e-5 \
    --eval-every 100 --checkpoint-every 200 \
    --n-layer 4 --n-head 4 --n-kv-head 4 --d-model 192 --d-ff 512
```

`runs/init_random_ckpt.py` wrote the random-init checkpoint (same architecture,
`tokens_seen` absent, so SFT reports zero pretraining tokens). Both arms: 3,838
packed blocks of 257 (73.8% real tokens), 357 optimizer steps, same data, same
recipe, same budget — only the starting weights differ.

| step | pretrained-base SFT val | random-init SFT val |
|---:|---:|---:|
| 0 | 9.5188 | 9.7475 |
| 100 | 9.0501 | 9.2033 |
| 200 | 8.7736 | 8.9272 |
| 300 | 8.6496 | 8.8015 |

Both finished in 0.03h at ~29k tok/s, MFU 0.6% (MPS fp32).

## Samples, identical prompt, temperature 0.8 / top-k 50 (sample defaults)

`core/sft.py sample`, prompt "What causes seasons on Earth?", 100 new tokens:

**base (before SFT):**
```
 Discovery kilomet forces-est mac mac acquire spir unfortunately Find involoppoppgramgramPeople Nat Ath Die Die pick pick abundance allowingHz-life acquire acquire acquire hungry hungryickededing mere resolve sixty sixtyusesuses Max preparing dietary temperateengtherenceerence Seattle publishedonn hungryicked instancesongPeople invisible Northern tracks Narast Shel Shel Es Structure Legisl Workers aspirript publication experienced neut treatment treatment voice voice strat pan pan phen ChicagoHzuble reefistan NatIR reef incub incub kilomet console nodes nodeslesh reef reef pan Northern Voy dietaryverb
```

**pretrained-base SFT:**
```
 dal off a I of the the was and the to not not in that know:,,al has'm all from by at on of all, right on in the two,'t a., and, to, one two,'t, and atly this on same mayF,ial the the, all'' L to and findon have the all of have, all find'm the find find,, it L only. has this not in d this with a and
```

**random-init SFT:**
```
 look about all about, and this in the, come that5 than. The hees
```

All three are fragments, not answers. The `--samples-after` batch (100 samples
from the pretrained-base arm) reads the same way: repeated closed-class words,
occasional comma runs, no coherent clause. This is the honest low end of the
size axis: at 5M with a Shakespeare-only prior, three epochs of dialogue data
do not land as fluent chat — the model is too small for the format *and* the
content to fit at once.

## What this run does and does not show

It shows: a 5M base trained on ~330k tokens of Shakespeare, SFT'd on 9,500
conversations, ends at val 8.65 (vs 8.80 from random init) and produces
word-fragment generations; the recorded 88M arm (2026-07-28, different
tokenizer and recipe) ended at val 2.7828 with fluent-but-wrong generations.
The two numbers are NOT comparable as-is — different tokenizer, different
corpus, different device — the chapter treats them as points on a size axis,
not as a head-to-head.

It does not show: that any particular size is the "right" place to stop; the
effect of larger SFT budgets at each size; or what happens between 5M and 88M.
Those are the chapter's stated evidence boundary, not open questions the run
pretends to answer.
