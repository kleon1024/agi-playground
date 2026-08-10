# Run — the automate-versus-gate boundary, read from the recorded arms

**Date:** 2026-08-08
**Command:** `uv run python core/product_boundary.py`
**Hardware:** Apple M1 Pro (32 GB), macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.08s real.
**Cost:** \$0 (local lane; the inputs were the mission's own recorded model
attempts, and no model was called).

## Purpose

The chapter's question is when an agent should act on its own and when a
human should gate it. This run reads the recorded arms and prints the
routing table a product decision needs: per tier and arm, resolve rate, cost
per delivered outcome, the always-frontier versus cheap-with-loop spread,
the total recorded spend, and the feedback-only slice.

## Output

```
the automate-versus-gate routing table, from recorded runs:

arm / tier            delivered  $/delivered
no-harness haiku        0/6              nan
no-harness sonnet       1/6           1.3744
no-harness opus         3/6           1.0924
harness haiku           6/6           0.1604
harness sonnet          6/6           0.5368
harness opus            6/6           0.8226
public haiku            6/6           0.1068
closing-loop pool       2/12          1.5256

total recorded spend across the 42 real attempts: $14.9034
feedback-only slice (no tools): 2/12 retries resolved
```

## Notes

- The 42 real attempts are the mission's own count (36 private across three
  tiers, plus 6 public); the closing-the-loop pool of 12 retries is listed
  separately as the feedback-only slice.
- `nan` is a zero-delivery cell (no-harness haiku), where cost per delivered
  is undefined.
- The routing spread is the product decision: harness haiku delivers 6/6 at
  \$0.1604 per delivered outcome, and the public set (6/6 at \$0.1068)
  reproduces that on a previously unseen codebase; the blind arms cost more
  per delivery and deliver less at every tier.
