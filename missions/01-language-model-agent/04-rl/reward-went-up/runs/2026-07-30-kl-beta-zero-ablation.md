# Run — Exercise 1, remove the leash (`--kl-beta 0`), for real

This chapter's first exercise: "Remove the leash. Set `kl_beta` to 0 and
train. Plot reward and a held-out correctness check on the same axes, and
identify the step where they separate." This is that run, against the
identical seed and settings as
[the base run](../../runs/2026-07-30-base-grpo-run.md), with only
`--kl-beta` changed from its default (0.04) to 0.

## Command

```bash
python core/grpo.py train --steps 200 --group-size 8 --prompts-per-step 4 \
    --max-new-tokens 56 --inner-epochs 2 --kl-beta 0 \
    --checkpoint grpo.ckpt.pt --history grpo_history.json
```

## Hardware and software

Identical to the base run: local CPU, no GPU, torch 2.10.0, $0 cost.

## Result: identical to the base run — every group still degenerate

```
step 43: every group this step was degenerate, skipping
step 44: every group this step was degenerate, skipping
step 45: every group this step was degenerate, skipping
step 46: every group this step was degenerate, skipping
```

Every logged step through this run matches the base run's pattern exactly:
every one of the 200 groups is degenerate (`std(rewards) < 1e-6`), so no
`grpo_history.json` or `grpo.ckpt.pt` is produced here either.

## The exercise cannot be completed at these settings, and here is why

The exercise asks to "identify the step where [reward and held-out
correctness] separate" — but `kl_beta` only enters the loss inside
`grpo_loss`, which is only ever called for a *non-degenerate* group
(`rollout_and_score` returns `None`, and the caller `continue`s, before
`grpo_loss` is reached). [The base run](../../runs/2026-07-30-base-grpo-run.md)
already established that this exact reward function, character-level
vocabulary, and random initialization combine to make a non-degenerate group
astronomically unlikely (roughly `2e-8` expected non-degenerate completions
across 6,400 sampled here). Setting `kl_beta` to 0 changes nothing about
which groups are degenerate, because degeneracy is decided entirely by the
reward function and the sampled completions — the KL term is downstream of a
gate this run never opens.

This is the honest result: **you cannot observe reward hacking or KL-leash
removal at a point training never reaches.** The mechanism this exercise is
built to demonstrate (an unleashed policy drifting toward degenerate
high-reward completions) requires a policy that has already cleared the
format-reward floor at least once — this run's policy never does.

## What this does and does not establish

- **Does establish**: at these exact settings, removing the KL penalty
  produces no observable difference from the base run, because both runs
  are stuck at the same pre-gradient degenerate-group wall.
- **Does not establish** anything about reward hacking, KL-leash behavior, or
  which `beta` value is safe — those all require a policy that has started
  moving, which this configuration never produces. The analysis in the rest
  of this chapter (the leash, the three hacks, the inverted-U result) remains
  correct as a description of the mechanism and of published, external
  measurements; it is not re-derived or contradicted by this null run, only
  left unobserved locally.
- **What would actually let this exercise run**: the same fix the base run's
  writeup names — a warm start that gets even a small fraction of
  completions past the format-reward floor before RL begins, which is a
  restatement, from the failure side, of this mission's own "why RL after
  SFT" argument.
