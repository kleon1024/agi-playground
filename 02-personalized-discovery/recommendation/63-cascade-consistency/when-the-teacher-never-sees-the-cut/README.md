---
status: verified
level: applied
base: scratch
label: When the teacher never sees the cut
verified: 2026-08-08
---

# The teacher only ever scores survivors

**Question:** [stage 63](../) distills the final ranker's score into the
pre-rank. This chapter asks what happens when the distillation target is
itself truncated by the cascade's cut, and answers: the student is trained
on a saturated, survivor-only label set, lands below the popularity
baseline it was meant to beat, and the cascade locks the same 12 of the
oracle's top-50 out of the teacher's view forever.

**Before this:** [stage 63 — cascade consistency](../).

## The truncated teacher, executed

The run ([record](runs/2026-08-08-cascade-cut.md)) simulates a two-stage
cascade over six generations under three teacher-label regimes. The
teacher's score is a saturated probability — sigmoid of 4 times popularity
plus quality, like a pCVR — so among the survivors the labels are crushed
near one and carry no discrimination. Generation 1 to 6, the cut is 100 of
2,000 items; the oracle's true top-50 is fixed; every generation the run
reads how much of that top-50 the teacher was allowed to score.

The top-K recall at the cut, per generation:

| pre-rank | gen 1 | gen 6 | ever scored |
|---|---:|---:|---:|
| popularity baseline | 37 | 37 | — |
| distilled on survivors only | 33 | 32 | 38 of 50 |
| distilled with full-corpus sample | 40 | 40 | 43 of 50 |
| distilled with stratified sample | 40 | 40 | 43 of 50 |

The student's read against the full corpus — the read the team cannot
compute without scoring beyond the cut — drifts for the locked arm while
the fix arms hold:

| pre-rank | gen 1 | gen 6 |
|---|---:|---:|
| survivors only | 0.715 | 0.689 |
| full-corpus sample | 0.756 | 0.756 |
| stratified sample | 0.756 | 0.755 |

And the correlation on the pairs the teacher actually scored — the read
the team can compute — is flat near zero for every arm across all six
generations, because the saturated head labels cannot rank anyone.

## The reading

The teacher only ever scores survivors, and the survivors' labels are
saturated: every item the cut let through is "good", so the distilled
student learns nothing from them except the survivor feature geometry,
which is popularity. Its score extrapolates to the tail as a noisy
popularity proxy, the cut converges to a popularity-shaped set, and the
next generation's labels are the same saturated head again. The funnel is
closed from generation 1: the survivors-only student drifts to 32 of the
oracle's top-50, below the 37 the popularity baseline itself keeps, and 12
of the top-50 are never scored in any generation. An item that never
survives the cut can never be taught.

The failure is invisible in the aggregate. The correlation the team can
compute — student score versus teacher label on the pairs the teacher
scored — is flat near zero for every arm, so nothing trends and nothing
alarms. The divergence lives in the full-corpus read: the locked arm
drifts 0.715 to 0.689 while the fix arms hold 0.756. The metric that
matters across a cascade is top-K recall at the cut, and it must be
measured against the teacher's full-corpus choices, not against the
survivor pairs that exist only because the cut already decided.

## The fix and its trade

The fix is to teach beyond the cut: the teacher runs on a sample of the
rejected corpus each refresh, so the student gets unsaturated labels from
the tail it never sees. The executed read prices the repair: a
full-corpus sample of 400 rejected items takes the cut from 32 back to 40
of the oracle's top-50 and lifts the ever-scored count from 38 to 43. The
stratified variant — drawing the extra labels per popularity group so the
tail is represented — reaches the same recovery here; the two differ in
where the teacher budget is spent, and the stratified repair is the one
the literature supports when that budget is tight. Kang et al. (WSDM
2023) show standard distillation propagates and intensifies a popularity
bias — unpopular-group recall drops on average 22.4% across the KDs they
compare while popular groups rise — and propose partitioning items by
popularity and extracting within-group ranking knowledge.

