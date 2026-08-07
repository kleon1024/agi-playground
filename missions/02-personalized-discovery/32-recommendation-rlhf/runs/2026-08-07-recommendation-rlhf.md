# Run — recommendation RLHF, executed on the Bradley-Terry preference loss

**Date:** 2026-08-07
**Command:** `uv run python core/preference_opt.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 32 asks how a ranker learns from pairwise preferences. This run computes the Bradley-Terry log loss over three pairs and reads where the loss is highest.

## Output

```
preference optimization, read (Bradley-Terry log loss):
  chosen 1.2 vs rejected 0.4: logit 0.8, p 0.69, loss 0.37
  chosen 0.9 vs rejected 0.8: logit 0.1, p 0.52, loss 0.64
  chosen 0.3 vs rejected 1.1: logit -0.8, p 0.31, loss 1.17
  total loss: 2.19

reading: the model is pushed to widen the gap between the
chosen and the rejected item. The loss is the negative log
probability of the preference; real RLHF optimizes it over
sampled pairs, which is where the reward-hacking detour lives.
```

## Notes

- The loss is the negative log probability of the chosen-over-rejected preference; the total is 2.19.
- The weakest pair (0.3 vs 1.1) contributes 1.17 alone — real RLHF optimizes over sampled pairs, which is where the reward-hacking detour lives.
