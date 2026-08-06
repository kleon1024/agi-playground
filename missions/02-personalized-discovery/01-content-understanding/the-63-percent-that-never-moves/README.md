---
status: verified
level: applied
base: scratch
label: The 63 percent that never moves
verified: 2026-08-06
---

# The behavioural floor the threshold cannot touch

**Question:** [stage 01's content queue](../) applies a confidence
threshold to labels. This chapter reads the recorded sweep and asks what
the threshold can and cannot change.

**Before this:** [stage 01's content queue](../) and its recorded sweep.

## The constant, read

The run ([record](runs/2026-08-06-behavioral-floor.md)) reads the recorded
sweep:

| metric | at threshold 0.00 | at threshold 0.65 |
|---|---:|---:|
| union coverage | 100% | 72% |
| cold coverage | 100% | 25% |
| behavioural coverage | 63% | 63% |

## Two readings

**The content queue's boundary is a dial; the behaviour queue's is a fact.**
Union and cold coverage move with the threshold because they depend on the
labeller's confidence. Behavioural coverage is 63% in every row because it
depends on the log — items with interactions stay reachable regardless of
how the content labels are filtered. The two queues have different owners
of reach, and the threshold only reshapes the content side.

**A threshold can never rescue an item neither queue reaches.** The
behaviour queue stops at what the log recorded; the content queue stops at
what the threshold keeps. An item that is both cold and low-confidence
falls through both, and no threshold setting brings it back — which is why
the stage's cold-coverage number (25% at 0.65) is the honest cost of
precision, not a bug to tune away.

## Evidence boundary

The recorded synthetic sweep (300 items, 112 cold, one seed). It reads that
artifact; it does not re-run the harness and the 63% is a property of this
synthetic catalogue, not a production reach figure.

## Check your mental model

Answer each before opening it.

**1. Why does behavioural coverage not change between thresholds?**

<details>
<summary>Answer</summary>

Because the behaviour queue's reach is determined by logged interactions,
not by label confidence. It is 63% at 0.00 and 63% at 0.65 for the same
reason: the items that have been engaged are reachable no matter how the
content labels are filtered, and the items that have not are not. The
threshold is a label dial; the log is the behaviour queue's fixed input.

</details>

**2. What would 0% cold coverage at the extreme threshold mean?**

<details>
<summary>Answer</summary>

It would mean the content queue has been filtered until it covers nothing
cold — the limit of the trade this chapter reads. The union would shrink to
the behaviour queue's 63%, and every cold item would be unreachable. The
threshold at the extreme does not improve labels; it removes the tail
entirely, which is the same failure the threshold-trade detour reads at
0.65.

</details>

## Next

Back to [stage 01](../), or to
[the threshold trade](../when-the-threshold-rescues-the-tail/) which reads the
same sweep's precision-for-reach exchange.
