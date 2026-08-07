---
status: verified
level: applied
base: none
label: When the rules collide
verified: 2026-08-06
---

# When does the rule engine return an empty set?

**Question:** [stage 07](../) runs declarative rules — blocks, boosts, caps
— and its demo shows one empty-set case (region EU). The empty set is a
property of the rule-by-context grid, not a single request: this chapter
maps the frontier.

**Before this:** [stage 07's rule engine](../), including its demo.

## The frontier, measured

The run ([record](runs/2026-08-06-rule-frontier.md)) sweeps region and the
per-creator cap across the stage's own rules:

| region | cap 1 | cap 2 | cap 3 | cap 4 |
|---|---:|---:|---:|---:|
| US | 3 kept | 6 kept | 6 kept | 6 kept |
| EU | empty | empty | empty | empty |

## Two readings

**The empty set is region-determined, not cap-determined.** EU empties at
every cap and US never does: the rules intersect to nothing for EU by
construction, and the cap — the knob that looks like the tunable one — is
irrelevant to the emptiness. The frontier is a vertical line in the grid.
An engine that only reports "no candidates" would hide that the cause is a
region policy, not a cap threshold.

**The audit is what makes the policy conversational.** The record shows the
capped decision's fired rule and its human-readable explanation ("creator
cap of 1 reached"). The "why was this shown" answer is attached to the
decision, which is the mission's requirement for an auditable rule layer —
the same property that lets an empty set be diagnosed by its solo-removal
breakdown instead of reported as a number.

## Evidence boundary

One synthetic item set, the stage's DEFAULT_RULES, two regions, four caps.
It maps this grid's frontier and shows the audit shape; it does not claim
the frontier transfers to other rule sets — that is the point of mapping it
per policy.

## Check your mental model

Answer each before opening it.

**1. Why does the cap — the knob that changes the US result — not change the
EU result?**

<details>
<summary>Answer</summary>

Because the EU empty set is produced by block rules that remove every
candidate before the cap stage runs. The engine's precedence is blocks
first (terminal), boosts, then caps — so a region whose blocks remove
everything never reaches the cap. The grid shows the emptiness is a
property of the block rules in the EU context, not of the cap parameter.

</details>

**2. What does the audit record add beyond the kept/capped counts?**

<details>
<summary>Answer</summary>

It attaches the cause to each decision — which rule fired and a
human-readable explanation — so a policy change can be argued about
concretely ("this item was capped because the creator cap of 1 was
reached") rather than through aggregate counts. It is also what makes an
empty set diagnosable: the solo-removal breakdown shows which rules would
empty it on their own, which the counts alone cannot.

</details>

## Next

Back to [stage 07's rule engine](../), or forward to
[stage 08's serving](../../08-serving/) where the filtered candidates get
scored under the latency budget.
