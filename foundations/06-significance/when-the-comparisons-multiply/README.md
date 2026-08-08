---
status: verified
level: applied
base: scratch
label: When the comparisons multiply
verified: 2026-08-08
---

# More comparisons, more chance hits: the multiple-testing failure

**Question:** [the significance chapter](../) compares two models with
one declared alpha and one verdict. Real evaluation compares many pairs
at once — a dozen model variants against a baseline, several prompts,
several tasks. This chapter executes the multiple-comparison audit: how
many of the pairwise wins are chance, and what the correction costs.

**Before this:** [the significance chapter](../) and its recorded paired
bootstrap, which sets up the single-comparison decision rule this chapter
multiplies.

## The audit, executed

The run ([record](runs/2026-08-08-many-comparisons.md)) draws 12
independent paired comparisons of n=300 items each. In the null draw,
every pair has true effect zero:

| procedure | flags (of 12) |
|---|---:|
| naive, alpha 0.05 | 1 |
| BH, q 0.10 | 1 |

In the planted draw, pair 6 carries a real effect (p = 5.19e-07), pairs 3
and 9 are null but fire:

| pair | p-value | naive | BH q=0.10 |
|---|---:|---|---|
| 3 | 0.0255 | reject | keep |
| 6 | 5.19e-07 | reject | reject |
| 9 | 0.0170 | reject | keep |

Across 500 repetitions of the planted shape, naive testing averages 0.59
false positives per experiment and 44.2 percent of experiments have at
least one; BH averages 0.22 and 16.8 percent. The true pair is missed
6/500 times by naive testing, 25/500 by BH.

## The failure mode, named

**One alpha, repeated, is a different promise than one alpha once.** A
single comparison at alpha 0.05 lies 5 percent of the time. Twelve
independent comparisons each lie 5 percent of the time, and the
probability that at least one of them lies is 1 - 0.95^12 = 46.0 percent
— the run's null draw shows the mechanism directly: nothing is true, and
one pair still fires. The naive verdicts in the planted draw are the same
failure wearing a product hat: two of the three "wins" (pairs 3 and 9)
would ship a change that does nothing, because each comparison was read
as if it were the only one. The more comparisons a team reports, the
higher the chance that the reported win is a chance hit; reporting only
the significant ones — or only the pair that was significant — is the
same bias applied after the fact. Benjamini & Hochberg (1995, JRSS-B, doi
10.1111/j.2517-6161.1995.tb02031.x) formalize the alternative: control
the false discovery rate, not the per-test rate.

**Two error budgets, two fixes.** The family-wise error rate asks that
the probability of *any* false discovery stay at alpha — the conservative
correction (Bonferroni divides alpha by the number of tests) answers
that, at the cost of power. The false discovery rate asks that the
expected *share* of rejected tests that are false stay at q, which is
what Benjamini-Hochberg controls.

## The fix and its trade

The fix is to stop declaring wins per-comparison and declare them against
the whole family: sort the p-values, reject every test at or below the
largest rank k whose p-value is at most k·q/m (the measured run is that
procedure, executed on every draw). The trade is real and measured, not
asserted. BH cuts false positives per experiment from 0.59 to 0.22 and
the family-wise rate from 44.2 to 16.8 percent, and it pays for that with
power: the true pair is missed 25/500 times versus 6/500, because BH's
threshold for the top-ranked test (q/m = 0.0083 at q=0.10, m=12) is
stricter than the per-test alpha of 0.05. For a dozen model comparisons,
shipping a false win costs real product changes; 25 missed confirmations
of a real effect is the cheaper error. The process half is
pre-registration — deciding the family and the q before looking at the
p-values, which closes the variant where the family is defined by what
happened to be significant.

## Who owns the loop

The family-wise failure stays fixed only if each owner holds one piece,
and each is tied to one row of the audit:

- **The evaluation and measurement team** owns the pre-registration: the
  family — which comparisons count — and the q are decided before the
  p-values exist. It owns the post-hoc-family failure, defining the
  family by what happened to be significant, which is the one failure no
  correction procedure can repair.
- **The statistics and experiment team** owns the correction choice:
  the family-wise bar (Bonferroni) versus the false-discovery-rate bar
  (Benjamini-Hochberg). It owns the error-budget failure — the measured
  trade between 0.59 and 0.22 false positives per experiment, and between
  6/500 and 25/500 misses of the true pair, is this team's decision
  against the product's tolerance, not the p-values'.
- **The product owner** owns what a false win costs. It owns the
  ship/reject consequence — pairs 3 and 9 ship as wins under naive
  reading and both are null, so the team that cannot name the cost of a
  null ship cannot choose between the two error budgets.

When ownership is implicit, the measurement team reports the pair that
fired, the statistics team corrects a family nobody pre-registered, and
the product owner ships a null result — the same undefined-family failure
from three sides.

## Evidence boundary

The executed audit uses synthetic paired comparisons with known true
effects, a fixed seed, and the z-test p-value on per-item differences.
It demonstrates the family-wise accumulation of chance hits, the
Benjamini-Hochberg step-up procedure suppressing them, and the measured
power cost on this configuration. It does not extend to real evals,
where comparisons are correlated (the same test items appear in every
pair), sample sizes differ, and p-values are not uniform under the null
— correlation in particular changes the family-wise math, which is why
the chapter's paired-design discussion is the prerequisite.

## Check your mental model

Answer each before opening it.

**1. Twelve comparisons at alpha 0.05 with nothing true: why is the
chance of at least one win 46 percent and not 5 percent?**

<details>
<summary>Answer</summary>

Because the 5 percent is per comparison, and the comparisons are
independent in the audit. The probability that a single comparison stays
silent is 0.95; the probability that all twelve stay silent is 0.95^12 =
0.54, so the probability that at least one fires is 0.46. The null draw
is the mechanism made visible: one pair fired anyway, and the repetition
shows 44.2 percent of naive experiments carrying at least one.

</details>

**2. In the planted draw, pairs 3 and 9 have p-values below 0.05 and BH
keeps them. Why is that the right outcome?**

<details>
<summary>Answer</summary>

Because with 12 tests, p = 0.0255 and p = 0.0170 are not evidence against
the family — under 12 nulls you expect the smallest p-values to reach
below 0.05 by chance, and BH's rank-scaled threshold (k·q/m) is what a
p-value must beat to count. The two pairs would ship as wins under naive
reading; the repetition confirms they are the expected chance hits.

</details>

**3. BH misses the true pair more often than naive testing does. How can
a correction make the real effect harder to find?**

<details>
<summary>Answer</summary>

Because controlling the false discovery rate at q tightens the bar for
the top-ranked test: with m=12 and q=0.10, the smallest p-value needs to
beat 0.0083, which is stricter than the per-test 0.05. A real effect
whose draw lands a p-value between those two numbers survives naive
testing and is dropped by BH. The run measures it: 6/500 versus 25/500
misses. The correction trades a small power loss for a large cut in false
wins.

</details>

## Next

Back to [the significance chapter](../), where the single comparison is
set up, or to [the bigger gap is not the more certain
one](../when-the-interval-decides/) for the companion failure: the
interval, not the point estimate, is what decides — and a family of
intervals multiplies the same mistake.
