---
status: draft
---

# 04 — Post-training

**Goal:** take a pretrained base model — a next-token predictor with no notion of
"answer the question" — and turn it into something that follows instructions,
prefers good responses over bad ones, and can be compressed or recombined
without retraining from scratch.

**Why this track exists as its own thing.** Most from-scratch curricula stop at
pretraining and treat everything after as "just call `SFTTrainer`." That hides
the actual content: why loss masking is not optional, why a rank-16 matrix can
capture most of what full fine-tuning does, why five different preference-loss
papers all reduce to a two-line diff against each other, and why a reward model
is a classifier with a specific failure mode, not an oracle. This track teaches
the mechanics that RL post-training (`05-rl`) then builds on — reward models
and the DPO family are the on-ramp to GRPO/RLVR, not a separate subject.

## What you build

The seed lesson, `01-sft-chat-tuning`, is speedrun [stage
03](../../speedrun/03-sft/): a chat template applied to a small open instruct
set, loss-masked so the model only pays for its own tokens, fine-tuned on top
of the stage-02 pretrained checkpoint, with before/after generation samples as
the evidence a newcomer can inspect. Everything from `02-lora-and-peft` onward
is track content that speedrun stage 03 does not need at full depth but stage
04 (RL) and any real post-training work will.

## Conceptual spine

### SFT and loss masking

Pretraining teaches "what to say"; SFT teaches "how to say it, in this
format." Concretely: chat templates (ChatML-style `<|im_start|>role` markers
are the 2026 default; Alpaca-style plain text is the historical baseline) wrap
`(instruction, response)` pairs into a single sequence, and the loss is
computed only on the response tokens. In PyTorch this is `ignore_index=-100`
on `CrossEntropyLoss`: labels for prompt tokens are set to `-100`, and the
mean is taken only over the tokens that remain. Skipping this — training on
the full sequence — wastes compute reproducing the prompt and can bias the
model toward echoing the user.

LIMA (Zhou et al., 2023) is the empirical argument for why SFT data quality
dominates quantity: ~1,000 hand-curated examples got close to strong
proprietary-model quality in human eval, versus 52K for Alpaca. The
"Superficial Alignment Hypothesis" reading: pretraining already contains
almost all the knowledge; SFT mostly teaches output format and style. This
doesn't mean SFT is trivial — it means the lesson budget goes to data curation
(diversity across task types, correctness, style consistency) rather than
scale.

Packing (concatenating multiple short examples into one training sequence
with a block-diagonal attention mask) turns ~54% padding efficiency into
~93%+ — worth teaching once as the reason production SFT trainers default to
it.

### LoRA: the actual mathematics

Full fine-tuning a 7B model needs weights + gradients + optimizer state —
roughly 4x the parameter count in fp32-class terms, well past a 24GB card
before you add activations. LoRA's premise, grounded in Aghajanyan et al.
(2021)'s intrinsic-dimensionality result, is that the *change* induced by
fine-tuning, not the model itself, is low-rank: a 125M-parameter model's
fine-tuning trajectory can be captured in a subspace of a few hundred
dimensions and still recover ~90% of full fine-tune performance.

The parameterization:

```
W' = W + ΔW = W + BA
```

with `W ∈ R^{d×k}` frozen, `B ∈ R^{d×r}`, `A ∈ R^{r×k}`, and `r ≪ min(d,k)`
(typically 4–64). Forward pass: `h = Wx + (α/r)·BAx`. For a 4096×4096
attention projection, full fine-tuning is 16.8M parameters per matrix; LoRA at
r=16 is ~131K — about 0.12% of the layer.

Three details that determine whether it actually works, not just whether it
runs:

- **`B` is initialized to zero, `A` to `N(0, σ²)`.** This makes `ΔW = 0` at
  step zero — training starts exactly at the pretrained model, a warm start.
  If both were randomly initialized, training would begin by immediately
  perturbing a model that already works. Note the asymmetry is load-bearing:
  if `A` were also zero, `B`'s gradient (`∂L/∂B = (α/r)·(∂L/∂h)(Ax)ᵀ`) would
  be zero too and nothing would ever move.
- **The `α/r` scaling exists so rank is a free hyperparameter to sweep.**
  Without it, `BAx`'s variance scales with `r`, so results at different ranks
  aren't comparable. (rsLoRA argues `α/√r` is the theoretically correct
  normalization — `BAx`'s variance is a sum of `r` terms, so its standard
  deviation scales with `√r`, not `r` — and matters mainly at high rank.)
- **Merging is free at inference.** `W' = W + (α/r)BA` folds back into a
  single matrix with zero extra latency, at the cost of losing the ability to
  hot-swap adapters.

### The PEFT family beyond vanilla LoRA

