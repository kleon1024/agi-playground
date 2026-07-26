---
status: draft
---

# 05 — RL

**Goal:** take a model that already follows instructions and has a notion of
preference (`04-post-training`) and optimize it against a *reward signal*
through actual generation-and-update cycles — not a fixed offline dataset.

**Why this track is a flagship, not a capstone.** Every other full-stack
teaching repo we surveyed (CS336 included) treats RL post-training as one
assignment at the end: implement PPO once, move on. That's the wrong shape
for what the field actually looks like in 2026. RL post-training is a
progression — PPO's mechanics, then why GRPO deleted an entire model to get
comparable results, then GSPO and DAPO as documented fixes to specific GRPO
failure modes, then RLVR as the umbrella paradigm all of them serve, then
multi-turn agentic RL as the frontier where the "environment" itself becomes
the object of design. This track teaches it as a progression because that's
how the field's own literature is structured, and no other single-GPU
curriculum walks it end to end.

## What you build

The seed lesson, `02-grpo`, is speedrun [stage 04](../../../missions/01-language-model-agent/04-rl/): GRPO
with LoRA on a verifiable task (arithmetic or a Countdown-style number game),
with the reward curve published as the run's evidence. `01-ppo-grounding`
exists so that GRPO's simplification actually reads as a simplification —
you have to see the four-model PPO loop to appreciate what GRPO removes.
Everything from `03-gspo-dapo-diffs` onward is deeper track content: the
speedrun proves the core loop works, the track explains why the field moved
past the naive version of it.

## Conceptual spine

### PPO, for grounding

RLHF's RL step is: state = the token sequence generated so far, action =
next token, policy = the LLM itself, reward = a scalar from a reward model
applied at (usually) the end of the sequence. Vanilla policy gradient
(REINFORCE) on this setup has high variance and no protection against
destructively large updates. PPO's answer has three parts, and all three
matter:

**Advantage over raw return.** `A(s,a) = Q(s,a) − V(s)` — how much better this
action was than the state's average — is lower variance than the raw return
because it subtracts a baseline. In practice this is computed via GAE
(Generalized Advantage Estimation): define the TD-error
`δ_t = r_t + γV(s_{t+1}) − V(s_t)`, then

```
A_t^GAE = Σ_{l=0}^{T-t} (γλ)^l · δ_{t+l}
```

with `γ=1.0` in LLM RL (no discounting across a single response) and `λ≈0.95`
trading off bias and variance: `λ=0` is a one-step TD estimate (low variance,
high bias — fully trusts the critic), `λ=1` is Monte Carlo return minus
baseline (zero bias, high variance).

**Clipping instead of a KL trust region.** TRPO constrains the policy update
with a hard KL bound, which needs second-order optimization. PPO's
first-order approximation: let `r_t(θ) = π_θ(a_t|s_t)/π_θ_old(a_t|s_t)`, and
optimize

```
L^CLIP = E[min(r_t·A_t, clip(r_t, 1−ε, 1+ε)·A_t)]
```

with `ε=0.2` the usual choice. The `min` makes this a *pessimistic* bound: for
a good action (`A>0`) the objective stops improving once the ratio exceeds
`1+ε`, removing the incentive to keep pushing probability mass in that
direction within one update.

**A KL penalty against the reference model**, added directly to the reward
signal (`r_modified = r_RM − β·KL(π_θ‖π_ref)`), because without it the policy
drifts arbitrarily far from the SFT model chasing reward-model score — the
first concrete instance of reward hacking this track covers.

The cost of all this: PPO's actor-critic setup needs **four models in
memory simultaneously** — actor, critic, frozen reference, frozen reward
model — which for a 7B model in fp16 is close to 56GB before activations,
squarely a multi-GPU problem even before you account for generation.

### Why GRPO dropped the critic

GRPO's (Shao et al., 2024, DeepSeekMath) core move: instead of training a
critic to estimate `V(s)`, sample a *group* of `G` responses to the same
prompt and use the group's own statistics as the baseline:

```
Â_i = (r_i − mean(r_1,...,r_G)) / std(r_1,...,r_G)
```

Everything else — the clipped surrogate, the KL penalty — carries over
unchanged from PPO; the only substitution is `Â_i` for the GAE advantage.
This removes an entire model's worth of memory (down to three: actor,
reference, reward source) at the cost of `G`x more generation per update step
— you're trading training-time memory for inference-time compute, which is
exactly the trade a 24GB card with a fast inference backend (vLLM) can afford
to make. `G` is typically 8–64; DeepSeek's own choice was 64. A degenerate
case worth knowing before you hit it: if every response in a group gets the
same reward, `std=0` and the advantage is `0/0` — handled by skipping the
group or adding an epsilon, and it happens more often than you'd expect on
easy prompts.

