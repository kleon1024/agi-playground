# Run — the exposure-concentration audit over the served log

**Date:** 2026-08-07
**Commands:** `uv run python core/popularity_collapse.py --emit-log /tmp/loop-envelope.json`;
`uv run python prod/exposure_audit.py /tmp/loop-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 45's loop hides itself: every logged label was produced under the
serving policy, so the log endorses the policy that wrote it. This run
is the case-finding half of the stage: how a team finds the
concentration. The core script emits the per-item exposure ledger; the
production audit bands the catalogue by true CTR and reports impression
share and measured-versus-true CTR per band.

## Output

```
exposure-concentration audit over the served log:
  total impressions: 1500
  head   5 items: 1485 impressions (99%), measured ctr 0.0545, true ctr 0.0460, never shown 0
  mid   10 items:   10 impressions (1%), measured ctr 0.0000, true ctr 0.0310, never shown 0
  tail   5 items:    5 impressions (0%), measured ctr 0.0000, true ctr 0.0160, never shown 0

verdict: CONCENTRATED -- the head holds nearly all exposure and
the tail's CTR is measured on 5 impressions
(0.0000), so the log cannot prove the tail is worse; it only
proves the tail was not shown.
  head impression share: 99%;
  tail impression share: 0%,
  tail true ctr 0.0160 vs measured 0.0000.
```

## Notes

- The tail's true CTR (0.0160) is higher than what the log measured
  (0.0000), but the point is not the gap — it is that five impressions
  cannot estimate anything. The log has no evidence about the tail, so
  "the tail is worse" is unprovable from the served data.
- The audit asks the question Mansoury et al. measure in production-style
  runs: exposure concentrates, the log's evidence about the tail
  evaporates, and the loop amplifies the initial advantage (Mansoury et
  al., "Feedback Loop and Bias Amplification in Recommender Systems",
  CIKM 2020).
