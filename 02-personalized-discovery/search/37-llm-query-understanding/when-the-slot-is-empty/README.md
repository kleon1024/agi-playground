---
status: verified
level: applied
base: scratch
label: When the slot is empty
verified: 2026-08-07
---

# The empty slot makes retrieval decide

**Question:** [stage 37's LLM query understanding](../) parses queries
into slots. This chapter reads the executed comparison and asks what a
missing required slot does to retrieval.

**Before this:** [stage 37 — LLM query understanding](../) and its
executed intent-slot parser.

## The comparison, executed

The run ([record](runs/2026-08-07-slot-is-empty-read.md)) retrieves with
and without a filled origin slot:

| query | parse | retrieval |
|---|---|---|
| flights to tokyo | origin None, dest tokyo | broaden to all origins |
| flights from sin to tokyo | origin sin, dest tokyo | exact match |

## The reading

With origin missing, retrieval broadens to every origin — more
coverage, less precision; with the slot filled, the index answers
exactly. The empty slot is a decision, not a default: the system can
ask for the slot, broaden the query, or guess, and each has a measured
cost. Asking preserves precision but adds a turn; broadening preserves
the query's intent but returns a wider set; guessing risks filtering on
a value the user never stated.

## The fix and its trade

The fix is to treat an empty slot as a decision with a declared policy —
ask, broaden, or guess — because retrieval serves the keys it is given.
The executed comparison prices the two ends: with origin None, retrieval
broadens to every origin (more coverage, less precision); with origin
sin, the index answers exactly. The empty slot is not neutral: asking
preserves precision and adds a turn; broadening preserves the query's
intent and returns a wider set; guessing risks filtering on a value the
user never stated.

The trade, named: the three options buy different things — a turn, a
wider result set, or a false filter — and the policy must be chosen per
slot and per product surface, not left to the retrieval default. The
measurement that decides is precision-recall across the decision: the
system that asks only when the ask is cheap, broadens when the slot is
optional, and never guesses on a slot the query did not state.

## Who owns the loop

- **The retrieval team** owns the broaden, ask, or guess contract per
  slot.
- **The assistant team** owns the ask flow when the clarification is
  worth the extra turn.
- **The product owner** owns the cost tradeoff — the turn, the wider
  set, or the filter risk — per surface.

## Evidence boundary

The executed comparison over two declared queries (illustrative,
deterministic, assumed parses). It demonstrates the mechanism; real
query understanding needs the slot schema, the retrieval index, and
measured precision-recall across the decision.

## Check your mental model

Answer each before opening it.

**1. Why is a missing slot not a neutral event?**

<details>
<summary>Answer</summary>

Because retrieval serves the keys it is given. With origin None, the
index cannot restrict by origin, so every origin competes — the result
set widens and precision falls. The slot's absence is a constraint the
system silently drops, and the user experiences it as broader, less
relevant results. The parse's completeness directly shapes what the
index returns.

</details>

**2. What are the three options, and what does each cost?**

<details>
<summary>Answer</summary>

Ask, broaden, or guess. Asking adds a conversation turn but keeps
precision. Broadening returns results immediately but with more noise.
Guessing fills the slot with an assumed value and risks filtering on a
constraint the user never stated — the exact failure the over-parse
detour measures. The decision is which cost fits the product, and it
has to be made explicitly, not by default.

</details>

## Next

Back to [stage 37](../). The
[over-parse detour](../when-the-llm-over-parses/) shows the opposite
failure: a slot that was never missing because the LLM invented it.
