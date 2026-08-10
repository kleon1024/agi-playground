---
status: verified
level: applied
base: scratch
label: When the shuffle does not move
verified: 2026-08-06
---

# The negative result that is still the lesson

**Question:** [stage 03's walk-forward validation](../) compares shuffled,
chronological, and purged evaluation. This chapter reads the recorded run
and asks what it means when purge changes nothing.

**Before this:** [stage 03's walk-forward validation](../) and its recorded
run.

## The three paths, read

The run ([record](runs/2026-08-06-shuffle-read.md)) reads the recorded
Sharpe values:

| path | out-of-fold Sharpe |
|---|---:|
| shuffled-invalid | 0.7393 |
| chronological-unpurged | 0.9722 |
| purged-five-day / gapped-five-day | 0.9722 |

## Two readings

**Purge did not change this rule's score — and the reason is the lesson.**
The recovered implementation never used its training indices, so there was
nothing to leak: the chronological and purged paths agree (0.9722) because
the rule's prediction did not depend on training data. That is a negative
result about this run, explicitly not proof that leakage is harmless — a
different rule that did use its training indices would show the gap this
one cannot.

**The three-path comparison is the point, not the number.** The shuffled
path (0.7393) is the invalid baseline, the chronological path is the
naive-but-honest one, and the purged path is the defended one. Running all
three on the same data is what makes the difference legible — and the
recorded 0.9722-vs-0.9722 is the honest version of a comparison that could
easily have been a 0.9722-vs-1.20 leakage headline.

## The fix and its trade

The fix is the three-path comparison itself: shuffled-invalid (0.7393) as
the floor, chronological-unpurged (0.9722) as the naive-but-honest path,
and purged-gapped (0.9722) as the defended path, all on the same data.
Running all three is what makes a negative result legible: this rule's
prediction never used its training indices, so there was no leak for purge
to remove, and the two defended paths agree exactly because of it.

The trade is the cost of keeping three evaluation paths honest. Two extra
paths to build and maintain, each with its own invariant (shuffle must
destroy temporal structure; the purged path must use the platform's
eligibility boundary — the same purge/embargo machinery the platform owns,
canonical in López de Prado, *Advances in Financial Machine Learning*,
Wiley, 2018), for a comparison whose value is mostly negative: it proves a
null result and a sensitive harness, not an edge. The payoff is that the
negative result is evidence *about this run* — the chapter says explicitly
it is not proof leakage is harmless. A different rule that did use its
training indices would show the gap this one cannot, and only the
three-path harness would make that gap visible as a difference rather than
a headline.

## Who owns the loop

- **The evaluation platform** owns the three-path harness: the shuffled
  baseline, the chronological path, and the purged path share one
  implementation so the comparison is controlled.
- **Research** owns the rule that decides whether purge matters: the
  three-path read is the evidence that a purge decision was made — the bet
  "this rule has no overlap sensitivity" was actually tested rather than
  assumed.
- **Statistics/evaluation** owns the reading: the shuffled path is the
  floor, purge is the defense, and the gap between them is the quantity of
  interest, not either number alone.

When the three paths are not run, a leak that exists is invisible in the
single chronological number — and "purge changed nothing" is reported
without the control that makes it meaningful.

## Evidence boundary

The recorded walk-forward run (1,255 AAPL bars, 1,230 five-day labels, one
fold-fitted rule, one window). It reads that artifact; it does not re-fetch
and the negative result is evidence about this run, not about walk-forward
validation in general.

## Check your mental model

Answer each before opening it.

**1. If purge changes nothing, is the purge unnecessary?**

<details>
<summary>Answer</summary>

No — the comparison shows this rule did not leak, not that leakage cannot
happen. The fold-fitted rule's prediction never used its training indices,
so there was no leak for purge to remove. The discipline exists for rules
that do use training data; this run is the control that proves the
comparison is sensitive enough to show a difference when one exists.

</details>

**2. Why is the shuffled path reported at all?**

<details>
<summary>Answer</summary>

Because it is the invalid baseline that bounds the comparison. Shuffled
evaluation (0.7393) destroys the temporal structure the strategy depends
on, so it should be the worst path; chronological and purged sit above it.
Reporting it makes the direction of the discipline visible — shuffle is
the floor, purge is the defense, and the three together define what
"honest evaluation" means for this rule.

</details>

## Next

Back to [stage 03](../), or to
[why fold-specific fit is not strategy fit](../when-purge-matters/) which
reads the same run's purge story.
