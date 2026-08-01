---
status: draft
level: reference
---

# Pretraining: Landscape

Source: `reference/research/synthesis.md` anchor table, "Tokenizer" and "Pretraining"
rows.

| Toy (teach-from) | Production | Our take |
|---|---|---|
| minbpe (byte-pair encoding, readable in one sitting) | HF `tokenizers`, `tiktoken`, SentencePiece | minbpe teaches the algorithm; the three production libraries differ on speed (Rust-backed `tokenizers`), OpenAI-ecosystem fit (`tiktoken`), and unigram/BPE flexibility (SentencePiece). Know the algorithm from minbpe, then pick a production tokenizer by ecosystem fit, not by "the one we happened to teach." |
| nanoGPT → nanochat spine, modded-nanoGPT speedrun tricks | torchtitan, nanotron, OLMo-core, Megatron (read-only reference) | nanochat (Oct 2025) is the current bar for full-stack teaching repos — nanoGPT is deprecated by its own author in that role, though its architecture still reads cleanly. Production trainers diverge mainly on distributed-training abstractions (FSDP2/DTensor in torchtitan, 3D parallelism in Megatron); at our single-GPU/GPT-2-class scale those abstractions aren't load-bearing, so we teach the single-GPU loop and read the distributed trainers rather than depend on any one of them. |

**Single-vendor-rot note:** both rows name three-plus independent production
projects (three tokenizer libraries; four pretraining trainers spanning
Meta/EleutherAI-adjacent, HF, AllenAI, and NVIDIA lineages), consistent with
the design doc's Lilac-lesson risk mitigation.
