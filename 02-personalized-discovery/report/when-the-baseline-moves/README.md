---
status: verified
level: applied
base: scratch
label: When the baseline moves
verified: 2026-08-07
---

# The baseline that moved

**Question:** [stage 09's report](../) compares the system against a
popularity baseline. This chapter reads the executed multi-period run and
asks what a dated baseline claim actually proves.

**Before this:** [stage 09 — report](../) and its executed evaluation.

## The drift, executed

The run ([record](runs/2026-08-07-baseline-read.md)) recomputes the
baseline per week:

| period | system | baseline | verdict |
|---|---:|---:|---|
| w1 | 0.42 | 0.38 | beats |
| w2 | 0.45 | 0.46 | loses |
| w3 | 0.44 | 0.39 | beats |

## Two readings

**The same system beats popularity in week 1, loses in week 2, and wins
again in week 3.** The system's quality barely moves (0.42 to 0.45 to
0.44); the baseline is what swings — 0.38, 0.46, 0.39. When a popular
item carries the week's demand, popularity is hard to beat; when demand
is diffuse, it is easier. The verdict is a property of the period, not a
property of the system.

**A report dated to one period says when the win holds, not forever.**
The mission's outcome claim must name its window — the nDCG@10 lift over
popularity during the measured period — because the executed run shows
the same numbers flipping across windows. That is not a flaw in the
report; it is the correct scope of the claim. The baseline is the demand
curve, and the demand curve moves.

## The fix and its trade

The fix is to recompute the baseline over the same window as the system and
date every claim to that window. The executed drift run prices why: the
system's quality barely moves (0.42, 0.45, 0.44) while the popularity
baseline swings 0.38, 0.46, 0.39, flipping the verdict from beats to loses
to beats across weeks — the verdict is a property of the period, not of
the system, because the baseline is the demand curve and the demand curve
moves.

The trade, named: a dated claim is narrower but true, and the alternative
is an undated headline that silently stops holding. The discipline also
means labeling a new evaluation context — when the catalogue, split,
metric definition, or eligibility policy changes, rerun both baselines and
never append incomparable points to a trend line. The hidden cost is in
the plumbing: a change in logging cutoff or eligibility can dominate a
model change while leaving a familiar metric label unchanged, which is why
the report must record the exact command, revision, split, and checksums
next to the arrays.

## Who owns the loop

- **The evaluation team** owns same-window baseline recomputation and the
  evaluation-context label when inputs change.
- **The data pipeline team** owns the logging cutoff and eligibility rules
  that can move a baseline without a model change — their changes are
  context changes, not noise.
- **The product owner** owns the windowed claim: the mission outcome is the
  lift over the declared baseline during the measured period, and no wider
  claim is licensed by the report.

## Evidence boundary

The executed hand-built period table (illustrative, deterministic). It
demonstrates the drift mechanism; real reports must recompute the
baseline over the same window as the system to keep the comparison
honest.

## Check your mental model

Answer each before opening it.

**1. Why does the system lose in w2 without getting worse?**

<details>
<summary>Answer</summary>

Because the baseline rose, not the system fell. Week 2's demand is
concentrated on popular items, and popularity predicts them well — the
baseline reaches 0.46 while the system's 0.45 is a marginal miss. Beating
popularity is harder exactly when popularity is right, and when it is
right is a property of the week's demand, outside the system's control.

</details>

**2. What would make the w2 verdict honest?**

<details>
<summary>Answer</summary>

Reporting the window: the claim becomes "the system beat popularity in w1
and w3, and did not in w2", with the baseline recomputed per window. That
is more useful than a single aggregate because it separates the system's
behavior from the demand curve's. The executed run is the template for
that report — each period pairs the system and baseline over the same
data, so the comparison never mixes two different worlds.

</details>

## Next

Back to [stage 09](../), or to
[the variance that decides](../the-variance-that-decides/) for the
seed-level uncertainty on the same evaluation.
