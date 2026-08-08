---
status: verified
level: applied
base: scratch
label: When the feature is missing
verified: 2026-08-07
---

# A missing feature default is a silent ranking decision

**Question:** [stage 43's feature store](../) guarantees identical reads.
This chapter asks what the store serves when the feature was never
written — a new item with no price yet — and answers: the default is a
policy choice that looks like bookkeeping.

**Before this:** [stage 43 — feature store](../) and its executed store
model.

## The default, executed

The run ([record](runs/2026-08-07-feature-is-missing-read.md)) adds a
new item, P1004, whose price is missing. The store serves a default price
of zero and ranks; the true price ranks again:

| item | ctr | default price | rank with 0 | rank with \$39 |
|---|---|---:|---|---|
| P1001 | 0.032 | \$49 | 2 | 1 |
| P1004 | 0.025 | \$0 | 1 | 2 |
| P1003 | 0.011 | \$19 | 3 | 3 |
| P1002 | 0.032 | \$89 | 4 | 4 |

## The reading

The missing price defaulted to zero, which rewards the item as if it were
free and promotes it to the top of the slate. The default is a policy
choice that looks like bookkeeping: nobody chose to rank P1004 first, but
the store's choice of zero did. The ranker cannot tell a real price from
a default, so the store must make the default explicit and auditable —
the rule engine (stage 07) is where the policy belongs, not buried in a
feature reader.

## The fix and its trade

The fix is an explicit, auditable missing-value policy: the feature
owner declares the default per feature, the store logs every read that
served a default, and the policy lives in stage 07's rule engine rather
than inside a feature reader. The executed read prices the failure — the
zero default promotes P1004 (ctr 0.025) above P1001 (ctr 0.032) and to
rank 1, where the true \$39 price puts it at rank 2 — so the store's
silent choice moved the slate as much as the real value would.

The trade is between two explicit policies, not between a default and
nothing. A default keeps the new item in the race but may rank it on a
value nobody chose; disqualifying the item on a missing feature protects
the rank but costs coverage for exactly the fresh items the store is
built to onboard. Whoever declares the default also declares the
disqualification rule, and the audit log is what makes either choice
reviewable instead of invisible.

## Who owns the loop

- **The feature-owner team** declares the default and whether a missing
  value disqualifies the item from ranking at all.
- **The ranking and rule-engine team** owns where the policy lives (stage
  07's rules, not the feature reader) and enforces it consistently.
- **The feature-store team** logs every default-served read so the
  decision can be audited after the fact.

## Evidence boundary

The executed read over four declared items (illustrative, deterministic).
It demonstrates the mechanism; real stores must choose per-feature
defaults, log when a default was served, and decide whether a missing
feature should disqualify the item from ranking at all.

## Check your mental model

Answer each before opening it.

**1. Why does a zero price outrank a higher-CTR item?**

<details>
<summary>Answer</summary>

Because the score subtracts price: a zero price removes the penalty, so
P1004 (ctr 0.025) scores above P1001 (ctr 0.032) even though it clicks
less. With the true \$39 price, the penalty returns and P1004 drops to
second. The default changed the rank as much as the real value would.

</details>

**2. What makes the default dangerous rather than merely wrong?**

<details>
<summary>Answer</summary>

Silence. A wrong price is a visible bug; a default is invisible, because
the ranker treats it like any other value. The store must log when a
default was served and who chose it, so the decision can be audited — the
same property stage 07's rule engine exists to guarantee.

</details>

## Next

Back to [stage 43](../). The [feature-divergence detour](../when-the-feature-diverges/)
is the other failure the store prevents: the two reads disagreeing about
the same item.
