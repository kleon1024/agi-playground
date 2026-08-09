# Run — the intent-to-delivery gap, read from the recorded arms

**Date:** 2026-08-08
**Command:** `uv run python core/intent_delivery.py`
**Hardware:** Apple M1 Pro (32 GB), macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.14s real.
**Cost:** \$0 (local lane; the inputs were the mission's own recorded model
attempts, and no model was called).

## Purpose

The chapter's question is where a stakeholder intent stops being delivered.
This run reads the three recorded arms — the 18 blind no-harness calls, the
18 full-harness tool-loop attempts, and the 12 closing-the-loop retries —
and prints, per arm and per tier, how many attempts produced a deliverable
at all and how many were delivered (scored resolved).

## Output

```
intent-to-delivery, read from the recorded mission-04 arms:

no-harness (blind call): 18 attempts, 5/18 produced a deliverable, 4/18 delivered; cost $5.144 total, 1793s wall-clock
  haiku   0/6 delivered, $nan/delivered
  opus    3/6 delivered, $1.0924/delivered
  sonnet  1/6 delivered, $1.3744/delivered
full harness (tool loop): 18 attempts, 18/18 produced a deliverable, 18/18 delivered; cost $9.119 total, 1555s wall-clock
  haiku   6/6 delivered, $0.1604/delivered
  opus    6/6 delivered, $0.8226/delivered
  sonnet  6/6 delivered, $0.5368/delivered
closing-the-loop (feedback, no tools): 12 attempts, 2/12 produced a deliverable, 2/12 delivered; cost $3.051 total, 851s wall-clock
  haiku   0/6 delivered, $nan/delivered
  opus    1/3 delivered, $1.2604/delivered
  sonnet  1/3 delivered, $1.3057/delivered

reading: intent is delivered only when the loop turns it into a
deliverable and verifies it. The blind call produced a patch-shaped
object in 5/18 attempts but delivered 4/18;
$2.917 was spent on attempts that never delivered.
```

## Notes

- "Produced a deliverable" means `patch_applied` where the log records it
  (blind and retry arms); the harness log has no such column, so a resolved
  attempt is its scored deliverable. The contrast is the point: the blind arm
  produced a patch-shaped object in 5/18 attempts and delivered 4/18, while
  the harness arm delivered 18/18.
- `nan` rows are tiers with zero deliveries (no-harness haiku, and haiku in
  the retry slice); dividing cost by zero resolved attempts is not reported
  as a price.
- The harness arm's higher total cost (\$9.119 vs \$5.144) buys 18 deliveries
  instead of 4; per delivered outcome it is cheaper (\$0.51 vs \$1.29).
