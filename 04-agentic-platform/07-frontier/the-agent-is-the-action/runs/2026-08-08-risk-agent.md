# Run — the agent as the action, read from the recorded mission-04 arms

**Date:** 2026-08-08
**Command:** `uv run python core/risk_agent.py`
**Hardware:** Apple M1 Pro (32 GB), macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.10s real.
**Cost:** \$0 (local lane; the inputs were the mission's own recorded model
attempts, and no model was called).

## Purpose

The chapter's question is what reconciliation costs when the agent does not
recommend an action but is the action. This run reads the recorded failure
taxonomy, the zero-failure contrast, and the reconciliation-gate read, and
prints the un-reconciled agent's record (the blind call) against the
reconciled one (the harness) — the evidence the chapter's argument stands on.

## Output

```
the agent as the action, read from the recorded mission-04 arms:

the un-reconciled agent (blind call, 18 attempts):
  target_still_failing 12/18, eleven of them a diff
  git apply rejects outright; timeout 2/18
  a reconciliation gate would reject 14/18 before delivery,
  at $2.917 and 1305s of wall-clock
  tampering record: 0 across 54 real attempts

the reconciled agent (harness, 18 attempts):
  resolved 4/18 (harness 18/18)
  every failure category other than resolved: 0/18

reading: when the agent is the action, the action must be
reconciled before it lands. The blind call is the un-reconciled
agent: 14 of 18 actions would be rejected by a gate that checks
the verdict at all. The harness is the reconciled agent: the same
18 attempts all resolve because verification is inside the loop,
and the gate's own cost is below the blind call's per-delivered
price. Reconciliation is not overhead; it is the mechanism that
turns an agent that acts into one a risk owner can sign off on.
```

## Notes

- Every number is re-read from committed runs, not re-measured: the
  taxonomy (12/18 target_still_failing, eleven of them a non-applying diff,
  2/18 timeout) comes from
  `04-how-it-fails/runs/2026-08-01-failure-taxonomy.md`; the harness
  contrast (resolved 4/18 blind vs 18/18 harness, every other category 0/18)
  from `04-how-it-fails/the-zero-failure-taxonomy/runs/2026-08-06-taxonomy-read.md`;
  and the gate read (14/18 rejected, \$2.917 and 1305s, zero tampering across
  54 calls) from `07-frontier/control-plane-governance/runs/2026-08-08-governance-gates.md`.
- The chapter reads the blind call as the risk-control analogue of an agent
  that acts without reconciliation: the verdict is produced, and nothing
  checks it before it would land. The gate the harness already runs is the
  reconciliation owner, priced at \$0.5066 per delivered outcome against the
  blind call's \$1.2859.
