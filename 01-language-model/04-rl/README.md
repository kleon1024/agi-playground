---
status: verified
level: applied
base: scratch
label: RL (GRPO)
verified: 2026-07-30
---

# How do you improve a model with no correct answer to copy?

**Goal:** take a policy and optimize it against a *reward signal* through
actual generation-and-update cycles — sample completions, score them, push
the policy toward the ones that scored well — instead of imitating a fixed
dataset of examples.

## Why RL after SFT at all

Go back to stage 03's SFT loss and ask what it actually optimizes: minimizing
cross-entropy against a target token sequence someone else produced — a
*behavioral cloning* objective that never asks "was this response actually
good," only "did you predict this exact token." Follow that as far as it
goes and you hit a hard ceiling: SFT can only ever be as good as its
demonstrations, and cannot express a preference it never saw a labeled
example of — it can't learn "shorter is better when both answers are
correct" unless that preference was written into the training set.

RL replaces "imitate this token sequence" with "maximize this scalar
objective," which the model discovers its own path to by generating, getting
scored, and updating — including paths no human demonstration ever walked.
DeepSeek-R1-Zero is the sharpest existing evidence: RL applied directly to a
base model with **no SFT stage at all** produced self-verification and
backtracking ("wait, let me reconsider") that no training example ever
demonstrated — it emerged from optimizing the reward (DeepSeek-AI,
*DeepSeek-R1*, 2025). Imitation learning cannot produce that structurally; it
requires generating, being scored, and updating on your own outputs.

Pretraining is a separate, earlier precondition from the SFT one. It is what
puts a behaviour anywhere in the model's distribution at all, and RL cannot
install a behaviour with zero probability under the current policy — it can only
reweight one that already occurs sometimes under sampling.
[Mission 06's stage 03](../../05-game-ai/03-fixing-collapse/) shows that
precondition in miniature, with a cold-start policy and no pretrained backbone:
GRPO training alone produces real board-sensitivity under sampled decode
(14.4-21.0% success across seeds), yet greedy decode ignores the board entirely
on every seed, and neither a smaller rollout group nor a direct entropy bonus
moved the argmax toward it. The entropy bonus measurably widened the
distribution (1.3-1.7 nats) without changing which token wins — the training
signal did the one thing it can do, reweight what sampling already reaches, and
reweighting was not enough to make the behaviour the deterministic default.
Pretrain-to-RL is about whether a behaviour is in the distribution at all;
SFT-to-RL is about which present behaviour becomes the default that RL then
sharpens.

## What you build

`core/grpo.py` — GRPO from scratch, on a verifiable arithmetic task
(RLVR — Reinforcement Learning from Verifiable Rewards): given "what is
`13 * 17`?", the reward is computed by evaluating `13 * 17`, not by a
learned reward model. The task requires wrapping reasoning in
`<think></think>` and the final answer in `<answer></answer>`; the reward
is additive over a **format** component (did the completion take that
shape) and a **correctness** component (does the extracted answer match the
ground truth). This file implements, by hand:

- **rollout**: sample a *group* of `G` completions per prompt from the
  current policy (`rollout_group`), recording each token's log-prob under
  that policy (`pi_theta_old`) — no KV cache, O(n²) per rollout, the honest
  cost of readability here (track 06 fixes it).
- **group-normalized advantage**: `(r_i - mean(r)) / (std(r) + eps)` over the
  group's own rewards (`rollout_and_score`) — GRPO's entire contribution over
  PPO, nothing else in the loss changes.
- **the clipped surrogate and KL penalty** (`grpo_loss`): PPO's objective,
  unmodified, run against the group-relative advantage instead of a GAE
  advantage. A **k3 KL estimator** (Schulman's unbiased, always-nonnegative
  approximation) measures divergence from a frozen reference policy cloned
  once at the start of training.
- reward-curve logging to JSON, and a resumable checkpoint
  (`save_checkpoint`/`load_checkpoint`) restoring model, optimizer, and step
  count.

**No critic anywhere** — grep this file: no value network, no `V(s)`
estimate. That absence *is* GRPO.

**Scale and fine-tuning choice, stated plainly.** This trains a randomly
initialized, few-hundred-thousand-parameter Transformer — imported from
[`02-pretrain/core/model.py`](../02-pretrain/core/model.py), not redefined —
over a character-level vocabulary built for this task alone, not the BPE
tokenizer or a checkpoint from earlier stages. There is no SFT behind this
policy: a cold start, R1-Zero style, so the file runs standalone without a
GPU or an upstream checkpoint. Every update is **full fine-tuning**, not
LoRA — cheap at this scale and free of adapter bookkeeping. LoRA is the
right default once you're updating a real pretrained checkpoint, which is
exactly what the next file does.

`prod/trl_grpo.py` — the same task and reward function (imported directly
from `core/grpo.py`, so the two can't drift apart), trained with TRL's
`GRPOTrainer` against a real pretrained checkpoint with a LoRA adapter. TRL
hides rollout generation (optionally vLLM-backed), the group-relative
advantage, the clipped surrogate, the reference clone, and the KL
bookkeeping inside `.train()`. What survives as a config knob is the
mechanism itself — `num_generations` is `G`, `epsilon` is `clip_eps`, `beta`
is `kl_beta` — and `reward_funcs` is still yours to write, since the
environment is the one thing no trainer hides from you.

## The group-relative trick

Ask where PPO's advantage estimate comes from: a learned critic,
`A(s,a) = Q(s,a) - V(s)`, trained alongside the policy to predict expected
return. For LLM RL that critic is itself a full copy of the model, so before
writing a line of GRPO, count what PPO already holds in memory at once: actor,
critic, frozen reference, and — in RLHF's original formulation — a frozen
reward model, four models at once. GRPO's move (Shao et al., *DeepSeekMath*,
2024) removes one outright: stop training a critic. Instead, sample `G`
completions to the *same* prompt and use the group's own reward mean and
standard deviation as the baseline:

```
A_i = (r_i - mean(r_1, ..., r_G)) / (std(r_1, ..., r_G) + eps)
```

Everything downstream — the clipped surrogate, the KL penalty — is copied
from PPO unchanged; the substitution is `A_i` for the GAE advantage,
nowhere else. The trade is explicit: `G`x more generation per update step,
in exchange for one entire model's memory footprint disappearing from the
loop — the memory a critic would have occupied buys more rollouts instead.

The failure mode this file handles directly: if every completion in a group
scores identically, `std = 0` and the advantage is `0/0`;
`rollout_and_score` returns `None` and training skips that group. This
happens more than intuition suggests — the real run further down shows it
happening in literally every group across an entire 200-step budget.

The useful quantity is not the absolute reward; it is each completion's
standardized position inside its own prompt group.

<!-- interactive: GRPOAdvantage -->

A detour from here: [what does the group-relative trick actually change?](the-group-relative-trick/)
— the advantage arithmetic run on the actual reward groups (the 200/200
degenerate case, a sparse group, a healthy spread), with the clip's one-sided
brake computed and the zero-sum property named.

A second detour: [the leash that keeps the policy close](the-kl-leash/) —
the k3 KL estimator's arithmetic: always non-negative, asymmetric (reducing
probability mass costs more than increasing it), and soft at the repo's
beta 0.04.

