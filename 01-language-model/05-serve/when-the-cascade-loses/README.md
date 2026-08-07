---
status: verified
level: applied
base: scratch
label: When the cascade loses
verified: 2026-08-07
---

# When does the cheap gate stop paying?

**Question:** the serving system has a latency budget and two models — a
cheap one that answers every step and an expensive one that answers the
ones worth paying for. The cascade gates on the cheap model's own
confidence: above a threshold, answer cheap; below it, escalate to the
expensive model. This chapter asks where that gate stops paying: can the
threshold be set wrong, can the cascade get *slower* than calling the
expensive model directly, and what does a hard latency budget do to the
quality it was meant to protect?

**Before this:** [what is the model actually doing between tokens?](../) for
why a decode step is memory-bound and why batch size decides intensity, and
[why concurrency pays](../why-concurrency-pays/) for the cost model a
request actually inherits. The sibling chapter
[speculative decoding](../speculative-decoding/) verifies every cheap guess
with the expensive model; this one is the other design — the gate *decides*
whether the expensive model is called at all, which is BranchyNet's
early-exit idea (Teerapittayanon et al., ICPR 2016,
[arXiv:1709.01686](https://arxiv.org/abs/1709.01686)).

## What the cascade is, measured

The run ([record](runs/2026-08-07-cascade-audit.md)) trains a 2.9M target
(expensive) and a 0.2M cheap model on the same tinyshakespeare corpus, in
two qualities: `cheap-good` (600 steps) and `cheap-poor` (40 steps). Each
decode step: the cheap model proposes a token and a confidence; above the
threshold `tau`, the token is emitted without the target; below it, the
target is called and its choice emitted. The audit sweeps `tau`, swaps in
the poor cheap model, and caps the expensive calls with a budget. Three
measured verdicts, each one a place the cascade loses.

## Verdict one: confidence is not correctness

At `tau=0.3`, `cheap-good` accepts 60 of 100 steps on its own confidence —
yet only 18% of positions match what the target would have chosen, and the
target's cross-entropy on the output (1.512) is barely better than the cheap
model alone (1.547). The gate accepted most of the sequence and protected
almost none of the quality, because the gate selects on the cheap model's
self-reported confidence, and confidence is not accuracy. This is the
failure a calibration check exists for: the threshold has to be chosen
against a *measured* accuracy-per-confidence band, not against the
confidence number itself.

## Verdict two: the escalation tax

Raise the threshold and the opposite failure appears. At `tau=0.7` and
`tau=0.9`, `cheap-good` escalates 92% and 99% of steps, so every step pays
cheap forward plus target forward, and the cascade is *slower* than calling
the target directly: 0.98x and 0.91x of target-only wall-clock. The poor
cheap model cannot even clear `tau=0.7`: it escalates 100 of 100 steps
(0.89x). A gate that escalates everything is strictly worse than the
expensive model alone — it adds the cheap model's latency to the expensive
model's latency and returns nothing for it. The threshold is not a free
quality dial; it is a cost dial, and on the wrong model it is a tax.

## Verdict three: the budget cliff

The latency budget is the real constraint a serving team faces: some number
of expensive calls per request. With a 5-expensive-call budget at `tau=0.9`,
the sequence spends the budget in the first steps and then is forced onto
the cheap path for the remaining 94 of 100: match with target-only output
collapses from 100% to 13%, and the target's cross-entropy rises from 1.006
to 1.494. The budget converted a quality-preserving gate into a garbage
fallback at the exact moment the request outlasted it — which is when the
tail of the workload, not the average, decides whether a system keeps its
SLA. The tail is the p95 discipline of
[when the tail waits](../observability/when-the-tail-waits/), applied to the
cascade's expensive calls: the budget has to be sized on the slice that
needs it most, not on the mean request.

## Where the cascade wins — and who decides

The table has one real band: `tau=0.5` with `cheap-good` runs 1.45x faster
than target-only at 58% match and a target cross-entropy of 1.219 — a
genuine quality-versus-latency trade, not a free lunch and not a collapse.
The serving owner prices that quality loss against the latency gain; nobody
else can, because the price is a product decision. The same gate, with the
same numbers, is how the recommendation side spends its pre-rank budget —
[cascade consistency in personalized discovery](../../../02-personalized-discovery/recommendation/63-cascade-consistency/)
is the same decision where the cheap stage is a ranker and the expensive
stage is the final ranker, and its detours measure what happens when the
cheap stage optimizes the wrong objective and ejects what the expensive
stage would have kept.

## Who owns it

- **The model team** owns the cheap model's calibration, not just its loss:
  the confidence-to-accuracy band per slice, measured, is what a threshold
  can be set against. `tau=0.3` looked like a speed dial and was a quality
  collapse because nobody had measured the band.
- **The serving team** owns the threshold and the budget as a pair, tuned on
  the tail slice: the budget that exhausts on hard requests (verdict three)
  and the threshold that escalates everything (verdict two) are both
  serving-time decisions, and both have to be checked on the p95 request,
  not the average.
- **The eval team** owns the match/quality metric the trade is priced on —
  this run's target cross-entropy and match rate — and a per-slice breakdown
  of it, because a global acceptance rate hides the slice where the gate
  collapses.
- **The product owner** owns the price of the quality loss: at what match
  rate is 1.45x speed worth shipping?

When nobody owns the calibration band, the symptom is a cascade that
"sometimes serves garbage": fast on easy requests, silently wrong on the
confident-but-wrong band, and slower than the expensive model on the hard
tail — three different failure modes, one gate.

## What this chapter does not prove

This is a mechanism demo at tiny scale — 2.9M/0.2M parameters, one prompt,
one seed — per the evidence-scale rule. It proves the three failure modes
exist and measures their shape; the specific thresholds and ratios do not
carry to production models, whose confidence distributions are the thing a
team has to measure on its own traffic. The run also measures greedy
generation only; sampled decoding and multi-request batching change the
numbers but not the three failure families.

## Check your mental model

Answer each before opening it.

**1. `tau=0.3` accepts 60% of steps yet matches the target on only 18% of
positions. What is the gate actually selecting on?**

<details>
<summary>Answer</summary>

On the cheap model's self-reported confidence, which is not the same as its
accuracy. A model can be confidently wrong — assigning high probability to a
token the expensive model would not choose — and a threshold on that
confidence admits the confident-wrong band wholesale. The gate has to be
set against a measured confidence-to-accuracy band per slice, not against
the raw confidence value.

</details>

**2. Why can a cascade be slower than calling the expensive model directly?**

<details>
<summary>Answer</summary>

When the threshold is set high enough (or the cheap model is too
underconfident to clear it), nearly every step escalates. Each escalated
step pays the cheap forward *and* the expensive forward, so total wall-clock
exceeds the expensive model alone — the cheap model's latency is added to
the expensive model's latency with nothing returned. In this run,
`tau=0.7`/`tau=0.9` with the good cheap model and `tau=0.7` with the poor
one all land below 1.0x.

</details>

**3. The 5-expensive-call budget leaves quality intact for the first steps
and destroys it afterward. Why is that a tail problem, not an average
problem?**

<details>
<summary>Answer</summary>

The budget is spent by the requests that need escalation most — the hard
tail — and once spent, the rest of *that request* is forced onto the cheap
path. A budget sized on the average request looks fine and exhausts exactly
on the requests whose quality matters most; the collapse (13% match in this
run) happens on the tail, which is where the p95 SLA lives. Budget and
threshold have to be validated on the tail slice, the same discipline
[when the tail waits](../observability/when-the-tail-waits/) applies to
latency itself.

</details>

## Next

Return to [the serving stage](../README.md) with the gate's three failure
modes in hand. The sibling question — a cheap draft verified by the
expensive model rather than gated by it — is
[speculative decoding](../speculative-decoding/), and the tail discipline
the budget depends on is [when the tail waits](../observability/when-the-tail-waits/).
