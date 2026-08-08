# Run — verification replacing score, read from the recorded ranking runs

**Date:** 2026-08-08
**Command:** `uv run python core/verification_replaces_score.py`
**Hardware:** Apple M1 Pro (32 GB), macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.10s real.
**Cost:** \$0 (local lane; the inputs were the mission's own recorded runs,
and no model was called).

## Purpose

The chapter's question is which mechanisms persist when the system generates
the answer instead of ranking the list. This run reads two committed records —
the LLM listwise-ranking run (stage 31) and the value-tree weight sweep
(stage 05) — and prints the two measured facts the argument rests on: the LLM
ranker reorders without a check, and a calibration break reorders the ranking
with no product-strategy change.

## Output

```
verification replacing score, read from the recorded ranking runs:

LLM listwise reorder: 4/5 positions changed -- a reorder with no
check against the pointwise order; the recorded cost is 'latency and prompt length, which is why LLM ranking sits at the top of a cascade, not over the whole candidate set'.

calibration break: click predictions inflated 1.6x reorders the
ranking -- order changed — with no change in product strategy, only in calibration.

value-tree auction: at trade_rate=0.2 the ad does not clear;
at trade_rate=0.8 it enters and displaces item_6 (organic value 0.499)

reading: the ranked list does not disappear -- it becomes the
retrieval input a generator conditions on. What becomes load-bearing
is the verification step: a reorder without a check and a
miscalibration that silently reorders are the failures the surface
must catch before the generated answer is shown.
```

## Notes

- The reorder fact (4/5 positions changed) comes from
  `recommendation/31-llm-ranking/runs/2026-08-07-llm-ranking.md`; the
  calibration break (1.6x inflation reorders with no strategy change) and the
  auction entry (`trade_rate=0.2` does not clear, `trade_rate=0.8` enters and
  displaces `item_6`, organic value 0.499) come from
  `shared/05-value-tree/runs/2026-07-30-weight-sweep-and-auction.md`.
- The chapter reads these as one failure family: a reorder is only worth
  trusting if something checks it, and calibration drift is a silent reorder
  that no ranking comparison will catch.
