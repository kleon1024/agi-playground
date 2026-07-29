---
status: draft
level: applied
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

## The reward is going up. Is that good?

Notice what the reward here is *not*: a learned model. `compute_reward` is a
Python function that evaluates `13 * 17` — reinforcement learning from
verifiable rewards, with no reward model to train and none to drift. That
removes most of the ways a reward gets hacked, and it does not remove all of
them.

The loss above also has one term this chapter has not justified: a KL penalty
against a frozen copy of the policy you started with. It is there because a
policy optimizing an imperfect reward finds that reward's blind spots before
you notice them, and the format reward this task needs in order to start
learning at all is the same reward that gets farmed once it has.

[The reward went up. Did the model get better?](reward-went-up/) takes both
apart: what a programmatic verifier buys and what surface it leaves, what the
leash is for and how it fails in either direction, three hacks specific to this
task, and the published result that measured reward and true quality diverge
past a knowable point rather than at some pathological extreme.

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
2. **Vary the group size.** Run `--group-size 4` versus `--group-size 32`.
   Group size trades inference compute for advantage-estimate variance —
   does a larger group give a visibly smoother reward curve at the same
   step count?
3. **Feel the clip do nothing, then something.** At `--inner-epochs 1` the
   ratio never leaves 1.0, so `clip` is provably a no-op (log
   `ratio.min()`/`ratio.max()` in `grpo_loss` to confirm). At what
   `--inner-epochs` count does the ratio actually leave `[1-eps, 1+eps]`?

## Next

[The reward went up. Did the model get better?](reward-went-up/) covers the KL
leash and the reward hacking this chapter set aside; read it before trusting a
reward curve. After that,
[stage 05 — serve](../05-serve/): this lesson's rollout loop recomputes
attention over the whole sequence at every generated token, which is the
first thing a real GRPO loop fixes — the KV cache and batched-decoding
mechanics that make group rollouts fast are taught there, and this
lesson's `G`x generation cost is exactly why they matter for RL specifically,
not just for serving.
