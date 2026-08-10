# Run — Chat template contract: marker cost, header parity, mask density

**Date:** 2026-08-07
**Commands:**

```bash
# export the frozen stage-01 tokenizer to HF format (parity verified in
# 01-tokenizer/runs/2026-07-26-bpe-16k.md)
cd 01-language-model/01-tokenizer/prod
python hf_tokenizer.py export ../tokenizer.json /tmp/tokenizer_hf.json \
    --corpus <corpus-dir> --verify-docs 300

cd 01-language-model/03-sft/the-template-is-a-contract/core
python mask_audit.py --tokenizer /tmp/tokenizer_hf.json
```

**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; tokenizers 0.23.1; datasets from the
local HuggingFace cache (offline).
**Wall-clock:** 8.7s (9,500 conversations rendered, packed, and counted).
**Cost:** \$0 (local lane).

## Purpose

Stage 03's chat template is a contract: `<|im_start|>role\ncontent<|im_end|>\n`
with the markers as reserved ids 16385/16386, and the loss masked to
assistant turns. The main chapter states the "exactly one convention"
rule. This run measures the three properties that rule depends on, on
the real frozen tokenizer, the real `render_and_mask`, and the real
9,500-conversation no_robots training set.

## Output

```
chat template contract audit (real tokenizer, real masker, real no_robots 9,500 conversations):

  marker cost on the frozen vocab:
    reserved id: 1 token per marker (ids 16385/16386)
    <|im_start|> byte-split: 8 tokens [60, 124, 317, 95, 306, 433, 124, 62]
    <|im_end|>   byte-split: 7 tokens [60, 124, 317, 95, 505, 124, 62]

  train/serve header parity (canonical 'assistant\n' = [557, 8697, 10]):
    assistant (no newline)       2 token(s) [557, 8697] first divergence at token 2
    Assistant\n (capital)        3 token(s) [11295, 8697, 10] first divergence at token 0
     assistant\n (leading space) 2 token(s) [10101, 10] first divergence at token 0
    assistant  \n (two spaces)   4 token(s) [557, 8697, 32, 4209] first divergence at token 2
    assistant\r\n (CRLF)         4 token(s) [557, 8697, 13, 10] first divergence at token 2

  what the mask trains on (9,500 conversations, 3,305 packed blocks of 1024):
    real tokens:      2,723,910
    loss targets:    1,856,390 (68.2% of real tokens)
    masked context:    832,996
    marker scaffold:    34,524
    padding:           663,715
    per-block target share: min 1.7%, p50 73.7%, p90 88.7%
    markers: 46,380; if byte-split they add ~301,470 tokens (+11.07% of real tokens)
    long conversations dropped by packing: 217

  the same conversation in the no-reserved-id world:
    reserved markers: 247 tokens; byte markers: 273 tokens (1.1x)

  verdict: the template is a contract - one id per marker,
  byte-exact train/serve parity, and a masker whose whole job
  is keeping user text out of a loss that is mostly answer
  on this curated set - except in the long-prompt tail.
```

## What the numbers show

- **A marker is one id, or it is seven or eight.** The frozen vocab byte-splits
  `<|im_start|>` into 8 tokens and `<|im_end|>` into 7. Across 9,500
  conversations that is 46,380 markers; unreserved, they would add about
  301,000 tokens, +11.1% of the real corpus. Amortized over long answers the
  per-conversation inflation is small (1.1x on the sample conversation), which
  is why the cost is usually invisible until the batch is full.
- **The header is supplied, never predicted — so it must be byte-exact.** The
  canonical `assistant\n` is ids [557, 8697, 10]. A capital `Assistant\n` or a
  leading space diverges at token 0; a missing newline, a CRLF, or an extra
  space diverges at token 2. The model has never seen these prefixes in
  training (the header is masked out of the loss), so serving with any of them
  starts the continuation off-distribution.
- **The mask's job here is exclusion, not density.** On this curated set the
  assistant answers average 177 tokens against 83 for user prompts, so 68.2%
  of real tokens are loss targets and the mask is mostly keeping the 30%
  user/system context out of the gradient — which is what stops the model from
  learning to imitate the user. The tail is the risk surface: per-block target
  share has a 1.7% minimum, so a long-prompt conversation can still train
  almost entirely on masked context.
- **Packing drops the long tail.** 217 of 9,500 conversations exceed one
  1024-token block and are skipped entirely by `pack`; the 3,305 blocks also
  carry 663,715 padding tokens (19.6% of block capacity).

## Evidence boundary

- All numbers are token-level measurements on the real tokenizer, the real
  masker, and the real no_robots data; there is no GPU run, so the header
  drift is measured as token-sequence divergence, not as end-to-end model
  degradation.
- The byte-split marker cost is a property of the frozen vocab, not a separate
  trained tokenizer: it shows what the contract costs when the ids are not
  reserved (or when a serving harness reconstructs markers as raw strings).
- The mask-density figure describes no_robots, a curated set; scraped or
  model-generated SFT corpora with shorter answers or longer prompts would
  shift the target share toward the measured 1.7% minimum, which is where the
  masker's correctness (and its tests) matter most.
