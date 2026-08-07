---
status: verified
level: applied
base: scratch
label: When the noise flips the order
verified: 2026-08-08
---

# More channels is more chances for the noise to move the budget

**Question:** [stage 40's privacy-safe attribution](../) measured how
often one adjacent pair flips under noise. This chapter reads the
executed granularity audit and asks the decision-side question that
rate skips: what happens to a report that ranks more than two
channels, when every close pair is another chance for the noise to
flip the budget.

**Before this:** [stage 40 — privacy-safe attribution](../) and its
executed DP-noise model.

## The granularity sweep, executed

The run ([record](runs/2026-08-08-order-flip-budget.md)) compares a
three-channel report with a six-channel report at the same epsilons,
over 1,000 fixed-seed draws each, under the stage's noise model
(uniform of range 100 / epsilon per count):

| report | epsilon | any rank flip | expected misallocated |
|---|---|---:|---:|
| 3 channels | 5.0 | 0.0% | 0.0% |
| 3 channels | 2.0 | 12.3% | 2.5% |
| 6 channels | 5.0 | 61.8% | 3.3% |
| 6 channels | 2.0 | 87.6% | 12.0% |

Adding three close channels to the same budget moves the flip rate
from 12.3 to 87.6 percent at epsilon 2.0 — and the six-channel report
already flips on 61.8 percent of draws at epsilon 5.0, where the
three-channel report never flips.

## The failure mode, named and audited

**The epsilon number hides the report's granularity.** The stage
audit's 12.9 percent display/email flip rate reads like a property of
the privacy dial. This audit shows it is also a property of the report
shape: the six-channel report's tail is a chain of 10-count gaps
(video 240, social 230, affiliate 220), and each gap sits below the
noise floor — at epsilon 2.0 the noise range is ±50, five times the
largest tail gap, so the tail's relative order is random and no
epsilon short of destroying the report can fix it (Dwork 2006, ICALP;
Xiao et al., "Click Without Compromise", arXiv:2406.02463, 2024;
Delaney et al., "Differentially Private Ad Conversion Measurement",
to appear PoPETs 2024, arXiv:2403.15224).

**The flip is a budget movement, not a footnote.** A rank-weighted
50/30/20-style split turns each flip into dollars: the six-channel
report misallocates 12.0 percent of the weekly budget on average at
epsilon 2.0, five times the three-channel report's 2.5 percent. The
privacy team and the budget team read the same report and see
different numbers — the privacy team sees a DP guarantee that is
unchanged, the budget team sees a channel allocation that is moving on
noise. Apple's AdAttributionKit (WWDC24) attacks the same problem on
the platform side by publishing crowd-anonymity-controlled buckets
instead of fine-grained per-source counts, which is the report-shape
fix at the system level.

## The fix and its trade

The fix is to coarsen the decision to the noise floor: merge channels
whose counts are not separable at the report's epsilon (the executed
tail collapses into one "other" line), or report only the top split
and let the rest share a residual — the top channel's 480 clears the
noise floor at every level in the audit, while the tail never does.
The trade is that attribution detail disappears exactly where the
budget has the least room to use it: a merged "other" line cannot tell
video from social, so the team's ability to cut a specific under-
performing channel is gone unless it buys that detail with a higher
epsilon or a trusted-server aggregator that avoids per-report noise
altogether — both of which change the privacy bargain the stage
measured.

## Evidence boundary

The executed granularity sweep over two declared report shapes
(illustrative, deterministic, fixed seed, uniform noise) demonstrates
the granularity mechanism; real privacy-safe attribution needs the
actual channel counts, the true noise mechanism, and the real budget
schedule. The Apple AdAttributionKit documentation (WWDC24) and the
DP-attribution papers are attributed as published.

## Check your mental model

Answer each before opening it.

**1. Why does the six-channel report flip at epsilon 5.0 when the
three-channel report never does?**

<details>
<summary>Answer</summary>

Because the flip rate depends on the count gaps, not just epsilon. The
three-channel report's smallest gap is 50 (display 310 vs email 260),
which clears the ±20 noise range at epsilon 5.0. The six-channel
report adds a 10-count tail chain (240, 230, 220), and those gaps are
half the noise range, so the tail order is essentially random even at
high epsilon. The privacy dial cannot fix a granularity problem.

</details>

**2. What does "coarsen the decision to the noise floor" mean for the
budget?**

<details>
<summary>Answer</summary>

It means reporting only the splits the noise can support — search at
480 clears every noise level in the audit, the middle of the pack is
decidable at high epsilon only, and the tail is never decidable. The
trade is attribution detail: a merged "other" line cannot tell video
from social, so cutting a specific tail channel requires a stronger
privacy bargain (higher epsilon or a trusted aggregator), not a finer
report.

</details>

## Next

Back to [stage 40](../). The
[budget-split detour](../when-the-budget-splits/) shows the second
pressure on the same report: the privacy budget shared across many
reports, which dilutes every one of them.
