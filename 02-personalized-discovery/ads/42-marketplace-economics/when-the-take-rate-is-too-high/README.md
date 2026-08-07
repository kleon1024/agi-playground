---
status: verified
level: applied
base: scratch
label: When the take rate is too high
verified: 2026-08-07
---

# The take rate is too high and the marketplace collapses

**Question:** [stage 42's marketplace economics](../) prices the
platform's cut. This chapter reads the executed sweep past the peak and
asks where greed becomes collapse.

**Before this:** [stage 42 — marketplace economics](../) and its
executed take-rate model.

## The collapse, executed

The run ([record](runs/2026-08-07-take-rate-is-too-high-read.md)) sweeps
the take rate past its peak:

| rate | volume | revenue |
|---|---:|---:|
| 30% | 520 | \$156 |
| 50% | 200 | \$100 |
| 70% | 0 | \$0 |
| 85% | 0 | \$0 |

## The reading

Revenue peaks around 30-40% and collapses past 70% — at 85% the volume
is nearly gone and revenue is a fraction of the peak. The platform's
greed is measured in lost volume: every point of take rate above the
threshold drives transactions away faster than the per-transaction cut
grows. The shape is the same as the reserve (stage 28) and the ad load:
a platform lever that prices its own market out of existence when
pushed too far.

## The fix and its trade

The fix is to price the rate at the measured revenue peak instead of
raising it toward the per-transaction ceiling: estimate the actual
volume-response curve first, then set the rate at the curve's peak and
move it only against measured response. The stage's own elasticity
audit ([run](../runs/2026-08-08-elasticity-sweep.md)) is the same
discipline — the peak sits at 42.0% on a sticky market and 25.0% on an
elastic one, so a rate that is "too high" is a function of the demand
curve, not a number. The trade is that the fix costs the platform the
revenue it could extract in the short run, and it needs the measured
elasticity, which only a live marketplace provides: every point of
take rate above the peak buys per-transaction cut at the price of
volume, and the same rate can be the optimum on one curve and the
collapse on another (Rysman 2009, "The Economics of Two-Sided
Markets", Journal of Economic Perspectives 23(3):125-143, doi
10.1257/jep.23.3.125).

## Evidence boundary

The executed sweep over a declared volume-response model (illustrative,
deterministic). It demonstrates the shape; real take-rate decisions need
the actual demand elasticity and measured volume response, which only a
live marketplace provides.

## Check your mental model

Answer each before opening it.

**1. Why does volume hit zero instead of asymptoting?**

<details>
<summary>Answer</summary>

Because at a high enough rate the transaction is not worth doing — the
cut exceeds what either side gains, so the marketplace has nothing to
facilitate. The executed model collapses at 70%: volume 0, revenue \$0.
The demand curve does not just bend; it dies, which is the collapse the
"too high" in the title names.

</details>

**2. How is this the same shape as the reserve and the ad load?**

<details>
<summary>Answer</summary>

All three are levers that raise revenue per unit while shrinking
volume, with a peak beyond which the market loses. The reserve (stage
28) raises the price floor and drops demand; the ad load displaces
organic value; the take rate prices the whole marketplace. Each has its
own curve, and each peaks — optimizing any lever in isolation ignores
that they share the same elasticity shape.

</details>

## Next

Back to [stage 42](../). The
[ad-load detour](../when-the-ad-load-moves/) shows the same curve on
the other platform lever: how many ads a page carries.