The trade, named: the fix costs the final ranker's inference on a few
hundred sampled items per refresh — small against the serving budget, but
real, and it must be owned by the team that runs the expensive stage. The
sampled labels age with the teacher, so the sample has to be refreshed
when the final ranker changes. And the acceptance metric has to be top-K
recall at the cut against the teacher's full-corpus choices plus the
ever-scored funnel — not the survivor correlation, which is flat for
every arm and would bless a cascade that lost 12 of the answer. The cheap
alternative, distilling whatever the final ranker emits on the survivors
alone, is the trap this chapter names: it makes the cheap stage worse
than the popularity baseline it replaced.

## Who owns the loop

- **The pre-rank model team** owns the distillation and the label pool —
  whether the teacher scores beyond the cut, and how the sample is drawn,
  is a training-time decision with a maintenance cost.
- **The final-ranker team** owns the teacher score and the sampling
  budget — the fix costs its inference on sampled rejected items every
  refresh, and the sample must be re-drawn when the teacher changes.
- **The serving team** owns the cut as a budget decision and the logging
  that makes the funnel readable — the run needs the rejected set and
  which items the teacher ever scored, not just what survived.
- **The evaluation team** owns the top-K recall at the cut against the
  teacher's full-corpus choices, and the ever-scored count — the two
  reads that move only in the tail.

## Evidence boundary

The executed read is a deterministic synthetic simulation (seeded stdlib
RNG, 2,000 items, six generations, three label regimes sharing one
generation-0 cut). It demonstrates the truncation mechanism; real systems
must log the cut's rejected set, sample the teacher over it, and measure
top-K recall at the cut against the teacher's full-corpus choices. The
citations were verified on 2026-08-08: Kang et al., "Unbiased Knowledge
Distillation for Recommendation", WSDM 2023, DOI 10.1145/3539597.3570477,
for the stratified repair; Covington et al., "Deep Neural Networks for
YouTube Recommendations", RecSys 2016, DOI 10.1145/2959100.2959190, for
sampling beyond the served set with correction; Zhu et al., "Learning
Tree-based Deep Model for Recommender Systems", KDD 2018,
DOI 10.1145/3219819.3219826, for the structural direction where the cheap
stage scores the full corpus like the final ranker. Their claims are the
authors', and this chapter leans on them only as the repair the executed
failure points to.

## Check your mental model

Answer each before opening it.

**1. Why does the survivors-only student land below the popularity
baseline it was meant to beat?**

<details>
<summary>Answer</summary>

Because its labels are saturated. Every survivor scores near one, so the
student's fit is driven by the survivor feature geometry — a noisy
popularity proxy — and its extrapolation to the tail is systematically
wrong. The clean popularity ranking at least ranks the head correctly and
keeps 37 of the oracle's top-50; the distilled student keeps 32.

</details>

**2. Why is the failure invisible in the aggregate?**

<details>
<summary>Answer</summary>

Because the read the team can compute — student score versus teacher label
on the pairs the teacher scored — is flat near zero for every arm: the
saturated head labels cannot rank anyone, so nothing trends across the six
generations. The divergence (0.715 to 0.689 for the locked arm versus
0.756 for the fix arms) lives entirely in the full corpus, which the team
cannot score without paying for the fix.

</details>

**3. What is the practical fix, and what does it cost?**

<details>
<summary>Answer</summary>

Score beyond the cut: the teacher runs on a sample of the rejected corpus
each refresh, uniform or stratified toward the tail, giving the student
unsaturated labels. It costs the final ranker's inference on a few hundred
sampled items per refresh and a re-draw whenever the teacher changes; the
buyback takes the cut from 32 back to 40 of the oracle's top-50 and lifts
the ever-scored count from 38 to 43.

</details>

## Next

Back to [stage 63](../), where the distilled pre-rank is the repair this
funnel failure quietly undoes. The teacher's own errors travel the same
path: [a noisy teacher passes its noise to the
pre-rank](../when-the-distillation-blurs/). And the arithmetic of the
cut, one stage at a time: [only 11 of the final top-20 survive a
click-based cut of 80](../when-top-k-is-not-preserved/).
