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
retrieval serves, which the detours price.

## How you find it: the parse-stability audit, executed

The failure mode this audit exists for is the aggregate parse-quality
metric: a head-dominated log reports "the LLM parse is good" while
tail queries — genuine judgment calls — swing between intents across
samples, and the same string can flip the retrieval path. The run
([record](runs/2026-08-07-parse-audit.md)) emits a 10-query log with
five sampled parses per query and stratifies agreement and quality by
head and tail:

| stratum | queries | agreement | quality | low-conf slots |
|---|---:|---:|---:|---:|
| head | 5 | 1.000 | 0.976 | 0.0 |
| tail | 5 | 0.520 | 0.554 | 2.4 |

The verdict is PARSE QUALITY HIDES SWINGING JUDGMENT CALLS: the
aggregate quality of 0.765 is a head artifact — head parses agree at
1.000 and score 0.976, while tail parses agree at only 0.520 with 2.4
low-confidence slots per query. The same query parses into different
intents across samples, so a low-confidence call flips the retrieval
path. The decision that follows: sample the parse and take the
majority (self-consistency; Wang et al., ICLR 2023,
arXiv:2203.11171), and treat a low-confidence slot as a clarification
or a broadening, never a silent guess.

## The fix and its trade

The fix is to sample the parse and take the majority — self-consistency —
and to treat a low-confidence slot as a clarification or a broadening,
never a silent guess. The executed audit prices the failure the fix
removes: head parses agree at 1.000 and score 0.976 with zero
low-confidence slots, while tail parses agree at only 0.520, score
0.554, and carry 2.4 low-confidence slots per query — the aggregate
quality of 0.765 is a head artifact, and the same query parsing into
different intents across samples flips the retrieval path. Wang et al.
(ICLR 2023, arXiv:2203.11171) establish the self-consistency pattern:
sample, take the majority, and let agreement be a confidence signal.

The trade, named: sampling costs LLM calls — latency and cost multiply
per query — and the slot-confidence floor costs calibration; the
alternative is a single logged parse that commits a judgment call as if
it were a fact. The parse feeds every downstream decision, so the
stability contract is owned at the model-serving boundary: a
low-confidence slot must change the retrieval behavior, not silently
filter it.

## Who owns the loop

The parse feeds every downstream decision, so its stability is owned at
the model-serving boundary, and the handoffs are where the swing gets
committed:

- **The query-understanding or LLM team** owns the parse itself: the
  sampling policy, the agreement rate, and the slot-confidence floor —
  the [when-the-parse-swings detour](when-the-parse-swings/) is its
  failure mode.
- **The retrieval team** owns what the parse feeds: the key space, and
  the fallback when a slot is missing or below confidence — the
  [when-the-slot-is-empty detour](when-the-slot-is-empty/) is its
  failure mode.
- **The product owner** owns the parse contract: when an invented
  constraint is acceptable and when the model over-commits — the
  [when-the-llm-over-parses detour](when-the-llm-over-parses/) is its
  pricing.

When the ownership is implicit, the LLM team logs a single parse, the
retrieval team serves the keys it is given, and nobody owns the swing —
so a judgment call that flips the path ships as "the parse is good"
until agreement is stratified and logged per query.

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

And a third: [the parse swings and the swing flips the retrieval
path](when-the-parse-swings/) — the executed sample read: "apple watch"
splits 3-2 between product and service, so sampling plus majority
(self-consistency) stabilizes the clear cases and a thin majority
broadens or clarifies instead of committing.
