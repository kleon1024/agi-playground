# Run — when the user is new, executed on the onboarding-prior read

**Date:** 2026-08-07
**Command:** `uv run python core/user_is_new.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 51's detour: with no trail, the platform can ask the new user what
they are here for. This run serves the first page under a right prior and
a wrong one, and reads the NDCG gap.

## Output

```
user is new, read (first page NDCG@10 with different priors):
  popularity only:            0.122
  onboarding prior on [2, 3]: 0.878
  onboarding prior on [0, 4]: 0.000

reading: the right prior lifts the first page from 0.122 to
0.878; the wrong one collapses it to 0.000. Onboarding is a
high-leverage bet - it decides the first page for a user
with no trail, and it is wrong whenever users do not say
what they mean or the option set misleads them.
```

## Notes

- The right prior lifts first-page NDCG from 0.122 to 0.878; the wrong one collapses it to 0.000.
- Onboarding is a high-leverage bet, wrong whenever users do not say what they mean or the option set misleads them.