QLoRA (Dettmers et al., 2023) is the one that changes what fits on a 24GB card:
quantize the frozen base to 4-bit NF4 (quantization bins placed at the
quantiles of a fitted normal distribution rather than uniformly, so precision
concentrates where the weight mass is), keep LoRA adapters in bf16, and add
double quantization (quantizing the quantization scale factors themselves).
Net effect: a 7B model's weight footprint drops from ~14GB (fp16) to ~3.6GB,
which is why QLoRA — not vanilla fp16 LoRA — is the practical default for
13B-class models on a single 24GB card. DoRA (2024) decomposes `W` into
magnitude and direction and lets LoRA update direction while a separate
learned scalar handles magnitude, closing 0.5–2% of the gap to full
fine-tuning for comparable cost. LoRA+ (2024) simply gives `B` a ~16x larger
learning rate than `A`, because `B`'s zero initialization means it needs a
bigger push to leave zero. AdaLoRA reallocates a fixed rank budget across
layers by pruning low-importance singular values during training instead of
fixing `r` uniformly.

### Reward models: a preference classifier, not a quality oracle

A reward model is a Bradley-Terry (1952) pairwise-preference classifier
wearing an LLM body. Given a preference pair `(x, y_w, y_l)` — a prompt and a
chosen/rejected response — Bradley-Terry says `P(y_w ≻ y_l) = σ(r_w − r_l)`,
and training minimizes the negative log-likelihood:

```
L_RM = −log σ(r_w − r_l)
```

which is binary cross-entropy on the reward difference. Architecturally: take
a pretrained transformer, attach a single `Linear(hidden_dim, 1)` head (no
bias — the absolute reward value carries no meaning, only differences do),
and read it off the last token's hidden state (the only position in a causal
model that has attended to the entire sequence). InstructGPT scaled RM size
with policy size and found a 6B RM clearly outperformed a 1.3B RM when
supervising a 175B policy — the RM has to be capable enough to detect the
policy's failure modes, or it becomes an easy target for reward hacking (see
`05-rl`'s treatment of that problem in the RL loop itself).

### The DPO family, taught as diffs against a shared loss

DPO's move (Rafailov et al., 2023) is to solve the KL-constrained RLHF
objective in closed form, note that the optimal policy has the form
`π*(y|x) = π_ref(y|x)·exp(r(x,y)/β)/Z(x)`, and observe that when you plug
this reward expression into Bradley-Terry, the intractable partition function
`Z(x)` cancels in the reward *difference*. The result is a loss you can
compute with two forward passes and no reward model, no rollouts, and no RL
loop:

```
L_DPO = −E[log σ(β·(h_w − h_l))],   h = log π_θ(y|x) − log π_ref(y|x)
```

Everything that follows is a one-line change to this loss:

| Method | Change from DPO | Why |
|---|---|---|
| **DPO** (2023) | baseline | Bradley-Terry + closed-form solve |
| **IPO** (2023) | `(h_w − h_l − 1/2β)²` — MSE to a fixed margin instead of log-sigmoid | DPO's loss has no upper bound on the margin and can overfit noisy preference labels; IPO gives it a target and penalizes overshoot |
| **KTO** (2024) | pointwise `(x, y, label∈{desirable, undesirable})` instead of pairs, loss built from prospect theory | Pairwise comparisons are expensive to collect; thumbs-up/down is not |
| **ORPO** (2024) | odds ratio `π_θ(y)/(1−π_θ(y))` instead of a ref-relative log-ratio; SFT and preference loss combined in one term | No reference model needed — one model, one pass, and SFT + alignment happen in the same step |
| **SimPO** (2024) | average per-token log-prob instead of summed log-prob, plus a margin `γ` | Removes both the reference model and DPO's implicit bias toward longer sequences (summed log-prob rewards length) |

Reading this as a progression, not five independent papers, is the point:
each column is answering "what does DPO assume that we can remove or fix," and
the removed assumption tells you when to reach for which. GRPO — which also
descends from "replace an explicit reward model / critic with something
cheaper" — belongs to `05-rl`, not here, because it optimizes online (fresh
rollouts every step) rather than against a fixed preference dataset.

### Distillation

Standard knowledge distillation trains a student on a frozen teacher's output
distribution — an *off-policy* signal, since the student sees the teacher's
tokens during training but its own tokens at inference, causing
exposure-bias-style mismatch. **On-policy distillation** (Thinking Machines,
2025; formalized earlier as GKD by Agarwal et al., 2024) closes this gap: the
student generates, and the teacher scores or provides soft labels on the
student's own trajectory, so training and inference distributions match.
DeepSeek-R1's distilled model line is the existence proof that reasoning
traces — not just answers — transfer: R1-Distill-Qwen-7B was reported to beat
GPT-4o on MATH and AIME 2024 by training on ~800K distilled chain-of-thought
samples that preserve the teacher's `<think>...</think>` format. Distilling
Step-by-Step (Hsieh et al., 2023) is the data-efficiency argument: supervising
on rationale *and* answer jointly reportedly matched standard fine-tuning
using an order of magnitude less data, because the rationale is an additional
training signal, not just the label.

### Model merging

