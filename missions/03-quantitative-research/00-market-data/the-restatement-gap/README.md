---
status: verified
level: applied
base: scratch
label: The restatement gap
verified: 2026-08-06
---

# The same period, two values, filed a year apart

**Question:** [stage 00's market data](../) builds a point-in-time panel.
This chapter reads the recorded check and asks what the restatement gap
actually looks like.

**Before this:** [stage 00's market data](../) and its recorded
point-in-time check.

## The gap, read

The run ([record](runs/2026-08-06-gap-read.md)) reads the recorded numbers:

| FY2015 value | filed |
|---|---|
| 176,223,000,000 | 2015-07-31 (first 10-K) |
| 174,472,000,000 | 2016-07-28 (restatement) |
| naive join would use | 174,472,000,000 (the restatement) |

## Two readings

**The same fiscal period carries two different values.** Microsoft's FY2015
was restated a year after the original 10-K, and a naive join keyed only on
the fiscal period silently uses the newer value — information that did not
exist on the decision date. The point-in-time join as of 2015-07-31 returns
176,223,000,000, which is what was actually knowable then. The gap is the
survivorship-adjacent error this stage exists to prevent.

**The corporate-action reconstruction is the sanity check beside it.** The
same run rebuilt dividend-adjusted prices from raw bars and matched Yahoo's
own adjclose exactly over 501 bars (median and max relative error both
0.000000, 8 dividends, 0 splits). The two halves of the run are the same
discipline — reconstruct what was knowable — applied to prices and to
fundamentals.

## Evidence boundary

The recorded point-in-time check (MSFT, 2y window, CIK 789019 Assets tag,
one restatement gap). It reads that artifact; it does not re-fetch live
data and the gap is one period of one company, chosen because it is sharp.

## Check your mental model

Answer each before opening it.

**1. Why is the restatement value "wrong" if it is the latest filing?**

<details>
<summary>Answer</summary>

Because "latest" and "knowable on the decision date" are different. The
restated 174,472,000,000 was filed in 2016 — a backtest as of 2015 has no
right to it. A naive join uses it anyway because it keys on the fiscal
period alone, which is exactly the point-in-time violation: the join must
be as of the decision date, not as of the latest filing.

</details>

**2. Why does the zero-residual reconstruction belong in the same chapter?**

<details>
<summary>Answer</summary>

Because it is the same claim tested on the other axis. The restatement gap
proves fundamentals change after the fact; the reconstruction proves prices
can be rebuilt to match the vendor's adjusted series exactly. Both are
"what was knowable when" — the price side confirms the reconstruction
method, and the fundamental side shows why the point-in-time discipline
matters even when prices are clean.

</details>

## Next

Back to [stage 00](../), or to
[the as-of join detour](../asof-vs-naive/) which generalizes the same gap
across many periods.
