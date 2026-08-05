---
level: reference
---

# The open-source line behind mission 01

> Dated survey, 2026-08-06. Sources cited inline. External claims are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** mission 01's stack makes choices that can look arbitrary — a 16K
tokenizer, a GQA decoder, a 3.0B-token budget, a small SFT set, GRPO instead
of PPO. Each one is a point on a line of open-source models, and reading the
line is how a learner knows which choice is theirs to make and what it cost
the successor who made it first. This survey is that line, stage by stage,
with the repo's own measured result at each point.

The through-line is the one Su Jianlin states for Kimi's K3
([kexue.fm/archives/11848](https://kexue.fm/archives/11848), 2026-08-04):
model iteration is inheritance plus a targeted upgrade, not reinvention, and
the axis every successor moves along is the same three-way trade — effect,
efficiency, stability.

## Data and scale

**GPT-2** (Radford et al., 2019) fixed the modern recipe: a decoder-only
transformer over web text with byte-level BPE. **GPT-3** (Brown et al., 2020)
showed scale itself is a capability lever — 175B parameters bought in-context
learning with no gradient update. **Chinchilla** (Hoffmann et al., 2022)
priced the other side: at fixed compute, loss is minimized near roughly 20
tokens per parameter, so a training budget is a data decision as much as a
model decision. **LLaMA** (Touvron et al., 2023) opened the weights and made
data curation a public subject; **FineWeb-Edu** (Penedo et al., 2024) is the
classifier-filtered descendant this repo actually trains on.

The repo's anchor: stage 00's funnel keeps 23% of raw Common Crawl, and the
88M model trains on 3.0B tokens — above the Chinchilla ratio, deliberately,
because the mission's claim is about the system composing, not the optimum.

## Tokenizer

Byte-level BPE descends from GPT-2. The open question is vocabulary size:
16K (this repo) is cheap in embeddings and fast to train but tokenizes slowly
across languages; 128K (the Llama and Qwen families) reverses the trade. The
repo pads 16,384 BPE tokens to 16,512 for tensor-core alignment — unused
embedding rows cost a rounding error and speed the largest matmul, the same
observation nanoGPT documented.

## Architecture

The decoder stack is one inheritance: Transformer (Vaswani et al., 2017) ->
decoder-only -> RoPE (Su et al., 2021) -> GQA (Ainslie et al., 2023) -> MLA
(DeepSeek-V2, 2024) -> KDA and linear attention (Kimi Linear, 2026) -> K3 as
the synthesis. Each step is a bet on the KV-cache tax, and the repo's own
decoder is the GQA point (`n_kv_head=4`, one third of MHA's cache).
[The attention-variants detour](../../../missions/01-language-model-agent/02-pretrain/attention-variants/)
draws that line and computes each variant's bill; this survey adds what
happened at the frontier after GQA.

**MLA** compresses K and V into one low-rank latent plus a small per-token
part, so the cache is driven by latent width rather than head count. Two
consequences matter: the compression ratio is baseline-relative (at latent
512, the repo's arithmetic gives 0.67x of its own MHA, far from the 93% the
paper reports against a much larger baseline), and MLA's decode behaves as
MQA with a very wide d_head — small cache, high per-token compute. The K3
article restates the resulting choice as a four-condition test an attention
design must pass to beat MLA — quality, training/prefill cost, cache size,
and decode compute — and notes nothing published satisfies all four, which is
why K3 keeps MLA inside a KDA hybrid. Its NoPE detail is a mechanism worth
the name: KDA's DeltaNet-style update generalizes rotation, so the hybrid
carries a positional prior and can drop RoPE where a pure-MLA model cannot.

On the expert side, the line is the stability story: SwiGLU's known outlier
failure when gate and linear align, answered by K3 with SiTU plus a softcap
on the linear branch (hard clipping exists in GPT-OSS and DSV4; softcap
worked better at the same bound), LatentMoE's four-matrix chain stabilized by
one RMS Norm at the up-projection input, and load balancing moving from
SignSGD-style updates to Quantile Balancing with a 1,000-bin histogram
approximation.

## Post-training

**InstructGPT** (Ouyang et al., 2022) fixed the stack's shape: chat template,
assistant-only loss mask, then RL. **LIMA** (Zhou et al., 2023) proposed the
superficial alignment hypothesis at 65B — alignment mostly teaches style;
knowledge lives in pretraining. The repo measures the small end of that
claim: a 5M SFT produces word fragments, the recorded 88M SFT produces fluent
format with wrong content, and at the top of the axis the claim is not
absolute — SFT can inject knowledge at scale with fact-scaled data
(arXiv:2509.16596, 2025), and SFT stabilizes format while RL generalizes
(Chu et al., ICML 2025, arXiv:2501.17161). **DPO** (Rafailov et al., 2023)
completes the line: preference alignment without a reward model or RL.

## Reinforcement learning

**PPO** (Schulman et al., 2017) applied to generation is the InstructGPT
recipe; its critic is expensive, which motivates **GRPO** (DeepSeekMath, Shao
et al., 2024): group-relative advantages, no critic. **RLVR** removes the
reward model where answers are checkable (R1 line, 2025). The repo's anchor
is a genuine null: at cold-start scale GRPO's group advantage was 0/0 for all
200 steps — the mechanism exists and the scale does not.

## Serving and agents

Serving: **KV cache** made decoding feasible; **PagedAttention** (vLLM, Kwon
et al., 2023) removed fragmentation; **continuous batching** (Orca, 2022)
removed alignment waste; **speculative decoding** (Leviathan et al., 2023)
and **MTP** (DeepSeek-V3, 2024) trade compute for latency — the tension that
complicates MLA's otherwise small cache. The repo measures the small-model
end: the KV cache buys 1.21x at 32 tokens and loses by 512.

Agents: **ReAct** (Yao et al., 2023) gave the loop its canonical plain-text
shape; the frontier moved to the data — installing the behavioral prior at
pretraining scale (Agentic CPT, arXiv:2509.13310, 2025; GLM-5 mid-training,
2026), with trajectories synthesized, truncated, noised, and mixed at a
single-digit share in annealing. The repo's anchor is the absence case: a
checkpoint that never saw a trajectory scored 0/6.

## Evidence boundary

This survey is dated and attributed, not measured: the 93% MLA compression
claim, the four-condition test, SFT knowledge injection, and all frontier
numbers are external results cited inline. The repo's own numbers — the 23%
funnel, 3.0B tokens, 1.21x/512 KV cache, 5M and 88M SFT curves, GRPO 0/0,
agent 0/6 — cite the runs that produced them. Per-model structure gets its
own chapters (the attention-variants detour is the first); this survey holds
the line, not the diagrams.