### GSPO and DAPO, as diffs against this GRPO baseline

Both are best understood as targeted fixes to specific things GRPO gets
wrong at scale, not new algorithms:

- **GSPO** (Qwen team) computes the importance ratio at the *sequence* level
  rather than per-token. GRPO's token-level ratio, aggregated over a long
  generated sequence with a MoE policy, accumulates enough variance to
  destabilize training; GSPO's fix is to normalize once per sequence instead.
- **DAPO** (ByteDance/Tsinghua) changes three things at once: "clip-higher"
  (an asymmetric clip range that gives good-but-improving responses more room
  to increase in probability than the symmetric `ε` allows), dynamic sampling
  (skip prompts whose group is all-correct or all-incorrect, since they
  contribute a zero-variance, zero-gradient batch), and overlong-response
  reward shaping (penalize truncated generations directly rather than letting
  them silently poison the reward signal).

Reading these as diffs — same GRPO skeleton, one or two lines changed — is
deliberate: the field did not reinvent RL for LLMs twice, it patched specific
failure modes as they surfaced at larger scale.

### RLVR: the umbrella, not a fourth algorithm

**Reinforcement Learning from Verifiable Rewards** is not another item in the
PPO/GRPO/GSPO/DAPO list — it's the paradigm shift underneath all of them once
the reward stops coming from a learned reward model and starts coming from a
programmatic verifier: does this code pass the test suite, does this
arithmetic answer match the ground truth, does this proof check. This is why
GRPO and math/code tasks are so tightly associated — a rule-based reward
sidesteps reward-model noise and reward-hacking risk almost entirely, at the
cost of only working where a verifier exists. DeepSeek-R1, Qwen3, and Tulu
3's RL stage all use RLVR as the substrate; GRPO (or GSPO, or DAPO) is simply
which optimizer they run on top of it. DeepSeek-R1-Zero — RLVR applied
directly to a base model with *no* SFT stage at all — is the sharpest
demonstration: reasoning behavior (self-verification, "wait, let me
reconsider") emerged from reward signal alone, though DeepSeek's own
production recipe adds a cold-start SFT stage back in because it makes
training more stable and the resulting format more legible.

Rejection sampling (generate many, keep the verifier-approved ones, SFT on
the winners — DeepSeek-R1's stage 3) is the lighter-weight sibling of a full
RLVR loop: no policy-gradient machinery, no clipping, no KL penalty, just
filtering plus ordinary SFT. It's worth teaching as the bridge between
`04-post-training` and this track, because it makes the RL loop's *marginal*
contribution over "generate, filter, fine-tune" visible.

### Multi-turn agentic RL and environments as packages

The frontier this track ends on: RL where a single "action" isn't one
response but a multi-turn trajectory involving tool calls, environment
observations, and a terminal (possibly delayed) reward — SWE-bench-style code
repair, browser tasks, math with a calculator. The organizing idea from
PrimeIntellect's `verifiers` library and Environments Hub (`prime env
install`) is **environment as installable package**: a reward function plus
the interaction protocol around it, versioned and shared like a library
dependency rather than hand-rolled per project. `prime-rl` trains against
these asynchronously at large scale; SkyRL (NovaSky/Berkeley) is the other
major open ecosystem, oriented around long-horizon terminal/SWE agents and
integrated with Harbor. This is deliberately the last lesson: it's where
reward design *is* environment design, and where the harness-engineering
concerns of `08-agents` and the RL concerns of this track meet directly.

## Reward hacking and training instability, honestly

RL post-training breaks in a small number of recurring ways, and pretending
otherwise would undercut the entire "verified runs only" premise of this
repo:

- **Reward hacking is the default failure mode, not an edge case.** A policy
  optimizing against an imperfect reward signal will find the signal's
  blind spots faster than you'll notice them: length inflation (RM prefers
  longer answers, so responses balloon), format gaming (unearned markdown
  headers and bullet points because the RM associates them with quality),
  sycophancy (agreeing with the user regardless of correctness), and
  repetition of reward-correlated keywords. Gao et al. (2023)'s scaling-law
  finding is the quantitative version: true quality follows an inverted-U in
  KL divergence from the reference — `Gold_score ≈ a·√KL − b·KL` — so there
  is a real optimum past which more RL training makes the *measured* reward
  go up while actual quality goes down.
- **KL divergence is the primary instability knob, in both directions.** Too
  small a KL penalty and the policy hacks the reward; too large and it barely
  moves. Adaptive KL controllers (target a specific KL, scale `β` up or down
  based on the gap) are the standard fix over a fixed coefficient.
- **Alignment tax is real and asymmetric.** RLHF/RLVR training reliably
  improves instruction-following and safety metrics while measurably eroding
  unrelated capabilities (math, code, long-context comprehension in some
  reports) unless pretraining-distribution data is deliberately mixed back in
  during the RL stage.
- **Verifiable rewards are not immune to hacking, just harder to hack.** A
  rule-based math or code reward is much less gameable than a learned RM, but
  "overlong reward shaping" in DAPO and dynamic sampling in the same paper
  exist precisely because RLVR setups still have exploitable edges (e.g.
  truncated-but-plausible-looking generations).

## Common misconceptions

1. **"GRPO is a new RL algorithm."** It's PPO with the critic's baseline
   replaced by group statistics — the clipped surrogate and KL penalty are
   unchanged. The novelty is the removal, not a new update rule.
2. **"RLVR means no reward model is ever involved."** RLVR means the reward
   is *verifiable* (rule-based or programmatic); production recipes often
   combine RLVR on verifiable tasks with a learned reward model for
   open-ended, non-verifiable ones in the same training run.
3. **"DPO is just a cheaper GRPO."** DPO is offline (fixed dataset, no
   generation during training); GRPO is online (fresh rollouts every step
   against the current policy). This is a difference in kind, not just cost —
   it's why GRPO can explore and DPO cannot.
4. **"A higher reward curve means a better model."** Only up to the point
   where reward-model overoptimization sets in; reward going up and quality
   going down simultaneously is the expected shape of an unmitigated RLHF/RLVR
   run past its optimum, not an anomaly.
5. **"Multi-turn agentic RL is just GRPO with more steps."** The reward is
   usually terminal and sparse across an entire multi-turn trajectory (did
   the PR merge, did the task complete), the environment has state that
   persists across turns, and credit assignment across the whole trajectory
   is an open problem — process reward models and step-level credit
   assignment (see `04-post-training`'s reward model lesson, and PRM-style
   dense-reward ideas) are the active research response, not a solved
   extension of single-turn GRPO.

## Prerequisites

`04-post-training` (reward models and the DPO family establish the
preference-optimization context RL extends) and `03-pretraining` (a base or
SFT'd checkpoint to apply RL to).

## Key papers

- Schulman et al., *Proximal Policy Optimization Algorithms* (2017) — the
  clip objective this track's PPO lesson implements from scratch.
- Shao et al., *DeepSeekMath: Pushing the Limits of Mathematical Reasoning*
  (2024) — GRPO's original formulation.
- DeepSeek-AI, *DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via
  Reinforcement Learning* (2025) — the four-stage recipe and the "aha
  moment" evidence for RL-emergent reasoning.
- Qwen Team, GSPO technical report — sequence-level importance ratios as the
  MoE-scale stability fix.
- ByteDance/Tsinghua, *DAPO: An Open-Source LLM Reinforcement Learning System
  at Scale* — clip-higher, dynamic sampling, overlong-reward shaping.
- Gao, Schulman, Hilton, *Scaling Laws for Reward Model Overoptimization*
  (2023) — the quantitative account of why more RL isn't always better.
- PrimeIntellect, `verifiers` and Environments Hub docs — "environment as
  installable package" for agentic RL.

## Hardware reality

GRPO with LoRA on 0.5–3B models is comfortably feasible on one 24GB card;
Unsloth's FP8 GRPO path has been reported to fit Qwen3-1.7B training in ~5GB,
leaving headroom for larger batch or group sizes. PPO's four-model memory
footprint makes even LoRA-scale full RLHF tight on a single 24GB card without
aggressive offloading — this track's `01-ppo-grounding` lesson runs at a
scale chosen to demonstrate the mechanics, not production scale. Full-parameter
RL on 7B+ models, multi-node asynchronous RL (OpenRLHF/verl/prime-rl
territory), and agentic multi-turn RL with real tool/browser environments
where rollout concurrency dominates cost all move to the Modal lane.

## Planned lessons

1. `01-ppo-grounding` — PPO mechanics from scratch: GAE, the clipped
   objective, KL penalty, why it's the historical baseline and what it costs.
2. `02-grpo` — group-relative policy optimization, the current default
   algorithm for LLM RL. Speedrun stage 04's seed lesson.
3. `03-gspo-dapo-diffs` — GSPO and DAPO as documented diffs against the GRPO
   baseline implemented in lesson 2.
4. `04-rlvr` — reinforcement learning from verifiable rewards as the umbrella
   paradigm; rubric and reward-function design for math/code tasks.
5. `05-rejection-sampling` — rejection sampling + SFT as a lighter alternative
   to a full RL loop (the DeepSeek-R1 recipe's stage 3).
6. `06-agentic-rl-environments` — multi-turn agentic RL, environment design as
   reward-function design (the frontier capstone).

## Next

[Track 06 — Inference](../../serving/): the GRPO loop above needs fast
rollout generation to be tractable at all — the KV cache and batching
mechanics that make that possible are taught there, and reused directly by
speedrun stage 05.
