---
status: draft
level: frontier
base: none
label: Economics of autonomy
---

# The cheap run resolved everything. What did the delivery actually cost?

**Question:** [stage 05](../../cheap-or-expensive/) priced the mission's
autonomy in dollars per resolved task — and showed that the cheap tier's
three patches carried defects the tests could not see. That is the first
step of the economics this chapter completes: cost per *attempt* flatters
whichever agent fails cheapest, cost per *resolved* flatters whichever
fails last, and neither is the number a delivery decision turns on. The
delivery stack's economics object measures what a verified, landed,
surviving outcome actually cost.

**The artifact this chapter follows** is the metric map: every cost a
delivery system incurs, sorted by what it answers. The mission's recorded
runs sit on the map as the smallest honest instance.

**Before this:** [stage 05](../../cheap-or-expensive/) and the autonomy
stage's authorization matrix. This chapter prices what both decide.

## Why dollars per resolved task is not enough

The mission's own record is the proof. On resolve rate the harness reads
18/18; on patch generality it reads 6/9; the cheapest tier's patches all
carried defects outside the tested input space. A maintainer paying by
resolve rate saw the cheap tier as a bargain. The defects were priced
later — in a regression found in production, a rollback, a customer
impact — and that later price is invisible in the resolve-rate number. The
first lesson of delivery economics: **the cost that matters is the one
incurred after the run, and it is the hardest to see.**

## The metric map

A delivery system needs six numbers, and each answers a different question:

| Metric | It answers | Mission instance |
|---|---|---|
| Cost per attempt | how cheap is a try? | tier cost per attempt, recorded |
| Cost per resolved | how cheap is a fix that passes? | \$0.16 (haiku) vs \$0.82 (frontier) per resolved, recorded |
| Cost per verified outcome | how cheap is a fix that survives generality? | 6/9 generality makes the cheap tier's true cost 50% higher than resolve suggests |
| Human review minutes | how much senior time per outcome? | zero in the benchmark — no review step exists |
| Escaped defect cost | what does a shipped wrong fix cost? | not measured — the benchmark has no production |
| Time to external outcome | how long until the world sees a result? | task-seconds, not delivery-days |

The first two are benchmark economics; the last four are delivery
economics, and the tutorial's honest position is that the mission can
measure only the first two. The boundary between them is the boundary
between the verified core and the design agenda.

## The automation threshold

The economics object exists to answer one decision: *should this task be
automated at all?* The threshold is a comparison, not a constant:

```text
automate when:  cost per verified outcome + review minutes < human cost
                AND escaped-defect risk is within tolerance
                AND rollback is possible
```

Each term maps to the objects already built: cost per verified outcome is
the economics object, review minutes is the human-in-the-loop economy
([autonomy stage](../../autonomy-and-orchestration/)), escape risk is the
trust boundary's residual after verification, rollback is the side-effect
semantics' compensation. The threshold is why the authorization matrix's
task types have different autonomy levels — the economics differs per
type, so the gate differs per type.

## The value of information

One more cost is easy to miss and decides whole projects: the value of
information. A task whose outcome tells you something new — an experiment,
a feasibility probe, a migration dry-run — has value beyond its direct
result, and the correct spend on it is higher than its direct ROI.
Conversely, a task that produces nothing learnable is pure cost. The
delivery stack's RunLedger exists partly for this: it accumulates the
information each run produced, so the next decision prices the knowledge
the stack already has.

## What this does not say

It does not claim the mission can measure delivery economics — it
explicitly cannot, and the chapter says so. It does not claim the six
metrics are exhaustive; it claims they are the ones that distinguish a
benchmark from a delivery. And it does not claim automation is a
threshold you compute once — every term drifts (model prices, review
supply, defect rates), which is why the threshold is recomputed, not
memorized.

**Next:** economics decides what to automate. The last object decides what
the system may change about itself — [bounded-improvement](../bounded-improvement/).
