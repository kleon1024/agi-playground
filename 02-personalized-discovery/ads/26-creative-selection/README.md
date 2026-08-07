---
status: verified
level: applied
base: scratch
label: Creative selection
verified: 2026-08-07
---

# The creative that won on history keeps winning after it stopped earning its slot

**Question:** [stage 15's eCPM ranking](../15-ecpm-ranking/) used a
click estimate, but the estimate depends on what the ad looks like.
This stage asks which creative an ad shows, and answers: the creative's
expected click rate is context-dependent, so selection is part of the
ad's value — and the audit shows a selection that averages logged CTR
crowns the stale winner while a newer, better creative waits for
traffic it never gets.

**Before this:** [stage 15 — eCPM ranking](../15-ecpm-ranking/) for how
the click estimate enters ranking, and [stage 16 — CTR
calibration](../16-ctr-calibration/) for the estimate's honesty.

## The mechanism, executed

The run ([record](runs/2026-08-07-creative-selection.md)) scores three
creatives per placement context:

| creative | mobile | desktop | winner |
|---|---:|---:|---|
| video | 0.07 | 0.03 | mobile |
| image | 0.04 | 0.05 | desktop |
| text | 0.02 | 0.02 | desktop |

The winner is context-dependent: the video creative wins on mobile, the
image on desktop. A global-average selection would pick video
everywhere and leave desktop clicks on the table. Selecting by context
raises the click rate per placement, which is why the creative is part
of the ad's expected value — it feeds the pCTR that [stage
15](../15-ecpm-ranking/) multiplies by the bid.

## The failure mode, named and audited

**Selection that averages logged CTR crowns the stale winner.** The
audit ([record](runs/2026-08-08-wear-exploration.md)) serves 20,000
placements (fixed seed) to a mature creative whose lifetime CTR is
0.06 but whose true rate decays toward 0.025, and a new creative whose
true rate is 0.04:

| policy | clicks | served A | served B | clicks/imp |
|---|---:|---:|---:|---:|
| greedy, lifetime CTR | 635 | 20,000 | 0 | 0.0318 |
| epsilon-greedy 0.10, lifetime | 645 | 18,981 | 1,019 | 0.0323 |
| greedy, recency-weighted (EWMA) | 828 | 7,700 | 12,300 | 0.0414 |
| Thompson, decaying counts | 807 | 8,444 | 11,556 | 0.0403 |

The verdict is measured: greedy on lifetime CTR serves the mature
creative for all 20,000 placements — its 0.06 history hides the decay,
so selection never estimates the alternative and earns 635 clicks.
Exploration alone barely helps: epsilon-greedy corrects the new
creative's estimate but the greedy arm still reads the same sticky
average (645 clicks). The fix is the estimator, not the policy: a
recency-weighted EWMA (828) or a Thompson posterior with decaying
counts (807) lets selection see the wear and switch, recovering about
30 percent of the clicks (Moriwaki, Nakagawa, Hisano & Ariu, 2019,
arXiv:1908.08936, model ad creative value as a function of served
impressions, wear-in and wear-out; Agrawal & Goyal, 2012,
arXiv:1203.4217, for Thompson sampling's exploration-exploitation
guarantee).

**A creative with no history cannot be priced.** The
[cold-start detour](when-the-creative-has-no-history/) sweeps
exploration from 0.00 to 0.20 against a new creative with a
pessimistic 0.02 prior: raising epsilon serves it 475 to 1,994
placements and corrects the estimate toward 0.04, but clicks move only
625 to 653 — the corrected estimate still loses to the incumbent's
sticky lifetime average, so exploration learns the truth and the
estimator refuses to use it. Cold start needs both traffic and a
recency-aware estimate (He, Pan, Jin et al., 2014, ADKDD, describe
the online learning and controlled-traffic pipeline for click
prediction at Facebook).

