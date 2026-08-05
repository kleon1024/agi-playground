---
level: reference
---

# The language-model lineage behind mission 01 (Mid-2026)

> Research pass conducted 2026-08-06; sources linked inline. Landscape facts
> reflect that date. This is a survey, not a run — external claims below are
> not re-measured here, and every repository claim cites the mission run that
> measured it.

Mission 01 builds one complete language-model system from scratch — corpus,
tokenizer, pretraining, SFT, RL, serving, agent loop. Every component is a
point on a line of open-source evolution, and the point of this chapter is
the line: what each successor kept, what it changed, and why. The framing
borrows the one Su Jianlin uses for Kimi's K3 in
[*简单谈谈K3的MoE和Attention*](https://kexue.fm/archives/11848) (2026-08-04):
model iteration is not a hunt for a theoretically perfect architecture, it is
"持续的、集大成的研究成果，而非孤注一掷" — an inheritance and an upgrade, where
every change carries an explicit motivation and experiment support, and the
axis is always the same three-way tradeoff: effect, efficiency, stability.

## Data and scale (stage 00)

**GPT-2** (Radford et al., 2019) established the modern recipe: a decoder-only
transformer trained on web text with byte-level BPE. **GPT-3** (Brown et al.,
2020) showed that scale itself is a capability lever — 175B parameters and
in-context learning with no gradient update. **Chinchilla** (Hoffmann et al.,
2022) put a number on the other side: at a fixed compute budget, the
token-to-parameter ratio that maximizes loss is roughly 20:1, which is why
the repo's 88M model trains on 3.0B tokens — above Chinchilla, deliberately,
because the mission's claim is about the system, not the optimum. **LLaMA**
(Touvron et al., 2023) opened the weights and made data curation a
first-class subject; **FineWeb-Edu** (Penedo et al., 2024) is the
classifier-filtered descendant the repo actually trains on.

The tradeoff the stage measures: raw Common Crawl keeps 23% of documents
after language ID, quality filters, and dedup, and the difference between
filtered and unfiltered corpora is larger than most architecture changes —
data is the highest-leverage variable, which is why mission 01 starts with a
funnel the learner writes, not a tidy download.

## Tokenizer (stage 01)

Byte-level BPE descends from GPT-2's `bytes_to_unicode` trick. The lineage's
open question is vocabulary size: small vocabularies (16K, this repo) are
cheap in embeddings and fast to train but tokenize slowly and unevenly across
languages; large vocabularies (128K in the Llama/Qwen families) reverse the
tradeoff. The repo's choice — 16,384 BPE tokens padded to 16,512 for tensor
core alignment — is the small end of that line, and the padding decision is
the same one nanoGPT found: unused embedding rows cost a rounding error and
speed up the largest matmul.

## Architecture (stage 02)

The decoder-only stack is one long inheritance: **Transformer** (Vaswani et
al., 2017) -> decoder-only (GPT-2) -> **RoPE** (Su et al., 2021 — the
kexue.fm author's own contribution) -> **GQA** (Ainslie et al., 2023, cutting
KV cache at fixed quality) -> **MLA** (DeepSeek-V2, 2024, compressing KV into
a low-rank latent) -> **KDA and linear attention** (Kimi Linear report, 2026)
-> **K3** as the synthesis of the 2026 line.

The K3 article is the clearest public statement of the attention tradeoff.
Su's earlier experiments concluded that, at equal training and inference
cost, MLA is close to the best full-attention variant, and he restates the
2026 version as four simultaneous conditions an attention design must meet to
beat it: effect at least MLA's, training and prefill cost at most MLA's, KV
cache smaller than MLA's, and decoding compute low enough not to collide with
multi-token prediction (MTP). Nothing published today satisfies all four,
which is why K3 keeps MLA inside a KDA hybrid — the linear part relieves the
parts MLA is weak on, instead of replacing the whole. **DeepSeek-V4**'s
attention is read in the same spirit: its head-dim-512 K=V MQA plus sparse
and compressed KV is, in Su's words, "MLA推到另一个极致" — MLA's decoding shape
pushed to its limit, at the cost of infrastructure complexity and unproven
optimality under aggressive sparsification. The article's NoPE discussion
adds the mechanism: KDA's DeltaNet-style update generalizes rotation, so a
KDA+MLA hybrid carries a built-in positional prior and can drop RoPE where a
pure-MLA model (K2) cannot.

On the MoE side, the lineage is the stability story: **SwiGLU** (from
PaLM/GPT-4 era) has a known outlier failure when gate and linear align, so
K3 replaces SiLU with **SiTU** plus a **softcap** on the linear branch
(hard-clip exists in GPT-OSS and DSV4, but softcap worked better at the same
bound), and **LatentMoE** (down-project -> 2n-choose-2k MoE -> up-project)
gains one RMS Norm at the up-projection input — the minimal change that
stabilizes the four-matrix chain and, per K3's ablations, even helps
benchmarks beyond stability. Load balancing moves from SignSGD-style updates
to **Quantile Balancing** with a 1,000-bin histogram approximation, chosen
because 10,000 bins buy nothing.

The repo's measured anchor on this line is small and honest: a GQA model with
`n_kv_head=4` whose KV cache buys 1.21x at 32 tokens and *loses* by 512 —
the same cache-efficiency logic that drives GQA and MLA, visible at a scale
where the fixed costs dominate.

## Post-training (stage 03)

**InstructGPT** (Ouyang et al., 2022) fixed the shape of the modern stack:
chat template, assistant-only loss mask, then RL. **LIMA** (Zhou et al.,
2023) proposed the superficial alignment hypothesis at 65B — alignment mostly
teaches style; knowledge lives in pretraining. The repo's
[what-model-size-changes](../../../missions/01-language-model-agent/03-sft/what-model-size-changes/)
chapter measures the small end of that claim: a 5M model's SFT produces word
fragments (val 9.52 -> 8.65, and 8.80 from random init), the recorded 88M SFT
produces fluent format with wrong content (val 3.1829 -> 2.7828), and the
literature at the top of the axis shows the claim is not absolute — SFT can
inject knowledge at scale when the data is fact-scaled rather than
token-scaled (arXiv:2509.16596, 2025), and SFT stabilizes format while RL
generalizes (Chu et al., ICML 2025, arXiv:2501.17161). The **DPO** family
(Rafailov et al., 2023) completes the line: preference alignment without
reward modeling or RL, at the cost of less principled credit assignment.

## Reinforcement learning (stage 04)

**PPO** (Schulman et al., 2017) applied to LM generation is the InstructGPT
recipe; its critic is expensive and unstable, which is the motivation for
**GRPO** (DeepSeekMath, Shao et al., 2024): group-relative advantages from a
small rollout batch, no critic. **RLVR** (verifiable-reward RL, R1 line,
2025) removes the reward model entirely where an answer is checkable. The
repo's measured point is a genuine null: at cold-start scale, GRPO's
advantage normalization produced zero gradient steps across 200/200 groups —
the mechanism exists and the scale does not, which is exactly the kind of
result a from-scratch mission exists to record.

## Serving (stage 05)

**KV cache** made decoding feasible; **PagedAttention** (vLLM, Kwon et al.,
2023) removed fragmentation by paging the cache like an OS; **continuous
batching** (Orca, 2022) removed the batch-alignment waste; **speculative
decoding** (Leviathan et al., 2023) and **MTP** (DeepSeek-V3, 2024) trade
compute for latency. The K3 article adds the current tension: MLA's decoding
is a head-dim-512+ MQA that has already spent most of its compute, so
"MLA + MTP" easily loses — which is precisely why the four-condition test
exists, and why KV-cache size alone is no longer the only serving variable.
The repo measures the small-model end: its KV cache buys 1.21x at 32 tokens
and loses by 512, and concurrency buys nothing until kernels fuse — the fixed
cost of the machinery dominates at this scale.

## Agents (stage 06)

**ReAct** (Yao et al., 2023) gave the agent loop its canonical shape:
Thought/Action/Observation in plain text — the neutral format that survives
whatever chat template post-training later picks. The current frontier of
the line is not the loop but the data: installing the behavioral prior at
pretraining scale (**Agentic CPT**, arXiv:2509.13310, 2025, 300B tokens;
**GLM-5**'s mid-training at roughly 5% of its pretraining budget, 2026), with
trajectories synthesized rather than recorded, plus the format decisions
this repo's mid-training chapter renders — separator conversion, truncation,
noise injection, and a single-digit-percent share concentrated in annealing.
The repo's measured anchor is the absence case: its served SFT checkpoint
scored 0/6 on agent tasks because it had never seen a `Thought:`/`Action:`
trajectory — a training-data format problem, not a prompting problem.

## The through-line

The K3 article's closing line — "效果、效率与稳定性之间的协调，依然是架构设计的
主旋律" — is the summary of this whole lineage. Every successor in this chapter
is an inheritance plus a targeted upgrade under that axis, and the open-source
record is what makes the tradeoffs legible: MLA's KV compression against MTP
friendliness, DPO's simplicity against PPO's credit assignment, GRPO's
no-critic against its sample efficiency, large vocabularies against embedding
cost. Mission 01's contribution is not a new point on any of these lines —
it is a working stack at a scale where a learner can *see* each tradeoff with
their own runs, from the 23% corpus funnel to the zero-gradient GRPO.
