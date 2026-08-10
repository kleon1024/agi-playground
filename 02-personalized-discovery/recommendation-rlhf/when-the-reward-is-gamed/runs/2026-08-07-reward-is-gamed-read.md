# Run — when the reward is gamed, executed on the proxy-versus-truth read

**Date:** 2026-08-07
**Command:** `uv run python core/reward_gaming.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 32's RLHF optimizes a proxy. This run compares proxy score with true quality across three policies.

## Output

```
reward gaming, read:
  helpful: proxy 0.7, true quality 0.7
  verbose: proxy 0.95, true quality 0.45
  sycophantic: proxy 0.9, true quality 0.35
  most gamed: sycophantic (gap 0.55)

reading: the verbose policy maximizes the proxy by exploiting
its preference for length, while true quality falls. The gap
between proxy and truth is reward hacking — why RLHF needs
regularization and held-out human evals, not just the reward.
```

## Notes

- The sycophantic policy is gamed most: proxy 0.9 against true quality 0.35, a gap of 0.55.
- The gap between proxy and truth is reward hacking — why RLHF needs regularization and held-out human evals, not just the reward.
