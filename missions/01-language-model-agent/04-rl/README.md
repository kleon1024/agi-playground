---
status: draft
base: scratch
label: RL (GRPO)
---

# How do you improve a model with no correct answer to copy?

**Goal:** take a policy and optimize it against a *reward signal* through
actual generation-and-update cycles — sample completions, score them, push
the policy toward the ones that scored well — instead of imitating a fixed
dataset of examples.

## Why RL after SFT at all

Supervised fine-tuning (stage 03) trains the model to imitate a distribution
of good responses: minimize cross-entropy against a target token sequence
someone else produced. That is a *behavioral cloning* objective — it never
asks "was this response actually good," only "did you predict this exact
token." SFT can only ever be as good as its demonstrations, and it cannot
express a preference it never saw a labeled example of — it can't learn
"shorter is better when both answers are correct" unless that preference
was written into the training set as an example.

RL replaces "imitate this token sequence" with "maximize this scalar
objective," which the model discovers its own path to by generating,
getting scored, and updating — including paths no human demonstration ever
walked. DeepSeek-R1-Zero is the sharpest existing evidence for this: applying
RL directly to a base model with **no SFT stage at all** produced
self-verification and backtracking behavior ("wait, let me reconsider") that
was never demonstrated in any training example — it emerged from optimizing
the reward (DeepSeek-AI, *DeepSeek-R1*, 2025). That is not something
imitation learning can produce structurally: it requires generating, being
scored, and updating on your own outputs.

## What you build

`core/grpo.py` — GRPO from scratch, on a verifiable arithmetic task
(RLVR — Reinforcement Learning from Verifiable Rewards): given "what is
`13 * 17`?", the reward is computed by evaluating `13 * 17`, not by a
learned reward model. The task requires the completion to wrap its
reasoning in `<think></think>` and its final answer in `<answer></answer>`;
the reward is additive over a **format** component (did the completion take
that shape) and a **correctness** component (does the extracted answer match
the ground truth). This file implements, by hand:

- **rollout**: sample a *group* of `G` completions per prompt from the
  current policy (`rollout_group`), recording each sampled token's log-prob
  under that policy (`pi_theta_old`) — no KV cache, so it's O(n²) per
  rollout, the honest cost of readability here (track 06 covers the fix).
- **group-normalized advantage**: `(r_i - mean(r)) / (std(r) + eps)` over
  the group's own rewards (`rollout_and_score`) — GRPO's entire contribution
  over PPO, and nothing else in the loss changes.
- **the clipped surrogate and KL penalty** (`grpo_loss`): PPO's objective,
  unmodified, run against the group-relative advantage instead of a GAE
  advantage from a value model. A **k3 KL estimator** (Schulman's unbiased,
  always-nonnegative approximation) measures divergence from a frozen
  reference policy cloned once at the start of training.
- reward-curve logging to JSON with `flush=True` prints every logged step,
  and a resumable checkpoint (`save_checkpoint`/`load_checkpoint`) that
  restores model, optimizer, and step count.

**No critic anywhere** — grep this file: no value network, no `V(s)`
estimate, no advantage-estimation module. That absence *is* GRPO.

**Scale and fine-tuning choice, stated plainly.** This trains a randomly
initialized, few-hundred-thousand-parameter Transformer — imported from
[`02-pretrain/core/model.py`](../02-pretrain/core/model.py), not redefined —
over a character-level vocabulary built for this task alone, not the BPE
tokenizer or a checkpoint from earlier stages. There is no SFT behind this
policy: it's a cold start, R1-Zero style, so the file runs standalone
without a GPU or an upstream checkpoint. Every update is **full
fine-tuning**, not LoRA — at a few hundred thousand parameters that's cheap
and keeps the update rule free of adapter bookkeeping. LoRA is the right
default once you're updating a real pretrained checkpoint, which is exactly
what the next file does.

`prod/trl_grpo.py` — the same task and reward function (imported directly
from `core/grpo.py`, so the two files can't drift apart), trained with
TRL's `GRPOTrainer` against a real pretrained checkpoint with a LoRA
adapter. TRL hides rollout generation (optionally vLLM-backed), the
group-relative advantage, the clipped surrogate, the reference clone, and
the KL bookkeeping inside `.train()`. What survives as a config knob is the
mechanism itself — `num_generations` is `G`, `epsilon` is `clip_eps`, `beta`
is `kl_beta` — and `reward_funcs` is still yours to write, because the
environment is the one thing no trainer can hide from you.

## The group-relative trick

PPO estimates the advantage of an action from a learned critic:
`A(s,a) = Q(s,a) - V(s)`, trained alongside the policy to predict expected
return. For LLM RL that critic is itself a full copy of the model, adding
an entire model's worth of memory (actor, critic, frozen reference, and — in
RLHF's original formulation — a frozen reward model: four models resident
simultaneously). GRPO's move (Shao et al., *DeepSeekMath*, 2024): stop
training a critic. Instead, sample `G` completions to the *same* prompt and
use the group's own reward mean and standard deviation as the baseline:

