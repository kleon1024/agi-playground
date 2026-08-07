# Run — new-user experience, executed on the cold-start runway read

**Date:** 2026-08-07
**Commands:** `uv run python core/cold_start.py --emit-log /tmp/cold-start-envelope.json`;
`uv run python prod/cold_start_audit.py /tmp/cold-start-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 51 introduces the new-user problem. This run measures NDCG@10
against the user's true taste as interactions accumulate, then emits
the per-path first-page cohort rows the production audit stratifies by
onboarding path.

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

cohort view (first page by onboarding path):
  path          traffic first-page ndcg retention
  popularity        60%           0.122      0.24
  right prior       20%           0.878      0.55
  wrong prior       10%           0.000      0.18
  no-ask            10%           0.050      0.20
  aggregate        100%           0.254      0.29

  reading: the aggregate first-page ndcg hides the path
  structure - the wrong-prior path scores 0.000 and loses
  more retention than the no-ask baseline, while 60% of new
  users arrive via popularity. Stratify by onboarding path
  before declaring the first-page policy healthy.
```

## Notes

- NDCG@10 rises from 0.122 (popularity only) to 0.878 after 20 interactions.
- At zero interactions popularity is the serving policy; onboarding priors are the lever that moves the first page before the trail exists.
- The cohort view is the case-finding half of the stage: the aggregate
  first-page number (0.254) blends paths, and the wrong-prior path
  (0.000 first-page NDCG, 0.18 retention) is below both the popularity
  default and the no-ask baseline. The audit reads the emitted envelope
  and returns the NEW-USER GAP verdict; see the audit record.
