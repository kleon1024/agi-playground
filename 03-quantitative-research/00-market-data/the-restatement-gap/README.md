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

## The fix and its trade

The fix is the point-in-time join the stage records — key on the filing
date, not the fiscal period — with the corporate-action reconstruction run
beside it as a sanity check. The restatement read shows why both halves
belong together: the naive join silently picks the 2016 restatement for a
decision made in 2015 (a 1.0% equity error on MSFT's FY2015 Assets), while
the reconstruction proves the price side can be rebuilt to match the
vendor's adjusted series exactly (zero residual over 501 bars). The two
checks are the same discipline — what was knowable when — applied to two
axes.

The trade is what the point-in-time discipline actually costs. The
restatement value is not "wrong" in the latest-filing sense; it is wrong
only relative to the decision date, so an as-of panel deliberately lags
the newest restatement until it is filed. The reconstruction, in turn, is
only a sanity check for the corporate-action part of the adjustment: it
cannot catch vendor errors that come from a different source
(survivorship filtering, bad ticker mapping), and it requires clean raw
bars to run. Survivorship bias in backtests is documented at least as far
back as Elton, Gruber & Blake, "Survivorship Bias and Mutual Fund
Performance" (Review of Financial Studies, 1996), and the point-in-time
database is a commercial category (Compustat's) because this class of
error was common enough to pay to eliminate — the fix here is the in-house
version of that product.

## Who owns the loop

Two owners, one contract:

- **The data owner** owns the availability timestamp on every fact and the
  corporate-action reconstruction that certifies the price series. The
  point-in-time panel is only as trustworthy as this metadata.
- **The research platform** owns the join: a backtest may only read the
  panel as of a decision date, and the naive join keyed on fiscal period
  is the failure mode the platform exists to prevent.

The strategy inherits the panel: if the timestamp is wrong, the backtest is
wrong in a way that looks exactly like a measurement error — which is why
the restatement gap has to be checked per-company, not assumed away.

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
