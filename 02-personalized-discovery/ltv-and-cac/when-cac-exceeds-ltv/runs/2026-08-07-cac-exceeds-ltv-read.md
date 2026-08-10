# Run — when CAC exceeds LTV, executed on the three-channel read

**Date:** 2026-08-07
**Command:** `uv run python core/cac_exceeds_ltv.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 55's detour: acquisition channels differ in cost and in the
retention of the users they bring. This run computes five-month LTV for
three channels and marks the verdict.

## Output

```
cac exceeds ltv, read (revenue $5/user/month, 5 months):
  organic search  cac $2.00, ltv $12.15, ltv/cac 6.08 (profitable)
  referral        cac $3.50, ltv $10.70, ltv/cac 3.06 (profitable)
  paid installs   cac $8.00, ltv $7.50, ltv/cac 0.94 (loses money)

reading: referral clears its cost; paid installs do not.
The decision is not the install price - it is the months
after it. A channel with LTV below CAC pays the platform to
grow, and volume makes the loss larger.
```

## Notes

- Referral clears its cost at 3.06; paid installs lose money at 0.94 despite a similar profile at signup.
- The decision is not the install price — it is the months after it; a channel with LTV below CAC pays the platform to grow.
