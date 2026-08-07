---
status: verified
level: applied
base: scratch
label: When the ad load moves
verified: 2026-08-07
---

# The ad load moves and displaces organic value

**Question:** [stage 42's marketplace economics](../) prices the
platform's levers. This chapter reads the executed ad-load sweep and
asks where the marginal ad stops paying.

**Before this:** [stage 42 — marketplace economics](../) and its
executed take-rate model.

## The sweep, executed

The run ([record](runs/2026-08-07-ad-load-moves-read.md)) fills a
ten-slot page with ads:

| ads | ad revenue | organic value | total |
|---|---:|---:|---:|
| 0 | \$0.00 | \$1.00 | \$1.00 |
| 1 | \$0.25 | \$0.90 | \$1.15 |
| 2 | \$0.40 | \$0.80 | \$1.20 |
| 3 | \$0.45 | \$0.70 | \$1.15 |

## The reading

Total value peaks at two ads (\$1.20) and falls after — the first ad is
the most valuable (\$0.25), each extra ad earns less, and the third ad
costs more organic value than it brings in. The ad load is a
marketplace decision, not a revenue default: every ad displaces an
organic slot, and the displacement is the same trade stage 18's
externality priced, now set by the platform choosing how many ads a page
carries.

## Evidence boundary

The executed sweep over a declared ten-slot page (illustrative,
deterministic, assumed ad and organic values). It demonstrates the
trade; real ad load needs measured organic-value loss per position and
the advertiser demand curve, which a live marketplace provides.

## Check your mental model

Answer each before opening it.

**1. Why does the third ad destroy value instead of adding it?**

<details>
<summary>Answer</summary>

Because its revenue (\$0.05) is less than the organic value it
displaces (\$0.10). The first two ads earn more than the slots they
took — total rises to \$1.20 — but the third ad's marginal revenue is
exhausted while every ad still costs a full organic slot. The page
peaks at two ads because the marginal ad stopped paying for its
displacement.

</details>

**2. How is this the same decision as stage 18's externality?**

<details>
<summary>Answer</summary>

Stage 18 priced the ad's displacement — the organic value it pushes
out — and the value tree (stage 05) decided whether the ad cleared the
bar. The ad-load sweep is the aggregate version of that per-slot
decision: the platform chooses the load, and the total curve shows the
point where the marginal ad's revenue no longer covers the organic
value it displaces. Same trade, marketplace scale.

</details>

## Next

Back to [stage 42](../). The
[take-rate detour](../when-the-take-rate-is-too-high/) shows the other
platform lever with the same peak shape: the cut the marketplace takes.