```
A_i = (r_i - mean(r_1, ..., r_G)) / (std(r_1, ..., r_G) + eps)
```

Everything downstream — the clipped surrogate, the KL penalty — is copied
from PPO unchanged; the substitution is `A_i` for the GAE advantage,
nowhere else. The trade is explicit: `G`x more generation per update step,
in exchange for one entire model's memory footprint disappearing from the
loop — the memory a critic would have occupied buys more rollouts instead.

The failure mode this file handles directly: if every completion in a group
gets the identical reward, `std = 0` and the advantage is `0/0`.
`rollout_and_score` returns `None` for that group and training skips it.
This happens more than intuition suggests — an easy prompt the policy
already nails every time, or (common early in a cold start) one it fails
identically every time, both produce exactly this. A degenerate group
contributes zero gradient signal; skipping it is standard practice, not a
bug being papered over.

Change the rewards below before moving to the policy update. The useful
quantity is not the absolute reward; it is each completion's standardized
position inside its own prompt group.

<!-- interactive: GRPOAdvantage -->

## Verifiable rewards: what "no reward model" buys you

RLHF's reward comes from a learned reward model trained on human
preference comparisons — itself a neural network with its own failure
modes, drift, and hackable blind spots. RLVR replaces that with a
programmatic verifier: does this arithmetic answer match the computed
ground truth, does this code pass its test suite, does this proof check.
`compute_reward` in this lesson is the entire "reward model" — a Python
function, not a trained one.

What that buys: no reward-model training run, no reward-model drift as the
policy's outputs shift away from what the RM was trained on, and — because
the verifier is a fixed rule, not a learned approximator — a much smaller
surface to exploit. Not zero surface (see "reward hacking," below), but a
rule that computes `13 * 17` can't be flattered by sycophantic phrasing or
a confident tone the way a learned reward model can. This is why RLVR and
math/code tasks are so tightly associated: a rule-based reward only works
where a verifier exists, but where one does, it sidesteps almost the entire
reward-hacking-against-a-learned-model problem.

## The KL penalty: a leash, not a suggestion

`grpo_loss` adds `kl_beta * kl` to the per-token loss, where `kl` is a k3
estimate of `KL(pi_theta || pi_ref)` against the frozen reference policy
cloned at the start of training. Delete this term and the policy is free
to drift arbitrarily far chasing reward — nothing in the loss says "and
also stay close to where you started," so it could settle on degenerate
token sequences that happen to slip past a regex edge case rather than
actual arithmetic. `beta` too small under-regularizes (the policy hacks the
reward faster than training tightens the leash); too large barely lets the
policy move (every gradient step gets cancelled by the divergence penalty).
This is the field's primary instability knob in both directions, which is
why production recipes use adaptive KL controllers — target a specific KL
value, scale `beta` against the gap — rather than the fixed coefficient
used here for readability.

## Reward hacking, concretely

A policy optimizing an imperfect reward signal finds that signal's blind
spots before you notice them. In this exact task, watch for:

- **Format-only optimization.** The format reward alone is 0.2-1.0 for
  producing `<think>...</think><answer>N</answer>`, regardless of whether
  `N` is right. A policy that finds well-formed tags easier than actual
  arithmetic will farm the format reward with a plausible but wrong answer
  if the correctness signal is too weak relative to it — exactly why
  `format_weight` (0.2) sits well below `correctness_weight` (1.0) in
  `compute_reward`, not the other way around.
- **Regex-edge exploitation.** `_ANSWER_RE` matches the *first*
  `<answer>N</answer>` in the text. A policy could learn to emit multiple
  answer tags, betting one matches, if that pattern were ever rewarded over
  a single honest attempt — a toy-scale instance of DAPO's
  "overlong-response reward shaping" motivation: real RLVR setups need
  explicit handling for plausible-looking-but-cheating completions, not
  just a correctness check.
- **Length/verbosity drift.** Nothing here penalizes a needlessly long
  `<think>` block. At larger scale this is the same mechanism behind RLHF's
  documented length bias, just with a different root cause — an
  unconstrained action space, not a biased scorer.

