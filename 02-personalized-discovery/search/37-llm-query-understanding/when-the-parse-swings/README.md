---
status: verified
level: applied
base: scratch
label: When the parse swings
verified: 2026-08-07
---

# The parse swings, and the swing flips the retrieval path

**Question:** [stage 37's LLM query understanding](../) parses a raw
query into intent and slots. This chapter asks what happens when
sampling produces different parses for the same string, and answers:
the intent swings, and a low-confidence judgment call routes the query
down a different path.

**Before this:** [stage 37 — LLM query understanding](../) for the
intent-slot key space, and the [over-parse detour](../when-the-llm-over-parses/)
for the parse that commits to more structure than the query carries.

## The swing, executed

The run ([record](runs/2026-08-07-parse-swing-read.md)) samples the
parse five times per query:

| query | samples | majority intent | agreement |
|---|---|---:|---:|
| apple watch | 5 | product_search | 3/5 |
| check my balance | 5 | bank_balance | 2/5 |

## The reading

Temperature sampling makes the parse a distribution, not a point.
"apple watch" splits 3-2 between product and service, and the minority
parse would route to a different retrieval path — a watch for sale
versus warranty service for one. "check my balance" is worse: no intent
reaches 3/5, so the parse genuinely cannot decide between a bank
balance, a game balance, and an account summary. The fix is the
self-consistency pattern (Wang et al., ICLR 2023): sample, take the
majority, and let agreement be a confidence signal. The deeper
consequence is the decision rule: a majority that is thin is not a
parse to commit to — it is a judgment call, and the retrieval path
should broaden or ask, not silently choose the mode intent. The swing
is the signal, and it is only visible because the log kept the samples
instead of a single parse.

## Evidence boundary

The executed sample parses over two hand-built queries (illustrative,
deterministic, declared sample draws). It demonstrates the shape; real
parse stability needs the actual LLM, a measured agreement
distribution, and the retrieval metrics that follow from choosing the
mode intent.

## Check your mental model

Answer each before opening it.

**1. Why is a 2/5 majority worse than a 3/5 majority?**

<details>
<summary>Answer</summary>

Because 3/5 is a weak signal and 2/5 is no signal. With 3/5 the mode
intent won twice as often as either loser, so committing to it is a
bet with some support. With 2/5 the samples spread across three
intents — the model has no preferred answer, and any choice is
arbitrary. The agreement rate is the confidence signal, and below a
threshold the right action is to broaden or clarify, not commit.

</details>

**2. What does the swing cost that a single parse cannot show?**

<details>
<summary>Answer</summary>

The alternative path. A single parse returns one intent and the log
records only that one; the swing shows that the query was a judgment
call and that the losing intents would have gone somewhere else. That
is the case-finding: swing rate per stratum is how you find the queries
whose retrieval path is decided by chance.

</details>

## Next

Back to [stage 37](../). The
[empty-slot detour](../when-the-slot-is-empty/) shows the parse that is
stable but incomplete: a slot the query never named, and the cost of
guessing it.
