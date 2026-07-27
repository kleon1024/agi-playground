---
status: draft
---

# Mission 02 — Personalized discovery

**Business goal:** reduce the time it takes a user to find something worth
their attention, without degrading what the catalogue offers them or what the
platform earns.

Recommendation, search, and advertising are one mission, not three, because
they are the same decision loop with different inputs. Recommendation ranks
with no query. Search ranks with one. Ads insert a paid item into either, and
the interesting problem is that **every ad displaces an organic result** — so
the three cannot be optimized independently without one quietly cannibalizing
the others.

Read [`mission.yaml`](mission.yaml) first, especially `does_not_prove`.

## Why this mission exists

Mission 01 proved the platform layers compose. It did not prove they
*generalize*, because everything in it was a language model producing text.

This mission is the test of the architecture's central claim. If
`platform/data`, `platform/training`, `platform/serving`, and
`platform/evaluation-observability` are real layers rather than a relabelled
LLM pipeline, then a completely different decision loop should reuse them.
Ranking is the sharpest available test: the objective is not next-token
likelihood, the model is not necessarily a transformer, and the failure modes
are ones text generation never has.

It is also where the repo stops being about models and starts being about
decisions. A language model is judged on its output. A ranker is judged on
what a user did next — which nobody can observe offline, which is exactly why
this mission's honesty constraints are stricter than mission 01's.

## The decision loop

```
user + context (+ query)
  → understand intent          # what are they actually looking for
  → retrieve candidates        # ~1000 from a catalogue of millions, fast
  → rank                       # expensive model, small candidate set
  → allocate paid placement    # auction, competing with organic for slots
  → present + explain
  → collect feedback           # which becomes tomorrow's training data
```

Two structural facts drive everything:

**The latency budget forces the architecture.** Scoring every item in the
catalogue with a good model is impossible inside 100ms, so the system must be
two-stage: cheap retrieval that is allowed to be approximate, then expensive
ranking over the survivors. Almost every design decision downstream is a
consequence of that split — including that a great ranker cannot rescue a
candidate set that never contained the right item.

**The feedback loop trains the next model.** The system's own choices become
the data the next version learns from, so a bias introduced today is amplified
tomorrow. This is why the guardrails include catalogue coverage: a model that
learns to recommend only head items produces logs containing only head items,
and the next model cannot learn anything else.

## What makes this hard to prove, and what we do about it

Mission 01 could claim "the stages ran". This mission wants to claim "users
found things faster", and that claim cannot be made here. There are no users.

So the outcome is proven by **offline replay** — rank held-out interactions
and measure whether the true item ranks higher — with three limitations stated
up front rather than buried:

1. **Logged data is confounded by the policy that produced it.** Users could
   only click what the previous system showed them. An offline win can vanish
   or reverse online. This is the central methodological problem of the field,
   not a caveat we invented.
2. **It cannot see what was never shown.** Novelty and discovery value are
   invisible to replay by construction.
3. **The ads component is simulated.** Bids come from a declared distribution,
   not real advertisers, so it can test auction mechanics and user cost but
   says nothing about revenue.

The honest response is not to avoid the claim but to bound it: this mission
establishes *better ranking of held-out interactions under a fixed candidate
set*, and names the interleaving or A/B experiment that would be required to
say more.

**And it must beat popularity.** Un-personalized global popularity is a
famously strong baseline that a great many published recommender results fail
to clear. Any system here that cannot beat "show everyone the same popular
items" has not demonstrated personalization, whatever its nDCG looks like in
isolation.

## Stages

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| `00-interactions` | A public interaction dataset, cleaned and split by time — never randomly, since a random split leaks the future | `platform/data` | 🚧 planned |
| `01-retrieval` | Two-tower embedding retrieval + a BM25-style lexical arm for search; recall@1000 against an exhaustive scan | `capabilities/retrieve-ground` | 🚧 planned |
| `02-ranking` | A ranker over retrieved candidates; nDCG@10 vs both baselines, with seed variance | `capabilities/rank-decide` | 🚧 planned |
| `03-ads-auction` | Second-price auction with a quality score; advertiser value and user cost reported separately | `capabilities/rank-decide` | 🚧 planned |
| `04-serving` | Two-stage serving inside the latency budget, measured | `platform/serving` | 🚧 planned |
| `05-report` | Outcome report against baselines and guardrails, with failure cases | `platform/evaluation-observability` | 🚧 planned |

## What this reuses, and what it adds

Reused from mission 01 without modification is the point of the exercise:
the data pipeline discipline from
[`platform/data`](../../platform/data/), the training-loop engineering from
[`platform/training`](../../platform/training/) — gradient accumulation, mixed
precision, resumable checkpoints — the serving concerns from
[`platform/serving`](../../platform/serving/), and the evaluation discipline
from [`platform/evaluation-observability`](../../platform/evaluation-observability/),
which is where harness disclosure and seed variance already live.

What is new is two capabilities, and they are admitted under the gate in
[`standards/mission-contract.md`](../../standards/mission-contract.md) —
`retrieve-ground` and `rank-decide` both have clear input/output contracts, are
independently evaluable, map toy → production, and run on the local lane.
Neither is admitted to `capabilities/` until a **second** mission needs it;
until then they live inside this mission.

## Sequencing

Mission 01 finishes before this one starts building. That ordering is
deliberate: this mission's entire value is demonstrating that the platform
layers are reusable, and that claim is worthless if those layers are still
being built. What exists now is the contract and the design — which is exactly
what [`mission.yaml`](mission.yaml) requires before any code is written.
