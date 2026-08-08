---
status: verified
level: applied
base: scratch
label: When the tail goes cold
verified: 2026-08-07
---

# The tail that the index forgets

**Question:** [stage 02's recall index](../) returns candidates from item
embeddings. This chapter reads the executed popularity run and asks what
the demand curve does to tail coverage.

**Before this:** [stage 02 — recall](../) and its executed index.

## The concentration, executed

The run ([record](runs/2026-08-07-tail-read.md)) models 1000 items under a
power-law popularity curve:

| measure | value |
|---|---:|
| share of demand held by top 100 items | 69.3% |
| share held by items 101-1000 | 30.7% |
| tail items kept by a 200-item recall pass | 100 of 900 |

## Two readings

**Popularity concentrates, so demand-trained recall serves the head.**
Ten percent of the catalog carries 69.3% of the demand. An index that
learns from interactions — embeddings trained on click logs, popularity
boosts, embedding neighbors of popular seeds — will be dense and accurate
exactly where the demand already is.

**Tail coverage is a deliberate trade, not an accident of the index.**
The same 200-item pass keeps only 100 of 900 tail items; the head wins the
candidate slots. That is the correct behavior for a popularity-driven
baseline and the wrong behavior for a discovery goal — which is why the
mission's recall stage has to decide which tail it serves before it
builds the index, not after.

## The fix and its trade

The fix is to decide which tail the recall stage serves before building the
index, and the executed read prices why the decision must be explicit:
under a power-law demand curve, the top 100 of 1,000 items hold 69.3% of
demand, and a 200-item recall pass keeps only 100 of the 900 tail items.
An index that learns from interactions is dense and accurate exactly where
the demand already is — which is the correct behavior for a
popularity-driven baseline and the wrong behavior for a discovery goal.

The trade, named: serving the tail costs head recall, and the cost is
measured per policy. A coverage floor, a separate tail index, or
exploration in candidate generation raises the tail's slot share at a
priced cost to head recall — the executed pass shows the default outcome
(100 of 900) and a deliberate policy changes it. The alternative is leaving
the trade to the demand curve, which is not a decision at all: the head
wins the candidate slots silently, and the discovery failure is attributed
to the model instead of to the index objective.

## Who owns the loop

- **The retrieval team** owns the index objective — whether the candidate
  pass optimizes demand or reserves tail slots is decided here, before the
  index is built.
- **The product team** owns the discovery goal: how much tail coverage the
  system must serve is a product promise, priced against head recall.
- **The evaluation team** owns the tail-coverage read per pass, so the
  decision's cost is visible as a number and re-checked when the demand
  curve moves.

## Evidence boundary

The executed hand-built power-law model (illustrative, deterministic). It
demonstrates the concentration mechanism; real catalogs have a measured
demand curve, and the trade is priced against it.

## Check your mental model

Answer each before opening it.

**1. Why does the top 10% hold 69.3% of demand?**

<details>
<summary>Answer</summary>

Because popularity is a power law, not a bell curve: the most popular
item gets a thousand units of demand, the tenth gets a hundred, the
hundredth gets ten. Summed over 100 items, that head mass dominates. The
shape is the mechanism — any demand-trained index inherits it, which is
why the tail is starved unless the objective says otherwise.

</details>

**2. What would a discovery-first recall stage change?**

<details>
<summary>Answer</summary>

The objective: reserve candidate slots for the tail explicitly — a
coverage floor, a separate tail index, or exploration in the candidate
generation. The executed pass shows the default outcome (100 of 900); a
deliberate policy raises that number at a measured cost to head recall.
The point is the decision is visible and priced, not left to the demand
curve.

</details>

## Next

Back to [stage 02](../), or to
[the price of approximate](../the-price-of-approximate/) for the latency
side of the same candidate generation.
