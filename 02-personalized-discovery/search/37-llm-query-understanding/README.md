---
status: verified
level: applied
base: scratch
label: LLM query understanding
verified: 2026-08-07
---

# The raw string becomes the keys retrieval serves

**Question:** stage 10's query understanding was rule-based. This stage
asks what an LLM does to the same job and answers: it parses the raw
string into an intent and slots directly — and it can invent slots,
which makes the parse a decision, not a lookup.

**Before this:** [stage 10 — query understanding](../10-query-understanding/)
for the key space retrieval must serve, and [stage 36 —
conversational search](../36-conversational-search/) for the session
that the parsed slots feed into.

## The parse, executed

The run ([record](runs/2026-08-07-llm-query-understanding.md)) parses
three queries:

| query | intent | slots |
|---|---|---|
| cheap flights to tokyo | flight_search | origin None, dest tokyo, max_price cheap |
| 2 bedroom apartment rent | housing_search | bedrooms 2, type apartment, action rent |
| how do i return an item | support | topic returns |

## The mechanism, named

The LLM reads the raw string and emits a structured key space: an
intent and the slots that intent needs. That is stage 10's job, now
done by a model that can handle phrasing stage 10's rules would miss —
"2 bedroom apartment rent" becomes housing_search with three slots.
The frontier cost is trust: the parse can be incomplete (origin is
None) or overcomplete (max_price invented), and both change what
retrieval serves, which the two detours price.

## Why this belongs in the mission

The funnel depends on a clean key space: retrieval can only serve the
keys it is given. An LLM parser widens what the funnel can understand,
and it introduces a failure the rule-based version did not have —
invented constraints that silently shrink recall. This stage keeps the
mission's discipline: the LLM is admitted where it changes the
decision, and its error modes are measured, not assumed away.

## Evidence boundary

The executed parse over three declared queries (illustrative,
deterministic, assumed LLM output). It demonstrates the mechanism; real
query understanding needs the model, a slot-confidence floor, and
measured parse quality over logged queries, which the detours quantify.

## Check your mental model

Answer each before opening it.

**1. What does the LLM parser add over stage 10's rules?**

<details>
<summary>Answer</summary>

Coverage of phrasing the rules would miss. A rule list maps known
patterns; the LLM handles paraphrases, multi-slot queries, and
colloquial phrasing — "2 bedroom apartment rent" becomes a structured
housing_search that a small rule set might not catch. The price is
that the parse is probabilistic, so it needs a confidence floor per
slot.

</details>

**2. Why is a missing slot a decision rather than a default?**

<details>
<summary>Answer</summary>

Because retrieval serves the keys it is given. Origin None means the
index cannot restrict by origin — the query either broadens to every
origin (more coverage, less precision) or the system asks for the slot.
Each choice has a measured cost, which is the empty-slot detour's point:
the parse is not finished until every required slot is either filled,
broadened, or explicitly asked for.

</details>

## Next

This closes the frontier search track (stages 35-37). The mission's ads
frontier begins next with [stage 38 — interleaving
experiments](../../ads/38-interleaving-experiments/).

A detour from here: [the slot is empty and retrieval has to
decide](when-the-slot-is-empty/) — the executed read: with origin
missing, retrieval broadens to all origins, while a filled slot lets the
index answer exactly — ask, broaden, or guess, each with a measured
cost.

Another detour: [the LLM over-parses and invents a
constraint](when-the-llm-over-parses/) — the executed read: the over-parsed query
invents max_price cheap and would filter the index by a constraint the
user never stated, silently shrinking recall like an over-eager rule.
