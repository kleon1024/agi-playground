# Run — when the filter bubble closes, executed on the per-user exposure loop

**Date:** 2026-08-07
**Command:** `uv run python core/filter_bubble.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 45's detour: per-user personalization feeds the user's clicks back
into the ranking. This run reads how a single user's page narrows over
epochs.

## Output

```
filter bubble, read (per-user exposure by epoch):
  epoch 1: liked-category share 33%
  epoch 5: liked-category share 70%
  epoch 10: liked-category share 94%

reading: each epoch the user clicks the liked categories
and the ranking amplifies them; the rest decay. Liked
exposure climbs from a third to most of the page by epoch
10 - the bubble closes from the inside, and the user never
chose it. The feedback loop is not just a popularity story;
it is a per-user one, and the same multiplicative dynamics
that concentrate the head concentrate a user's view.
```

## Notes

- Liked-category share climbs from 33% at epoch 1 to 94% at epoch 10.
- The bubble closes from the inside, and the user never chose it; the same dynamics that concentrate the head concentrate a user's view.
