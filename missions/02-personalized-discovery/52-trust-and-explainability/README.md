---
status: verified
level: applied
base: scratch
label: Trust and explainability
verified: 2026-08-07
---

# An explanation is only as good as the claim the user can check

**Question:** stages 05-07 built the score and the rules. This stage asks
what the user is told about why an item was shown, and answers: for one
shown item, the score is a sum of contributions, and the attribution that
builds trust is the one whose largest term the user can actually check.

**Before this:** [stage 05 — value tree](../05-value-tree/) for the score
combination being explained, and [stage 07 — rule engine](../07-rule-engine/)
for the auditable-decision discipline this continues.

## The contribution table, executed

The run ([record](runs/2026-08-07-trust-and-explainability.md)) breaks
one item's score into contributions:

| feature | value | weight | contribution | share |
|---|---:|---:|---:|---:|
| price | 3.0 | -0.008 | -0.0240 | penalty, verifiable |
| category affinity | 0.2 | +0.040 | +0.0080 | 19%, verifiable |
| similar users bought | 0.9 | +0.022 | +0.0198 | 47%, unverifiable |
| you viewed this category | 0.4 | +0.035 | +0.0140 | 33%, verifiable |

## The mechanism, named

The largest contribution is "similar users bought", which the user cannot
check — no record of similar users exists on their side. The verifiable
claims ("you viewed this category", "category affinity") are smaller.
Trust is built on explanations the user can falsify, not on the term with
the largest coefficient: an explanation succeeds when the user can
confirm it against what they actually did, and fails when the biggest
term is a black box.

## Why this belongs in the mission

The mission's value tree (05) made the score a product decision; this
stage makes the score legible to the person it ranks for. The rule
engine (07) already guaranteed "why was this shown" has an auditable
answer for rules; explainability extends the same promise to the learned
score, and it is the surface where the mission's trust claim is actually
tested — a user who cannot check the page stops believing the platform,
and the detours measure exactly how fast.

## Evidence boundary

The executed attribution over one declared item (illustrative,
deterministic). It demonstrates the mechanism; real explanation quality
must be measured on users — verifiability, opt-out rate, and whether the
explanation changes retention — not assumed from the presence of a
"why" button.

## Check your mental model

Answer each before opening it.

**1. Why is "similar users bought" the wrong headline even though it is
the biggest contribution?**

<details>
<summary>Answer</summary>

Because the user cannot check it: they have no view of "similar users",
so the claim is unfalsifiable. An explanation the user cannot verify is
an assertion, not an explanation. The verifiable terms — what they viewed,
which category they like — are smaller but real, and leading with them is
what makes the page trustworthy.

</details>

**2. How is this connected to the rule engine's audit promise?**

<details>
<summary>Answer</summary>

Stage 07 made rule decisions auditable; this stage makes learned-score
decisions verifiable. Both answer "why was this shown" — the rule engine
for policy, attribution for the model. The difference is the audience:
an audit is for the operator, an explanation is for the user, and the
two fail differently (the detours show an operator-facing metric and a
user-facing one).

</details>

## Next

The explanation must be verifiable; stage 53 asks how the page is
allocated across the whole catalogue. A detour from here: [the
attribution that explains the score tells a story the score did
not](when-the-explanation-is-wrong/) — the executed read: the largest
coefficient says "similar users bought" while the largest contribution
is the price term.

Another detour: [a false explanation burns trust faster than a missing
one](when-trust-erodes/) — the executed read: a 5% false rate nearly
doubles opt-outs, and at 50% a seventh of users leave.
