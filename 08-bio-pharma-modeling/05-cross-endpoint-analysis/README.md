---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Cross-endpoint analysis
---

# What does the three-endpoint pattern actually say, and what does it not say?

**Question:** stages 01, 03, and 04 each ran the same descriptor-vs-model
comparison on a different Tox21 endpoint and each added one more data point
to the scarcity-drives-variance hypothesis stage 03 first floated. Three
points is enough to ask a sharper question than "does the hypothesis hold" —
it is enough to ask whether variance and *win/loss direction* are actually
explained by the same variable, or whether treating them as one question was
always doing too much with three endpoints. This stage does not run a fourth
endpoint; stage 04 already closed that door, since Tox21's remaining
endpoints all fall inside the imbalance range these three already bracket.
Instead it goes back over the three real results already on disk and asks
what they jointly support.

**The artifact this stage produces** is not a new ROC-AUC number. It is a
small analysis script,
[`core/analyze_cross_endpoint.py`](core/analyze_cross_endpoint.py), that reads
stages 00/03/04's `split_summary.json` and `runs/*-seed{0,1,2}.json` files
directly (no hand-copied numbers) and answers two separate questions the
prior three stages had folded into one: does positive-class count predict
(1) the trained model's seed-to-seed variance, and (2) which approach wins.

**Before this:** [stage 01](../01-descriptor-baseline-and-model/) (SR-MMP),
[stage 03](../03-second-endpoint/) (NR-PPAR-gamma, the scarcity-variance
hypothesis), and [stage 04](../04-third-endpoint/) (NR-ER, the third point).

## Why analysis-only, not a fourth endpoint

Stage 04 already established that no remaining Tox21 endpoint sits outside
the imbalance range SR-MMP (14.8% positive) and NR-PPAR-gamma (2.3%) already
bracket — a fourth endpoint would add another interpolated point, not new
range. What three points have not yet been asked is whether they are even
answering the *same* question. Stage 04's own verdict already separated two
claims that a single "does the hypothesis hold" framing blurs together:
variance shrinking as positive count rises, and which side wins. This stage
makes that split explicit and checks each half on its own.

## The three results, side by side

| Endpoint | Train positive count | Descriptor mean AUC (spread) | Model mean AUC (spread) | Gap (model − descriptor) | Verdict |
|---|---|---|---|---|---|
| SR-MMP | 689 | 0.8142 (±0.0010) | 0.7312 (±0.0159) | −0.0830 | descriptor wins beyond spread |
| NR-PPAR-gamma | 118 | 0.6554 (±0.0044) | 0.6591 (±0.0620) | +0.0037 | inconclusive |
| NR-ER | 628 | 0.6413 (±0.0011) | 0.6679 (±0.0227) | +0.0265 | model wins beyond spread |

Those verdicts are a length compared against a length, and the table leaves the
comparison to be done in your head. Select an endpoint and watch the rule run
on the seeds themselves:

<!-- interactive: EndpointSpread -->

## Question 1: does positive-class count predict the model's variance?

Ranking the three endpoints by training positive count and reading off the
trained model's seed spread gives a clean monotonic trend: 118 → 0.0620,
628 → 0.0227, 689 → 0.0159. Fewer positive examples, more seed-to-seed
variance, at every step. This is the same relationship stage 04 already
reported holding "directionally, not precisely" — this stage confirms the
ranking is monotonic with all three points read programmatically rather than
by eye, and stops there. Three ranked points cannot support a correlation
coefficient or a p-value, and none is computed or implied.

## Question 2: does positive-class count predict which approach wins?

No. SR-MMP (689 positive) and NR-ER (628 positive) have training positive
counts within 10% of each other, yet SR-MMP is a clear descriptor win and
NR-ER is a clear model win in the opposite direction. If positive-class
count alone decided the winner, these two endpoints would have to land on
the same side. They do not. This is the concrete finding this stage adds:
variance-vs-scarcity and win/loss-vs-scarcity are two different
relationships, and only the first is supported by this data. No replacement
variable is proposed — fitting a new explanation to the same three outcomes
that produced it would be overfitting a hypothesis to its own evidence, not
a finding.

Full output and command: [`runs/2026-08-01-cross-endpoint-analysis.md`](runs/2026-08-01-cross-endpoint-analysis.md).

## The fix and its trade

The fix is the claim-separation rule: the stage splits "does the
hypothesis hold" into two falsifiable questions — does positive-class
count predict the model's *variance*, and does it predict *which approach
wins* — and checks each half on its own. The trade is that the separation
costs a conclusion: variance-vs-scarcity holds monotonically (118 → 0.0620,
628 → 0.0227, 689 → 0.0159), but win/loss-vs-scarcity does not (SR-MMP 689
and NR-ER 628, within 10% of each other, land on opposite sides), so the
stage deliberately stops at the negative — no replacement variable is
proposed, because fitting a new explanation to the same three outcomes that
produced it would be overfitting a hypothesis to its own evidence. The
refusal is the fix: three ranked points cannot support a correlation
coefficient or p-value, and none is computed or implied.

## Who owns this loop

- **The analysis owner** owns the two-question separation and the
  stop-at-the-negative rule: the table's verdicts are computed
  programmatically from the seeds, and the unanswered second question is
  reported as unanswered.
- **The evaluation owner** owns the monotone-variance read as the
  supported finding and the no-correlation boundary: the ranking is
  confirmed with all three points, and the statistical limits of n=3 are
  stated rather than papered over.
- **The model team** owns the win/loss-negative as the actionable
  consequence: since scarcity alone does not decide which approach wins,
  the next endpoint or representation comparison must vary something other
  than positive count.

## What this stage does not establish

This is three endpoints out of Tox21's twelve, and Tox21 is one small public
dataset chosen for tractability, not for relevance to any real screening
program — restated from `mission.yaml`, nothing here is evidence about
anti-aging biology, drug efficacy, or pharmacological safety. The
monotonic variance trend is a suggestive pattern over three ranked points,
not a statistically significant result, and the win/loss finding is a
negative result (ruling out one candidate explanation), not a positive
identification of what does decide the winner. Neither claim generalizes to
a different dataset or molecular representation without re-running this
comparison from scratch.

**Next:** [stage 06](../06-model-or-representation/) takes the second of those
two routes. Stage 04 closed the endpoint-coverage question for this dataset,
and this stage closes the "is variance-vs-scarcity the same claim as
win/loss-vs-scarcity" question the first three stages left implicit. A
genuinely new stage needed either a different dataset or a different candidate
explanatory variable, not another endpoint from this same panel — so stage 06
swaps the molecular representation while holding the learner fixed, and finds
that ten physicochemical descriptors beat 2048 substructure bits even at the
bit width most favourable to the fingerprint.

A detour from here: [what does scarcity decide, and what does it
not?](when-scarcity-decides/) — the two recorded directions read: variance
grows monotonically as positives shrink (scarcity explains where a winner
can be seen), while the gap is not monotonic (it does not explain who wins).

Another detour: [three endpoints, two directions, and the ceiling stated](the-n3-directional-read/) — the recorded JSON read: variance is monotonic with scarcity, the gap is not, and n=3 is the stated limit.
