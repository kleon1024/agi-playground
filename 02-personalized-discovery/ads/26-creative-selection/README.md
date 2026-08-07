---
status: verified
level: applied
base: scratch
label: Creative selection
verified: 2026-08-07
---

# The creative is part of the ad's value

**Question:** [stage 15's eCPM ranking](../15-ecpm-ranking/) used a
click estimate, but the estimate depends on what the ad looks like.
This stage asks which creative an ad shows, and answers: the creative's
expected click rate is context-dependent, so selection is part of the
ad's value.

**Before this:** [stage 15 — eCPM ranking](../15-ecpm-ranking/) for how
the click estimate enters ranking, and [stage 16 — CTR
calibration](../16-ctr-calibration/) for the estimate's honesty.

## The selection, executed

The run ([record](runs/2026-08-07-creative-selection.md)) scores three
creatives per placement context:

| creative | mobile | desktop | winner |
|---|---:|---:|---|
| video | 0.07 | 0.03 | mobile |
| image | 0.04 | 0.05 | desktop |
| text | 0.02 | 0.02 | desktop |

## The mechanism, named

The winner is context-dependent: the video creative wins on mobile, the
image on desktop. A global-average selection would pick video
everywhere and leave desktop clicks on the table. Selecting by context
raises the click rate per placement, which is why the creative is part
of the ad's expected value — it feeds the pCTR that [stage
15](../15-ecpm-ranking/) multiplies by the bid.

## Why this belongs in the mission

Creative selection is where the ads track meets the mission's central
trade: an ad's value is revenue minus displacement, and the creative
decides both sides. A better creative raises revenue per impression; a
worn or mis-contextualized creative (the two detours) quietly lowers
it, and the displacement cost is paid regardless.

## Evidence boundary

The executed per-context CTR table (illustrative, deterministic,
assumed creative-context interaction). It demonstrates the mechanism;
real creative selection is measured per placement and needs
recency-aware estimates, which the [stale-creative
detour](when-the-creative-is-stale/) motivates.

## Check your mental model

Answer each before opening it.

**1. Why does the winner change with context?**

<details>
<summary>Answer</summary>

Because users behave differently per placement. In the feed they browse
and a rich card earns attention; on search they scan and a compact
creative converts better. A single global rank hides that — it would
pick the rich card everywhere and leave search clicks unearned.

</details>

**2. Why is the creative part of the ad's expected value?**

<details>
<summary>Answer</summary>

Because eCPM is bid times click estimate, and the click estimate is a
property of the creative in its context. The image at 0.05 on desktop
is worth more than the video at 0.03 there — selection moves the
expected revenue per impression, which is the revenue side of the
displacement trade.

</details>

## Next

Forward to [stage 27 — bid strategy](../27-bid-strategy/) where the
advertiser's side of the auction is derived.

A detour from here: [logged CTR mixes quality with
wear](when-the-creative-is-stale/) — the executed wear read: a stale
winner's 0.06 logged CTR reflects 200,000 exposures while a new
creative's 0.03 is a cold-start estimate, so selection needs
recency-aware estimates.

Another detour: [context is a feature of creative
selection](when-the-creative-context-changes/) — the executed
per-context read: the rich card wins in the feed (0.08 vs 0.03) and the
compact creative wins on search (0.06 vs 0.02), so a global creative
rank leaves search clicks on the table.
