---
status: verified
level: applied
base: none
label: The split that decides
verified: 2026-08-06
---

# Does the split decide who wins?

**Question:** [stage 00](../) splits by Murcko scaffold so no scaffold
crosses train and test — checked, not assumed. But a scaffold split can
still shift the label distribution, because scaffolds cluster by activity.
This chapter measures that shift across the mission's three endpoints and
asks whether it sits inside the descriptor-versus-model verdicts.

**Before this:** [stage 00's scaffold split](../), and the mission's
cross-endpoint analysis.

## The shift, measured

The diagnostics ([run record](runs/2026-08-06-split-diagnostics.md)) read
the three recorded split summaries:

| endpoint | train positive | test positive | shift | verdict |
|---|---:|---:|---:|---|
| SR-MMP | 14.8% | 19.7% | +4.9pp | descriptor wins |
| NR-PPAR-gamma | 2.3% | 5.3% | +3.0pp | inconclusive |
| NR-ER | 12.7% | 13.2% | +0.5pp | descriptor wins |

## Two readings

**The split shifts the label distribution in every endpoint, in the same
direction.** Test is more positive than train in all three — scaffolds
cluster by activity, so the scaffold split systematically hands the test
side a harder class balance. The shift is 0.5 to 4.9 percentage points,
which is a real confound for any train/test comparison, and it is precisely
why the mission reports the overlap directly rather than assuming a shuffle
is clean.

**The largest shift sits on the scarcest endpoint — the one with no
verdict.** NR-PPAR-gamma's test positive rate (5.3%) is 2.3x its train's
(2.3%), and that is the endpoint whose comparison is inconclusive (gap
inside spread). The label shift and the variance the mission's stage 05
names are the same confound: on a scarce endpoint, the split's shift and
the run-to-run spread are large enough that no winner emerges. The split
does not decide the winner — but it does decide whether a winner can be
seen at all.

## Evidence boundary

Three endpoints, one split seed each, the recorded summaries. It shows the
label shift and its alignment with the verdict pattern; it does not prove
the shift causes the verdicts (the mission's cross-endpoint analysis owns
that claim), and it does not re-compute the scaffold groups (the stage 00
run record's checked-overlap numbers are cited, not re-derived).

## Check your mental model

Answer each before opening it.

**1. The scaffold split guarantees zero scaffold overlap. Why is the split
still not "clean"?**

<details>
<summary>Answer</summary>

Because "no shared scaffold" and "no label shift" are different properties.
Scaffolds cluster by activity, so splitting by scaffold can send a
disproportionate share of positive examples to one side — here, test is
more positive than train in every endpoint (0.5 to 4.9pp). The overlap check
verifies structural separation; the label shift is a separate property that
also has to be measured.

</details>

**2. Why is the inconclusive verdict exactly where the shift is largest?**

<details>
<summary>Answer</summary>

Because scarcity amplifies both: NR-PPAR-gamma's 2.3% train positive rate
means tiny counts drive the metrics, so the split's shift (test 2.3x the
train rate) and the run-to-run spread are both large enough to swallow any
winner. The mission's cross-endpoint analysis names scarcity as the
variance driver; this chapter shows the split's shift is the same confound,
visible before any model runs.

</details>

## Next

[Stage 05's cross-endpoint analysis](../../05-cross-endpoint-analysis/):
where the scarcity hypothesis and the verdict pattern are tested against
each other across all three endpoints.
