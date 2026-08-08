---
status: verified
level: applied
base: scratch
label: When the groups cross
verified: 2026-08-07
---

# The fairness verdict flips with the definition

**Question:** [stage 53's allocation](../) measured the price of a
floor. This chapter asks who the floor protects, and answers: the same
served allocation can look fair or unfair depending on how the protected
group is defined — across the whole catalogue the tail category clears
its floor, and split by segment the majority segment leaves it below.

**Before this:** [stage 53 — fairness and allocation](../) for the
exposure budget being measured, and [stage 50 — cost per
query](../../50-cost-per-query/) for the same aggregate-vs-slice
discipline applied to compute.

## The flip, executed

The run ([record](runs/2026-08-07-groups-cross-read.md)) measures the
tail category's exposure under a 10% floor, across the catalogue and by
segment:

| definition | tail exposure | vs floor |
|---|---:|---:|
| mobile | 8% | −2% |
| desktop | 15% | +5% |
| catalogue-wide | 10.1% | +0.1% |

## The reading

Across the whole catalogue the tail clears the floor (10.1% vs 10%), so
the allocation looks fair. Split the same allocation by segment and the
mobile segment — 70% of traffic — leaves the tail at 8%, below the
floor. Neither number is wrong; they answer different questions, but the
definition decides the verdict. Exposure bias is multi-sided: the
serving surface, the segment, and the catalogue each produce a different
exposure statement (Abdollahpouri et al., "Multi-sided Exposure Bias in
Recommendation", KDD Workshop on Industrial Recommendation Systems
2020), and group definitions themselves carry demographic assumptions
(Ekstrand et al., "All the Cool Kids, How Do They Fit In?", FAT* 2018).

The production consequence is that "is the allocation fair" is
unanswerable until someone names the group. The fix is to define the
group before measuring fairness, report both views, and treat the
definition as a policy decision owned by the team setting the floor —
not a reporting detail the dashboard picks.

## The fix and its trade

The fix is to define the group before measuring fairness, report both
views, and treat the definition as a policy decision owned by the team
setting the floor — not a reporting detail the dashboard picks. The
executed flip prices the failure: under a 10 percent floor the mobile
segment leaves the tail at 8 percent (minus 2), desktop at 15 percent
(plus 5), and the catalogue-wide view at 10.1 percent (plus 0.1) — the
same served allocation looks fair and unfair at once, and the
definition decides the verdict.

The trade is that no definition is neutral: group definitions carry
demographic assumptions (Ekstrand et al., FAT* 2018), and reporting per
segment costs dashboard and analysis complexity where the aggregate was
cheap. The catalogue number is not a lie — it is the average the
majority segment's shortfall and the minority's surplus cancel into —
and the repair is to name the protected group before reading any number,
so a fairness report is a verdict on a declared definition, not a
dashboard default.

## Who owns the loop

- **The policy and floor-setting team** owns the group definition, the
  decision that makes the fairness verdict answerable.
- **The measurement team** reports exposure per segment, so the
  aggregate that clears the bar cannot hide the majority segment that
  does not.
- **The product team** names the segments the product actually serves,
  since the definition must match the surface the allocation runs on.

## Evidence boundary

The executed exposure table over two declared segments (illustrative,
deterministic). It demonstrates the mechanism; real fairness
measurement must name its group definitions and report per-segment
exposure, because the aggregate that clears the bar hides the majority
segment that does not.

## Check your mental model

Answer each before opening it.

**1. Why is neither exposure number wrong?**

<details>
<summary>Answer</summary>

Because they answer different questions: "does the tail clear its floor
across the whole catalogue" and "does the tail clear its floor where
most users actually are". Both are computed from the same served
allocation. The catalogue number is not a lie — it is the average that
the majority segment's shortfall and the minority segment's surplus
cancel into.

</details>

**2. How would you catch this in a real fairness report?**

<details>
<summary>Answer</summary>

By asking who the protected group is before reading the number, and by
demanding the exposure split by the segments the product actually
serves — surface, device, cohort — not just the catalogue-wide
aggregate. If the definition is not written down, the number is not a
fairness verdict, it is a dashboard default.

</details>

## Next

Back to [stage 53](../). The allocation must be measured on a named
group; [stage 54 — online experiments](../../54-online-experiments/)
asks how the platform proves the allocation's effect on users, where the
same slice discipline applies to experiment analysis.