Gao, Schulman, and Hilton's scaling-law finding (*Scaling Laws for Reward
Model Overoptimization*, 2023) is the quantitative version of all of this:
true quality follows an inverted U in KL divergence from the reference
policy — `Gold_score ≈ a·sqrt(KL) − b·KL` — so there is a real optimum past
which the *measured* reward keeps climbing while actual quality falls.
Reward hacking is the default outcome of unmitigated RL, not an edge case.

## The format reward: why it's needed, how it gets gamed

Why not just reward correctness and skip the format reward entirely?
Because a 0/1 correctness-only signal gives a cold-start policy almost no
gradient on the way to getting there — early in training a random-init
policy essentially never emits a parseable `<answer>N</answer>` at all,
every completion scores exactly 0, every group is degenerate, and
`rollout_and_score` skips all of them. The format reward's partial-credit
ladder (`format_reward`: 1.0 well-formed, 0.5 both tags present but
malformed, 0.2 one tag, 0.0 neither) exists to give the policy something to
climb *before* it can possibly get the arithmetic right.

That same ladder is what the "format-only optimization" hack above
exploits: any reward shaped to make partial progress visible is, by
construction, also a reward partially satisfiable without doing the real
task. That is not specific to this lesson's reward function — DeepSeek-R1's
own paper reports navigating the identical tension, for the identical
cold-start reason, with correctness weighted to dominate for the identical
reason this lesson's is.

## Reproducing

No GPU is available while authoring this lesson, so nothing below has been
run in this repo, and no number in this README is a measured one — that is
what `status: draft` means, and it stays draft until a `runs/` entry exists.
The commands are exact and copy-pasteable on CPU for anyone who wants to
watch the mechanism work, at toy scale, right now:

```bash
# from-scratch GRPO, a few steps, small group — watch reward_curve.json grow
python core/grpo.py train --steps 200 --group-size 8 --prompts-per-step 4 \
    --max-new-tokens 56 --inner-epochs 2 --checkpoint grpo.ckpt.pt \
    --history grpo_history.json

# resume from the checkpoint above — start_step is read back from the file
python core/grpo.py train --steps 400 --checkpoint grpo.ckpt.pt \
    --history grpo_history.json

# TRL production path against a real pretrained checkpoint (needs trl, peft,
# transformers, datasets installed, and a GPU to run at any useful speed)
python prod/trl_grpo.py --model Qwen/Qwen2.5-0.5B-Instruct --group-size 8
```

Published external numbers worth knowing, attributed and dated so they
don't read as this repo's own results: DeepSeek-R1-Zero's RL-only run
against a 671B-parameter base model reached scores competitive with
OpenAI's o1-0912 on AIME 2024 using RLVR with GRPO and no SFT stage
(DeepSeek-AI, *DeepSeek-R1*, January 2025). TinyZero's reproduction showed
the same self-verification behavior emerging at a 3B-parameter scale on a
Countdown-style number task (Pan et al., *TinyZero*, 2025) — much closer to
this lesson's toy scale, and evidence the mechanism itself doesn't require
frontier-scale compute, though nothing in this repo has verified that
locally.

## Exercises

1. **Watch a group go non-degenerate.** Log how many groups get skipped
   (`groups_used` in the history JSON) over the first 50 steps. Cold-start
   policies skip almost everything at first — find roughly where that stops.
2. **Break the KL leash on purpose.** Set `--kl-beta 0.0` and compare the
   reward curve to a normal run. Does reward climb faster? Does the output
   still look like language, or degenerate into something that merely
   satisfies the regex?
3. **Reward-hack the format.** Set `--kl-beta 0.0` and drop
   `correctness_weight` toward `format_weight` in `compute_reward`. Confirm
   reward rises while `mean_correctness` does not — that gap *is* reward
   hacking, made visible.
4. **Vary the group size.** Run `--group-size 4` versus `--group-size 32`.
   Group size trades inference compute for advantage-estimate variance —
   does a larger group give a visibly smoother reward curve at the same
   step count?
5. **Feel the clip do nothing, then something.** At `--inner-epochs 1` the
   ratio never leaves 1.0, so `clip` is provably a no-op (log
   `ratio.min()`/`ratio.max()` in `grpo_loss` to confirm). At what
   `--inner-epochs` count does the ratio actually leave `[1-eps, 1+eps]`?

## Next

[Stage 05 — serve](../05-serve/): this lesson's rollout loop recomputes
attention over the whole sequence at every generated token, which is the
first thing a real GRPO loop fixes — the KV cache and batched-decoding
mechanics that make group rollouts fast are taught there, and this
lesson's `G`x generation cost is exactly why they matter for RL specifically,
not just for serving.
