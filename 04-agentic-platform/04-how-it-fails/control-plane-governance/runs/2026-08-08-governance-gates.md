# Run — the reconciliation gate, read from the recorded arms

**Date:** 2026-08-08
**Command:** `uv run python core/governance_gates.py`
**Hardware:** Apple M1 Pro (32 GB), macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.24s real.
**Cost:** \$0 (local lane; the inputs were the mission's own recorded model
attempts, and no model was called).

## Purpose

The chapter's question is which gates stop the failures that actually
happen. This run reads the recorded arms and prints three measured facts:
how many blind calls a reconciliation-style verification gate would have
rejected before delivery and what those undelivered attempts cost; the
tampering and regression record across all 54 real model calls; and the cost
of the gate itself, read as the harness's per-delivered cost versus the
blind call's.

## Output

```
reconciliation gate, read from the recorded runs:

blind calls the gate would reject before delivery: 14/18
cost of those undelivered attempts: $2.917, 1305s wall-clock
tampering across 54 real attempts: 0
regressions across 54 real attempts: 0

gate cost, read as the verification the harness already runs:
  blind call: $5.144 total, $1.2859/delivered (4/18)
  harness:    $9.119 total, $0.5066/delivered (18/18)

reading: the gate is the scored verification step, and it is
cheap relative to what it catches -- the blind call's own failures
cost $2.917 before the gate would have rejected them.
```

## Notes

- The 54 real model calls are the 42 attempts the mission's own report counts
  (36 private + 6 public) plus the 12 closing-the-loop retries of already-
  failed blind calls; the two counts differ because a retry is a second call
  on the same attempt.
- The gate is modeled as the scored verification step: any blind call whose
  verdict is not `resolved` is rejected before delivery (14/18: 12
  target_still_failing plus 2 timeouts). Its cost is the verification the
  harness already runs, and the harness's per-delivered cost (\$0.5066)
  remains below the blind call's (\$1.2859) even with that verification
  included.
- Zero tampering and zero regressions across all 54 calls is the recorded
  record, reported honestly: the guardrail has never fired on a real attempt.
