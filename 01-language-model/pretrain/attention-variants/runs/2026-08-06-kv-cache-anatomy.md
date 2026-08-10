# Run — KV-cache arithmetic across MHA / GQA / MQA / MLA

**Date:** 2026-08-06
**Command:** `uv run python core/kv_cache_anatomy.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Ground the attention-variants chapter's architecture comparison in arithmetic
computed from the measured stage-02 configuration (d_model 768, 12 layers, 12
query heads, 4 KV heads, bf16) rather than a table someone typed in. The
chapter's causal claim — the KV cache is the architecture's tax, and every
variant after MHA is a bet on how much to pay — is exactly this arithmetic.

## Output

```
stage-02 config: d_model=768, n_layer=12, n_head=12, d_head=64, bf16 (2B/value)

variant                 KV B/tok    KV @1k    KV @8k    KV @32k  attn p/layer   vs MHA
MHA (12 heads)             36864      36.0     288.0     1152.0     2,359,296    1.00x
GQA (4 KV heads)           12288      12.0      96.0      384.0     1,572,864    0.33x
MQA (1 KV head)             3072       3.0      24.0       96.0     1,277,952    0.08x
MLA (latent 512)           24576      24.0     192.0      768.0     1,572,864    0.67x
```

## Notes

- The repo's decoder is the GQA row (n_kv_head=4): its KV cache is one third
  of MHA's at every context length.
- MLA's cache (0.67x MHA at latent 512) looks unimpressive next to the
  headline 93% compression in DeepSeek-V2's paper. The gap is the baseline:
  the paper compares against a much larger MHA with per-head RoPE copies,
  while this table compares against this repo's 64-wide d_head MHA. The
  compression claim is baseline-relative, which is exactly the kind of number
  a learner should learn to read.
- Bytes are only half the story: MLA's decode behaves as MQA with a very wide
  d_head, so its per-token compute is high — the tension the K3 article
  (kexue.fm/archives/11848, 2026-08-04) names for MTP friendliness. This run
  computes bytes only; the serving stage's engine bench measures wall-clock.
- The serving stage measured the small-model end of this curve: the repo's
  KV cache buys 1.21x at 32 tokens and loses by 512, because engine fixed
  costs dominate at toy context (runs/2026-07-29-engine-bench-corrected.md).
