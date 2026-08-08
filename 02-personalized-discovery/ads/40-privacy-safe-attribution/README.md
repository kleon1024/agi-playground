---
status: verified
level: applied
base: scratch
label: Privacy-safe attribution
verified: 2026-08-07
---

# The noise flips the order that spends the budget

**Question:** stage 30's measurement reads per-user behavior. This
stage asks what attribution looks like when the platform must not see
the individual and answers: differential privacy — noise is added to
channel counts, and the noise trades privacy against the accuracy of
the budget decision, because the budget follows the *order* of the
counts, and order is exactly what noise destroys first.

**Before this:** [stage 30 — ads measurement](../30-ads-measurement/)
for what the measurement must decide, and [stage 27 — bid
strategy](../27-bid-strategy/) for the budget the attribution feeds.

## The noisy rank, executed

The run ([record](runs/2026-08-07-privacy-safe-attribution.md)) adds
Laplace noise at epsilon 2.0:

| channel | true | noisy |
|---|---:|---:|
| search | 480 | 462 |
| display | 310 | 275 |
| email | 260 | 275 |

True rank: search, display, email. Noisy rank: search, email, display.
Order preserved: no.

## The mechanism, named

Attribution needs aggregated channel counts; privacy forbids publishing
the true counts because an adversary could isolate an individual's
contribution. Adding calibrated noise hides any individual's
contribution while keeping the aggregate roughly usable. The executed
draw shows the trade: the noise flipped display and email (275 and 275),
so the rank that decides budget changed even though the true order was
clear. Epsilon is the dial between the two — the noise range is 100
divided by epsilon, so every halving of epsilon doubles the noise
(Dwork 2006, ICALP, introduced the framework the industry now builds
measurement on).

## The failure mode, named and audited

**Noise flips the order that spends the budget.** The audit
([record](runs/2026-08-08-epsilon-flip.md)) sweeps epsilon over 1,000
fixed-seed draws per level and measures how often the display/email
pair flips:

| epsilon | noise range | display/email flips | top-1 flips | full order kept |
|---:|---:|---:|---:|---:|
| 5.00 | ±20 | 0.0% | 0.0% | 100.0% |
| 2.00 | ±50 | 12.9% | 0.0% | 87.1% |
| 1.00 | ±100 | 27.6% | 0.9% | 71.5% |
| 0.50 | ±200 | 37.0% | 16.7% | 48.0% |
| 0.25 | ±400 | 43.4% | 31.6% | 32.4% |

At the stage's own epsilon 2.0 the close pair flips on 12.9 percent of
reports, so over twelve weekly reports the chance of at least one
flipped allocation is 1 - (1 - 0.129)^12 = 81 percent. The verdict is
measured: **THE NOISE FLIPS THE ORDER THAT SPENDS THE BUDGET.** Epsilon
must clear the gap that matters — at 5.0 the noise range is smaller
than the 50-count gap and the order never flips; at 2.0 the range
equals the gap and the budget moves on noise roughly once a quarter.
The privacy guarantee is unchanged in every row; the decision accuracy
is not, which is why the two dials are the same knob.

**More channels is more chances for the noise to move the budget.** The
[noise-flips-the-order detour](when-the-noise-flips-the-order/)
measures the report-shape side of the same failure: a six-channel
report flips on 87.6 percent of draws at epsilon 2.0 against 12.3
percent for three channels, and already flips on 61.8 percent at
epsilon 5.0, because its tail is a chain of 10-count gaps below the
noise floor. Every close pair the report adds is another chance for the
noise to move money.

**The privacy budget splits and dilutes every report.** The
[budget-split detour](when-the-budget-splits/) reads the third
pressure: one report gets epsilon 2.0 and noise scale 0.5, 100 reports
get epsilon 0.02 each and noise scale 50, so publishing more analyses
is not free — every additional report dilutes the signal of all the
others, and the team's appetite for reports and the accuracy of each
report are one decision made at the budget level.

## The fix and its trade

The fix is to set epsilon against the decision-relevant gap, not the
smallest count: the noise range is 100 divided by epsilon, so the dial
must clear the gap between the channels the budget actually
distinguishes. The audit prices the threshold — at the stage's own
epsilon 2.0 the close pair flips on 12.9 percent of reports, and twelve
weekly reports have an 81 percent chance of at least one flipped
allocation, while at epsilon 5.0 the noise range is smaller than the
50-count gap and the order never flips. Report shape is the second
lever: a six-channel report flips on 87.6 percent of draws against 12.3
percent for three, so the report is coarsened to the noise floor.

The trade is that every dial that protects the order spends the same
privacy budget: raising epsilon weakens the guarantee, and publishing
more reports dilutes all of them — one report gets epsilon 2.0 and
noise scale 0.5, 100 reports get epsilon 0.02 each and noise scale 50.
The privacy guarantee is unchanged in every row of the audit; the
decision accuracy is not, which is why the two dials are one knob and
the product team owns how many reports the guarantee will cover.

## Who owns the loop

