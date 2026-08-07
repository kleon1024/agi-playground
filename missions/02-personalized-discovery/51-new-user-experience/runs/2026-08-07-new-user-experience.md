# Run — new-user experience, executed on the cold-start runway read

**Date:** 2026-08-07
**Command:** `uv run python core/cold_start.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 51 introduces the new-user problem. This run measures NDCG@10
against the user's true taste as interactions accumulate.

## Output

```
new-user experience, read (NDCG@10 vs the user's true taste):
  popularity only:               0.122
  personalized after  1 interactions: 0.429
  personalized after  5 interactions: 0.694
  personalized after 20 interactions: 0.878

reading: at zero interactions personalization has no signal,
so popularity is the serving policy and the first page is a
default decision. The trail improves NDCG 0.12 to 0.88 over
twenty interactions - a short runway, but one that must be
bridged. Onboarding priors are the lever that moves the
first page before the trail exists, and the detours show
what a wrong prior costs.
```

## Notes

- NDCG@10 rises from 0.122 (popularity only) to 0.878 after 20 interactions.
- At zero interactions popularity is the serving policy; onboarding priors are the lever that moves the first page before the trail exists.
