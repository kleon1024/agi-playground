# Run — the exact base GRPO command, for real

The README's "Reproducing" section calls its commands "exact and
copy-pasteable on CPU... at toy scale, right now" but had never actually been
run. This is that run.

## Command

```bash
python core/grpo.py train --steps 200 --group-size 8 --prompts-per-step 4 \
    --max-new-tokens 56 --inner-epochs 2 --checkpoint grpo.ckpt.pt \
    --history grpo_history.json
```

Default seed (0), default `--kl-beta 0.04`, default `--clip-eps 0.2`.

## Hardware and software

| | |
|---|---|
| Machine | local CPU (Apple Silicon, macOS), no GPU used or needed |
| Python / torch | 3.11, torch 2.10.0 |
| Wall-clock | 7m01s (348s user, 297s system — torch's CPU thread pool, 153% average utilization) |
| Cost | $0 (local lane) |

## Result: zero gradient steps, in 200 out of 200

```
step 141: every group this step was degenerate, skipping
step 142: every group this step was degenerate, skipping
...
step 199: every group this step was degenerate, skipping
done: 200 steps, history in grpo_history.json
```

No `grpo_history.json` and no `grpo.ckpt.pt` exist after this run. Both are
only written inside the branch that runs when at least one prompt's group is
*not* degenerate — every single one of the 200 steps hit
`rollout_and_score`'s `return None` path (`std(rewards) < 1e-6`, i.e. every
completion in the group scored identically), so the loop never reaches the
optimizer step, the periodic checkpoint save, or the history write, for the
entire budget. `reward_curve.json` growing, the thing the README's
Reproducing section tells the reader to watch, does not happen at these
exact settings.

## Why: this is not a fluke, it is combinatorics

A direct inspection of the very first sampled group (`rollout_and_score` at
step 0, problem `13 + 14`) shows why:

```
0 reward 0.0 {'format': 0.0, 'correctness': 0.0} 'Aj+22kf0 GGkbHcd>IZZN8n=b:qpB0d*wmJC/pUDh2SAN Qp86/xk*wB'
1 reward 0.0 {'format': 0.0, 'correctness': 0.0} 'qr'
2 reward 0.0 {'format': 0.0, 'correctness': 0.0} 'FL-D*5BpI\nc<djxHR+26J=q-1C\nb:(1==<+/g)s:ExXg*3luPPzr7h'
...
7 reward 0.0 {'format': 0.0, 'correctness': 0.0} 'yHDD*x+,'
```

All eight completions in the group score exactly `0.0` — not close to zero,
identically zero — because `format_reward` requires the literal multi-character
substrings `<think>` (7 characters) or `<answer>...</answer>` to appear
somewhere in the completion, and this is a character-level vocabulary (78
usable symbols, one token per character). The probability of a randomly
initialized policy emitting the exact 7-character sequence `<think>` at some
position in a 56-character completion is on the order of `56 * 78^-7 ≈ 3e-12`
per rollout; across all 6,400 completions this run actually sampled (200
steps x 4 prompts x 8 completions), the expected count of even one
tag-bearing completion is roughly `2e-8` — indistinguishable from never.
Every group is degenerate for the same reason every other group is
degenerate: nothing has ever broken the symmetry.

## What this does and does not establish

- **Does establish**: at these exact documented settings, from a randomly
  initialized character-level policy with no warm start, GRPO's format+
  correctness reward as implemented here produces zero non-degenerate groups
  and therefore zero gradient updates across a 200-step budget. This is a
  measured fact about this configuration, not a guess.
- **Does establish, and ties back to this mission's own argument**: this is a
  concrete instance of exactly why R1-Zero-style pure-RL-from-a-base-model
  works at frontier scale but does not automatically transfer to a
  from-scratch toy model — DeepSeek-R1-Zero's base model had already learned
  enough from pretraining to occasionally emit tag-like structure by chance;
  a randomly initialized few-hundred-thousand-parameter character-level model
  has no such inductive bias to lean on.
- **Does not establish** that GRPO itself is broken, or that this reward
  function is unusable — only that *this* combination (random init, no SFT,
  character-level tokens, this exact reward shape, this step budget) never
  clears the format-reward's combinatorial floor. A warm start (even a
  handful of SFT steps on well-formed `<think>/<answer>` examples), a denser
  partial-credit signal, or vastly more rollouts per step would each plausibly
  break the symmetry — none of those were tried here, since doing so would
  depart from the commands the README documents.
- **Does not establish** anything about `inner_epochs`, `clip_eps`, or the KL
  term's behavior — none of that code path is ever reached when every group
  is degenerate.

## Reproduce

```bash
cd missions/01-language-model-agent/04-rl/core
python grpo.py train --steps 200 --group-size 8 --prompts-per-step 4 \
    --max-new-tokens 56 --inner-epochs 2 --checkpoint /tmp/grpo.ckpt.pt \
    --history /tmp/grpo_history.json
```