The privacy dial, the report shape, and the budget split are owned by
three different teams, and each owner is tied to one of the failure
modes above:

- **The measurement and privacy team** owns the epsilon budget and the
  noise mechanism that publishes the counts. It owns the flip-rate
  failure — the audit's 12.9 percent at epsilon 2.0 is a
  measurement-pipeline defect before it is a budget surprise, and the
  team's epsilon choice is the dial that sets the rate (Dwork 2006;
  Delaney et al., "Differentially Private Ad Conversion Measurement",
  to appear PoPETs 2024, arXiv:2403.15224, for the ad-measurement
  analogue).
- **The reporting and budget team** owns the report shape: how many
  channels are published and how the rank is consumed. It owns the
  granularity failure — the 87.6 percent six-channel flip rate is a
  report-design decision, and the fix is to coarsen the decision to the
  noise floor, the crowd-anonymity-bucket approach Apple's
  AdAttributionKit uses on the platform side (WWDC24).
- **The product and trust team** owns the privacy promise and the
  accounting that spends it. It owns the budget-split failure — the
  shared-resource cost of every extra report is a product decision
  (how many reports the product will publish) that the privacy
  guarantee alone cannot answer, and the platform-side alternative is
  central aggregation (Xiao et al., "Click Without Compromise",
  arXiv:2406.02463, 2024).

When the ownership is implicit, the privacy team ships an epsilon, the
reporting team ships a fine-grained report, and the budget team ships a
decision that moves on noise — each side correct within its own
definition, wrong for the loop as a whole.

## Why this belongs in the mission

The ads track's budget decision depends on measurement, and measurement
now runs under privacy constraints that change what can be published.
This is the mission's frontier claim for ads: the numbers the budget
uses have to survive noise, and the survival condition is a measured
decision-error rate, not a guarantee on the noise distribution. The
mission's discipline applies — the privacy mechanism is admitted only
where its error mode is measured, and the detours price the two
secondary pressures: report granularity and the shared privacy budget.

## Evidence boundary

The executed noisy draw and the epsilon-flip audit over declared counts
(illustrative, deterministic, assumed Laplace noise, fixed seed)
demonstrate the mechanism and its error rate; real privacy-safe
attribution needs the true epsilon budget, the actual noise mechanism,
and the real report schedule, because the flip rate depends on the true
count gaps, which are private by definition. The Dwork, PoPETs 2024,
arXiv:2406.02463, and Apple AdAttributionKit (WWDC24) citations are
attributed as published.

## Check your mental model

Answer each before opening it.

**1. What does the noise protect, and what does it cost?**

<details>
<summary>Answer</summary>

It protects the individual — no single user's contribution can be
recovered from the published aggregate. The cost is decision accuracy:
the executed draw reorders display and email, so the attribution rank
the budget follows changed. Epsilon is the dial: more noise means
stronger privacy and a weaker signal for the budget decision, and the
audit prices the dial — 12.9 percent of reports flip the close pair at
epsilon 2.0.

</details>

**2. Why is the order of the noisy counts the thing that matters?**

<details>
<summary>Answer</summary>

Because the budget decision is ordinal — it moves spend toward the
channels that rank highest. A small error in absolute counts is
harmless; an error that flips the order moves money. The executed run
shows the flip: search stays on top, but display and email swap at 275,
so the second allocation decision is wrong even though the totals are
nearly right. The audit shows the aggregate: over twelve weekly reports
at epsilon 2.0, there is an 81 percent chance of at least one flipped
allocation.

</details>

**3. Why is "the noisiest plausible draw keeps the order" the right
design constraint?**

<details>
<summary>Answer</summary>

Because the budget decision must not move on noise, and noise is a
distribution — the average draw is not the dangerous one. The audit's
12.9 percent flip rate at epsilon 2.0 means roughly one report in eight
reorders display and email, and over a quarter of reports the chance of
seeing at least one flip is 81 percent. Setting epsilon so even the
unlucky draw preserves the rank (the way 5.0 does, at the cost of a
weaker privacy bar) is the only constraint that makes the report safe
for the budget it feeds.

</details>

## Next

The frontier ads track continues. Next is [stage 41 — LLM creative
generation](../41-llm-creative-generation/), where the creative itself
is generated.

A detour from here: [more channels is more chances for the noise to
move the budget](when-the-noise-flips-the-order/) — the executed
granularity read: at epsilon 2.0 a six-channel report flips on 87.6
percent of draws against 12.3 percent for three channels, so the
report shape is a privacy cost the epsilon number alone does not show.

Another detour: [the noise is too high and the order
collapses](when-the-noise-is-too-high/) — the executed sweep read: at
epsilon 5 the order survives, at 0.5 the noise reorders email above
display, so the noisiest plausible draw must still keep the budget
decision intact.

Another detour: [the privacy budget splits and dilutes every
report](when-the-budget-splits/) — the executed split read: one report
gets epsilon 2.0 and noise scale 0.5, 100 reports get epsilon 0.02
each and noise scale 50, so every additional report dilutes the signal
of all the others.