Merging combines fine-tuned checkpoints with zero additional training, under
the assumption that a "task vector" `τ = θ_finetuned − θ_base` behaves
approximately linearly: `θ_merged = θ_base + Σ λ_i τ_i` (Ilharco et al.,
2023). This works when task vectors are close to orthogonal and breaks down
when they conflict — merging a censored and an uncensored fine-tune of the
same base is the canonical failure. TIES-Merging (Yadav et al., 2023) fixes
sign conflicts and redundant near-zero parameters via trim → elect-sign →
merge; DARE (Yu et al., 2023) randomly zeroes ~90% of each task vector and
rescales the rest, on the empirical claim that most of a fine-tune's weight
delta is noise and the "skill" lives in a small subset of parameters; SLERP
interpolates two checkpoints along the sphere rather than a straight line, so
weight norms don't collapse toward the midpoint. `mergekit` is the practical
tool for all three and the natural `prod/` counterpart to a from-scratch
task-arithmetic implementation.

## Common misconceptions

1. **"LoRA is an approximation of full fine-tuning."** It's closer to a
   *regularized* fine-tune: constraining `ΔW` to rank `r` isn't just a
   compute shortcut, it changes what the model can learn, which is part of
   why LoRA sometimes generalizes better on small datasets, not just cheaper.
2. **"A reward model measures quality."** It measures *relative preference
   under Bradley-Terry*, trained on a finite, noisy, non-exhaustive sample of
   comparisons. It has systematic blind spots (length, format, sycophancy)
   that a policy trained against it will find and exploit — this is Goodhart's
   Law, not a bug to patch away.
3. **"DPO is RL without the RL."** DPO is a *closed-form solution* to a
   specific KL-constrained objective, derived under the assumption that the
   training data already reflects what you want to optimize toward. It's
   offline and doesn't explore; the moment you need online generation and
   evaluation against a moving policy, you're back to something RL-shaped
   (`05-rl`'s Online/Iterative DPO territory).
4. **"ORPO and SimPO are strictly better than DPO because they drop the
   reference model."** They remove a memory cost, not a capability — DPO's
   reference model provides an explicit anchor against catastrophic drift
   that reference-free methods have to compensate for differently (odds
   ratio, or a margin term).
5. **"Model merging is a free lunch."** It's a free lunch specifically when
   task vectors are near-orthogonal and fine-tunes are shallow (LoRA-scale).
   It reliably fails across different base models, different architectures,
   or heavily-diverged full fine-tunes, because the linear-path assumption
   about the loss landscape stops holding.

## Prerequisites

`03-pretraining` — this track needs a base checkpoint to fine-tune. Any small
open checkpoint works if you haven't run the pretraining track yourself.

## Key papers

- Zhou et al., *LIMA: Less Is More for Alignment* (2023) — data quality over
  quantity for SFT; the Superficial Alignment Hypothesis.
- Hu et al., *LoRA: Low-Rank Adaptation of Large Language Models* (2021) —
  the original low-rank adapter formulation.
- Dettmers et al., *QLoRA: Efficient Finetuning of Quantized LLMs* (2023) —
  NF4 + double quantization + paged optimizers; the reason 13B fits on 24GB.
- Rafailov et al., *Direct Preference Optimization* (2023) — the closed-form
  derivation this track's DPO section walks through in full.
- Meng et al., *SimPO: Simple Preference Optimization with a Reference-Free
  Reward* (2024) — the simplest, and often strongest, DPO-family variant.
- Ilharco et al., *Editing Models with Task Arithmetic* (2023) — the
  linearity assumption behind model merging.
- Agarwal et al., *GKD: Generalized Knowledge Distillation for
  Auto-Regressive Sequence Models* (2024) — on-policy distillation.

## Hardware reality

SFT/LoRA/QLoRA up to ~7–8B, DPO/ORPO/SimPO on 1–3B full-parameter or 7–8B
LoRA, and reward-model training on ≤3B all fit comfortably on one 24GB card.
QLoRA is what makes 13B-class models fit at all on a 24GB card. Full-parameter
fine-tuning of 7B+ models, or reward models sized to match a 7B+ policy,
needs the Modal multi-GPU lane.

## Planned lessons

1. `01-sft-chat-tuning` — chat templates, loss masking, instruction tuning on
   a small open dataset. Speedrun stage 03's seed lesson.
2. `02-lora-and-peft` — low-rank adapters, why they work, QLoRA/DoRA/LoRA+,
   when full-parameter fine-tuning is still worth it.
3. `03-reward-model-training` — training a scalar reward model from
   preference data; Bradley-Terry loss derivation and implementation.
4. `04-dpo-family-loss-diffs` — DPO, IPO, KTO, ORPO, SimPO as "diff the loss
   function" exercises against a shared training loop.
5. `05-distillation` — teacher-student distillation, on-policy distillation
   (GKD), reasoning-data curation (DeepSeek-R1/OpenThoughts-style).
6. `06-model-merging` — task arithmetic, TIES, DARE, SLERP via `mergekit`.

## Next

[Track 05 — RL](../05-rl/): everything here that stopped at a fixed dataset
or a frozen reward model — DPO, reward models — is the on-ramp to RL
post-training proper: online rollouts, group-relative advantages, and
verifiable rewards.