## The reward is going up. Is that good?

Notice what the reward here is *not*: a learned model. `compute_reward` is a
Python function that evaluates `13 * 17` — no reward model to train and
none to drift. That removes most of the ways a reward gets hacked, not all
of them.

The loss above has one term this chapter has not justified: a KL penalty
against a frozen copy of the policy you started with. It exists because a
policy optimizing an imperfect reward finds that reward's blind spots before
you notice them, and the format reward this task needs to start learning at
all is the same reward that gets farmed once it has.

[The reward went up. Did the model get better?](reward-went-up/) takes both
apart: what a programmatic verifier buys and what surface it leaves, what the
leash is for and how it fails in either direction, three hacks specific to this
task, and the published result that measured reward and true quality diverge
past a knowable point rather than at some pathological extreme.

## A real run: zero gradient steps, not a growing reward curve

The base command below has now actually been run, on CPU, for 200 steps:
**every group came back degenerate** (`std(rewards) < 1e-6`), so the
optimizer step and history write are never reached — no `reward_curve.json`
grows. Not a fluke: `format_reward` needs the literal substrings `<think>` or
`<answer>...</answer>`, and against a 78-symbol character vocabulary a
randomly initialized policy emitting that 7-character sequence by chance is
roughly `3e-12` per completion — across the 6,400 completions sampled here,
expected count is `2e-8`. [Full run, with the raw completions that show
why.](runs/2026-07-30-base-grpo-run.md)

A real instance of this mission's "why RL after SFT" argument from the
failure side: DeepSeek-R1-Zero's base model had already learned enough from
pretraining to stumble into tag-like structure occasionally; a randomly
initialized toy model with no such prior never does, at this reward shape
and step budget.

## The fix and its trade

