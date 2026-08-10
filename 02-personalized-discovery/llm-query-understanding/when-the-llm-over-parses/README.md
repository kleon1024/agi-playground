---
status: verified
level: applied
base: scratch
label: When the LLM over-parses
verified: 2026-08-07
---

# The LLM over-parses and invents a constraint

**Question:** [stage 37's LLM query understanding](../) parses queries
into slots. This chapter reads the executed over-parse and asks what an
invented slot does to recall.

**Before this:** [stage 37 — LLM query understanding](../) and its
executed intent-slot parser.

## The over-parse, executed

The run ([record](runs/2026-08-07-llm-over-parses-read.md)) parses one
query two ways:

| parse | result |
|---|---|
| over-parsed | dest tokyo, max_price cheap (invented) |
| honest | dest tokyo, max_price None (absent) |

## The reading

The over-parsed version invents max_price cheap and would filter the
index by a constraint the user never stated. The query says nothing
about price — "flights to tokyo" — so the invented slot silently
shrinks recall exactly like an over-eager rule: the index now excludes
every flight above the assumed price. LLM parsing needs a confidence
floor per slot: a slot is only filled when the model is confident the
query stated it, and an invented constraint is worse than a missing one
because it looks authoritative.

## The fix and its trade

The fix is a confidence floor per slot: a slot is only filled when the
model is confident the query stated it. The executed comparison prices
the failure: the over-parsed version invents max_price cheap and would
filter the index by a constraint the user never stated — "flights to
tokyo" says nothing about price, and the invented slot silently shrinks
recall exactly like an over-eager rule, excluding every flight above
the assumed price. An invented constraint is worse than a missing one
because it looks authoritative.

The trade, named: a confidence floor costs calibration and a slot
schema — deciding what counts as "the query stated it" is per-slot
work — and the alternative is a parse that over-commits structure the
query does not carry. The retrieval consequence is the same as an
over-eager rule: recall shrinks with no signal that a constraint was
invented, which is why the floor belongs to the parse contract, not to
the prompt.

## Who owns the loop

- **The query-understanding and LLM team** owns the slot schema and the
  confidence floor per slot.
- **The retrieval team** owns the key space the parse feeds, and the
  fallback when a slot is below confidence.
- **The product owner** owns the parse contract — when an invented
  constraint is acceptable and when the model over-commits.

## Evidence boundary

The executed comparison over one declared query (illustrative,
deterministic, assumed parses). It demonstrates the mechanism; real
query understanding needs the slot schema, a confidence floor, and
measured parse quality over logged queries.

## Check your mental model

Answer each before opening it.

**1. Why is an invented slot worse than a missing one?**

<details>
<summary>Answer</summary>

Because a missing slot is visible — the system knows it has to decide
(ask, broaden, guess). An invented slot looks authoritative: the parse
says max_price cheap, so the index filters by it, and nothing flags the
constraint as fabricated. The user's results shrink and the system
believes it understood the query. The silent failure is the dangerous
one, which is why the confidence floor has to gate each slot.

</details>

**2. How is this the same failure as an over-eager rule?**

<details>
<summary>Answer</summary>

Both add a constraint the query did not state. A rule engine that
defaults "flights" to cheap filters the same flights the invented slot
does; the mechanism differs (rules versus LLM parse) but the recall
loss is identical. Stage 37's point is that the LLM can produce the
over-eager rule's effect with complete confidence, so the defense —
confidence floors and honest parses — has to be explicit.

</details>

## Next

Back to [stage 37](../). The
[empty-slot detour](../when-the-slot-is-empty/) shows the honest
version of the same decision: a slot that really is missing.
