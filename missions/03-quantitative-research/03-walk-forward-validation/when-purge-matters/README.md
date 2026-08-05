---
status: verified
level: applied
base: none
label: When purge matters
verified: 2026-08-06
---

# Why is fold-specific fit not strategy fit — and when does purge matter?

**Question:** [stage 03](../) teaches purged, embargoed walk-forward folds
and records an honest note: its fixed linear rule showed no leakage uplift.
This chapter gives the fold real selection power — a threshold grid kept by
in-fold Sharpe — and measures two things the note left open: how far in-fold
fit is from strategy fit, and whether the boundary rows the purge removes
are a measurable, different regime.

**Before this:** [stage 03's walk-forward run](../), including its recorded
null.

## Fold-specific fit is not strategy fit, measured

The ablation reuses the stage's own machinery — same AAPL fetch, same
five-day labels, same walk-forward splitters — and adds one thing: for every
fold, a grid of nine thresholds on the linear prediction, kept by in-fold
Sharpe. The full record is in
[`runs/2026-08-06-fold-fit-leak.md`](runs/2026-08-06-fold-fit-leak.md). The
per-fold table is the chapter's first lesson:

| label days | in-fold Sharpe range | same fold, out-of-fold range |
|---:|---:|---:|
| 5 | 0.47 - 0.63 | 0.015 - 1.88 |
| 20 | 1.02 - 1.40 | -1.06 - 3.74 |

The in-fold number never predicts the out-of-fold number, and it is not
supposed to: the selector is choosing the threshold the fold has already
seen. A strategy is the rule that survives out-of-fold; a fold-fit is the
threshold that won on that fold's own data. Reporting the in-fold number as
the strategy's quality is the exact failure the deflated-Sharpe line exists
to correct.

## The boundary is a different regime

The first label-days test rows of every block have labels whose windows reach
into the training block when the split is unpurged. Measuring them
separately shows they are systematically different from the interior:

| label days | boundary rows Sharpe | interior rows Sharpe |
|---:|---:|---:|
| 5 | 3.17 (25 rows) | 0.85 (590 rows) |
| 20 | 0.65 (100 rows) | 2.41 (507 rows) |

Different in both directions — which is the point. The boundary is not
quietly the same as the interior; it is a regime of its own, and it is the
only place a label-overlap leak could enter the evaluation. This is the
measurement the stage's recorded note said it could not make.

## The purge null, stated plainly

The aggregate out-of-fold Sharpe is 0.93 unpurged versus 1.13 purged at
five-day labels, and 2.12 versus 2.15 at twenty-day labels — both within
fold noise, and consistent with the stage's recorded null. The overlap is
real (the boundary rows prove it exists), but this momentum rule on this
window does not exploit it, so purge changes nothing measurable in the
aggregate. The chapter reports that honestly rather than inventing an
uplift: purge matters when the leak would matter, and the boundary partition
is how you check whether it does. A researcher who skips purge is betting
their rule has no overlap sensitivity; a researcher who measures the
boundary knows whether the bet held.

## Evidence boundary

One ticker, one rule family, two label widths, one fetch window (live
endpoint, drifts between runs). The per-fold and boundary numbers are this
window's result; re-running pulls a newer window and shifts them. The chapter
does not demonstrate an aggregate leakage uplift — it did not observe one —
and does not claim purge is ever unnecessary; it shows where the leak would
enter and how to look for it.

## Check your mental model

Answer each before opening it.

**1. Why can the in-fold Sharpe be 0.62 while the same fold's out-of-fold
Sharpe is 0.015?**

<details>
<summary>Answer</summary>

Because the threshold was selected on the in-fold returns: the selector
keeps the nine candidates' best, and the best of nine on a noisy window is
conditioned on being unusually high. Out-of-fold the same threshold faces
data it was not selected against, so the 0.62 is selection, not signal. This
is the same best-of-N inflation the signal stage measures, on a per-fold
scale.

</details>

**2. The boundary rows score differently from the interior in both label
widths, yet purge changed the aggregate little. What does that combination
establish?**

<details>
<summary>Answer</summary>

That the overlap is real and located where theory says — the boundary rows
whose label windows reach into training — but that this rule does not
exploit it, so removing the overlap changes little in the aggregate. It
separates "the leak exists" from "this strategy leaks," which is exactly the
distinction a purge decision needs: skip purge only when you have measured
the boundary and found your rule insensitive.

</details>

## Next

Back to [stage 03's walk-forward](../), where the folds consume the search
log and the deflated Sharpe adjusts for the search that produced the
candidate.
