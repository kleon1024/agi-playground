---
status: verified
level: applied
base: scratch
label: When the rule is a typo
verified: 2026-08-07
---

# The rule nobody tested

**Question:** [stage 07's rule engine](../) applies declarative
constraints to the slate. This chapter reads the executed typo run and
asks how a rule can fail without ever looking broken.

**Before this:** [stage 07 — rule engine](../) and its executed rules.

## The failure, executed

The run ([record](runs/2026-08-07-typo-read.md)) applies the intended
rules and a version with one misspelled attribute:

| item | intended | typo |
|---|---|---|
| fresh sneakers | keep | drop (silent) |
| used jacket | keep | drop (silent) |
| vintage lamp | drop | drop (same) |

## Two readings

**A typo'd attribute matches nothing, silently.** The misspelled key
defaults to False, so every item fails the rule and the engine returns an
empty set. Nothing throws, nothing logs — the empty set is a valid output
for a rule engine, which is exactly why the failure is invisible. The
intended rule would have kept two items; the typo keeps zero.

**Rule engines need a coverage check, not just a unit test.** A rule that
matches no real item is dead code wearing a policy. The fix is a runtime
invariant: every rule must match at least one item in the catalog, and a
rule that matches none is a defect. The executed run is the minimal
demonstration — the two rows marked silent are the ones a coverage check
would have caught before the empty set ever reached a user.

## Evidence boundary

The executed hand-built rule table (illustrative, deterministic). It
demonstrates the silent-failure mechanism; real catalogs are large enough
that the same typo would silently remove a class of items, not just three
rows.

## Check your mental model

Answer each before opening it.

**1. Why does the typo produce an empty set instead of an error?**

<details>
<summary>Answer</summary>

Because the engine reads the attribute defensively — a missing key
defaults to False rather than raising. That defensiveness is usually
correct, but it converts a programming mistake into a data outcome: the
rule says "in stock only" and the typo makes every item look out of
stock. The engine faithfully executes a rule that means something other
than what the author wrote.

</details>

**2. What would a coverage check add beyond tests?**

<details>
<summary>Answer</summary>

A test checks the rules against fixed examples; coverage checks the rules
against the live catalog. The typo passes a test written with the correct
attribute name, because the test author uses the right spelling. Coverage
catches what tests cannot: the rule as written matches nothing that
exists, which is a different failure than matching the wrong things. The
executed run is the evidence a coverage gate would need — match counts
per rule, with zero as a defect.

</details>

## Next

Back to [stage 07](../), or to
[the collision of two rules](../when-the-rules-collide/) for the
interaction failure on the same engine.