**Context is a feature, and so is age.** The
[context-changes detour](when-the-creative-context-changes/) shows the
same creative wins in one placement and loses in another (rich card
0.08 in the feed, 0.02 on search; compact 0.03 and 0.06), and the
[stale-creative detour](when-the-creative-is-stale/) shows logged CTR
mixes quality with wear (creative_a's 0.06 reflects 200,000 exposures;
creative_c's 0.03 is a cold-start estimate). Both are features the
selection model needs — placement and recency — not labels on top of a
global average.

## Who owns the loop

The creative only earns what someone is accountable for at each side of
the selection loop, and each owner is tied to one of the failure modes
above:

- **The creative-ranking team** owns the estimate: the context features,
  the recency-aware update, and the cold-start prior. It owns the
  stale-winner failure — the audit measured greedy serving 20,000
  placements to a creative whose true rate had decayed to 0.025, and
  the recency-weighted fix recovering 828 versus 635 clicks (Moriwaki
  et al., 2019).
- **The delivery and exploration team** owns the traffic allocation
  that prices cold creatives: how much serving stream goes to new
  creatives and how it is targeted. It owns the learning cost — the
  cold-start sweep's epsilon dial is its control, and exploration that
  corrects an estimate the estimator cannot use is a budget with no
  selection change (Agrawal & Goyal, 2012; He et al., 2014).
- **The ads-measurement team** owns the per-creative verdict: CTR by
  context and by age, time-to-correct for cold creatives, and whether
  the corrected estimate ever changes what gets served. It owns the
  invisible-wear failure — a 0.06 lifetime average that hides 0.025
  current value reads healthy on a campaign report until the columns
  above are split by creative age.

When the ownership is implicit, the ranking team averages logged CTR,
the delivery team never allocates cold-start traffic, and the worn
creative keeps winning on history while the better one never gets
estimated — 635 clicks against a possible 828, with nobody owning the
gap.

## Why this belongs in the mission

Creative selection is where the ads track meets the mission's central
trade: an ad's value is revenue minus displacement, and the creative
decides both sides. A better creative raises revenue per impression; a
worn or mis-contextualized creative quietly lowers it, and the
displacement cost is paid regardless. The audit adds the industrial
detail: selection is an online learning problem with a wear signal and
a cold-start prior, not a one-time per-context table — and the
estimator, not the exploration policy, is where the failure lives.

## Evidence boundary

The executed per-context CTR table and the audit's 20,000 synthetic
placements (fixed seed, declared wear functions) are illustrative and
deterministic. They demonstrate the mechanism and the stale-winner
arithmetic; real creative selection is measured per placement with
recency-aware estimates, real wear curves are fitted per segment and
per creative family, and the exploration budget is set per market
rather than declared.

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

**2. Your selection model keeps serving the creative with the best
lifetime CTR. What is it missing?**

<details>
<summary>Answer</summary>

Wear. The lifetime average mixes the creative's quality with its
history: a creative that earned 0.06 when fresh can be at 0.025 now,
but its average still wins. The audit measured greedy on lifetime CTR
serving it for all 20,000 placements while a genuinely better creative
waited — 635 clicks against the recency-aware estimator's 828. The
estimate needs a window or a decay, not the lifetime average.

</details>

**3. Why does exploration alone not fix a cold creative?**

<details>
<summary>Answer</summary>

Because exploration feeds the estimator, and the estimator decides
whether the corrected value can win the arm. The cold-start sweep
served a new creative 1,994 placements and corrected its prior from
0.02 to 0.036, but the corrected estimate still lost to the
incumbent's sticky 0.06 average — clicks barely moved (625 to 653).
Pair the exploration budget with a recency-aware estimate, or the
correction is wasted.

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

A third detour: [a creative with no history cannot be
priced](when-the-creative-has-no-history/) — the executed sweep read:
raising exploration from 0 to 0.20 corrects a cold creative's prior
from 0.02 toward 0.04 but moves clicks only 625 to 653, so exploration
learns the truth and the sticky estimator refuses to use it.