The failure the run makes legible is the degenerate group: when every
completion in a group scores identically, the group-relative advantage
is 0/0, and `rollout_and_score` skips the group. It is not a corner case
— the real run hit it in literally every group across the entire
200-step budget, because a randomly initialized policy emitting the
literal `<think>`/`<answer>` substrings over a 78-symbol vocabulary has
probability around 3e-12 per completion (an expected count of 2e-8
across the 6,400 sampled). The fix is the warm start the exercises name:
a few supervised steps on well-formed examples first — the same prior
DeepSeek-R1-Zero's base model had already learned from pretraining. The
trade is measured on the same axis. RL reweights behavior sampling
already reaches and cannot install behavior with zero probability under
the current policy: the game-ai stage's GRPO run reaches 14.4-21.0
percent success under sampled decode while greedy decode ignores the
board on every seed, and an entropy bonus widens the distribution
(1.3-1.7 nats) without changing which token wins. The second trade is
the leash: the KL penalty against the frozen reference keeps the policy
from farming the format reward's blind spots, and its knob (beta) trades
how far the policy may drift against how fast the reward moves. The
third is the group size itself: GRPO's no-critic move (Shao et al.,
DeepSeekMath, 2024) spends G times the generation per update to buy the
critic's memory footprint back as rollouts.

## Who owns the loop

Each failure in this chapter has one owner:

- **The RL and alignment team** owns the objective: the group-relative
  advantage, the clipped surrogate, and the KL beta. It owns the
  degenerate-group failure — the 200/200 skip run — and the warm-start
  decision that fixes it.
- **The reward and environment owner** owns the verifier:
  `compute_reward` is the one thing no trainer hides, and a Python
  function that evaluates `13 * 17` cannot drift, while a learned reward
  model can. It owns the reward-hacking failure the leash exists for.
- **The training-infra and serving team** owns the rollout cost: G times
  the generation per update is why the KV cache and batched decoding of
  stage 05 matter for RL, not just serving, and why
  [rollout-concurrency](rollout-concurrency/) measures the scheduling
  policy that decides how much of that cost is waiting.
- **The evaluation team** owns the reward-versus-quality read: a rising
  reward curve is not evidence the model got better
  ([reward went up](reward-went-up/)), and the group-relative trick's
  detour measures the zero-sum property that makes a single group's
  absolute reward meaningless.

## Reproducing

The commands are exact and copy-pasteable on CPU for anyone who wants to
watch the mechanism work, at toy scale, right now — reproducing the run
above requires no GPU:

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

Published external numbers, attributed and dated so they don't read as this
repo's own results: DeepSeek-R1-Zero's RL-only run against a 671B-parameter
base model reached scores competitive with OpenAI's o1-0912 on AIME 2024
using RLVR with GRPO and no SFT stage (DeepSeek-AI, *DeepSeek-R1*, January
2025). TinyZero's reproduction showed the same self-verification behavior at
a 3B-parameter scale on a Countdown-style task (Pan et al., *TinyZero*,
2025) — evidence the mechanism doesn't require frontier-scale compute, even
though a random cold start at this lesson's much smaller scale needs a warm
start first, per the run above.

## Exercises

1. **Break the symmetry.** The run above never logs a single non-degenerate
   group in 200 steps. Warm-start the policy first — even a handful of
   supervised steps on well-formed `<think>/<answer>` examples — then rerun
   and log `groups_used`. How few warm-start steps does it take before a
   group stops being degenerate?
2. **Vary the group size.** Run `--group-size 4` versus `--group-size 32`
   after the warm start above. Does a larger group give a visibly smoother
   reward curve at the same step count?
3. **Feel the clip do nothing, then something.** At `--inner-epochs 1` the
   ratio never leaves 1.0, so `clip` is provably a no-op (log
   `ratio.min()`/`ratio.max()` in `grpo_loss`). At what `--inner-epochs`
   count does the ratio leave `[1-eps, 1+eps]`?

## What a production loop has that this one does not

The loop above is complete and it is small. A real run spends most of its
engineering on parts this toy leaves implicit: the clip GRPO inherited from PPO
without deriving it, which failure each of GSPO and DAPO was actually built for,
why the verifier *defines* the task rather than measuring it, the sampler
becoming a training-loop component, what an environment owns once the model can
act, and why rollouts get expensive faster than group size alone suggests.

[What a real loop adds](what-a-real-loop-adds/) takes those in order. Read it
before choosing an acronym off a publication date.

Every method there also assumes the rollouts arrive.
[Why an RL update step waits on its slowest rollout](rollout-concurrency/)
measures what lockstep batching costs once trajectory length is heavy-tailed
instead of fixed — the reason the sampler half of the loop, not the trainer
half, is usually what you are paying for. And
[the RL landscape](LANDSCAPE.md) names the production frameworks that own the
sampler-plus-trainer loop this stage builds by hand, and what each assumes about
who owns the environment.

## Next

[The reward went up. Did the model get better?](reward-went-up/) covers the KL
leash and the reward hacking this chapter set aside; read it before trusting a
reward curve. After that, [stage 05 — serve](../05-serve/): this lesson's
rollout loop recomputes attention over the whole sequence at every generated
token, which is the first thing a real GRPO loop fixes — the KV cache and
batched-decoding mechanics that make group rollouts fast are taught there,
and this lesson's `G`x generation cost is exactly why they matter for RL,
not just serving.
