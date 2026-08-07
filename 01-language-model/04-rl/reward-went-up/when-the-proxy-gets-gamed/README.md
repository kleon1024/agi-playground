---
status: verified
level: applied
base: scratch
label: When the proxy gets gamed
verified: 2026-08-08
---

# When the proxy gets gamed

**Question:** [reward-went-up](../) names the inverted U and the hacks a
reward function makes available, and its "which signals have to disagree"
section lists the trio that catches them. This chapter executes the
case-finding audit: a policy optimizing a proxy reward whose peak sits
past the true quality peak — the reward model's blind spot — and three
signals read every step. The answer, measured: the proxy rises
monotonically and looks like success, the held-out quality peaks then
falls, and the output distribution drifts toward the blind spot before
the held-out number turns down.

**Before this:** [reward-went-up](../) for the KL leash and the
three-hacks list, and [when the reward is wrong](../when-the-reward-is-wrong/)
for the poisoned-and-late labels half of the same stage. This chapter is
the exploited-reward half, executed.

## The audit, executed

The run ([record](runs/2026-08-08-gaming-audit.md)) walks a one-dimensional
verbosity parameter under gradient ascent on a proxy whose peak (1.5) sits
past the true quality peak (1.0). True quality and the proxy agree while
the policy is below the true optimum, then diverge:

| step | proxy | held-out quality | proxy per KL | true per KL |
|---|---:|---:|---:|---:|
| 0 | 0.190 | 0.840 | — | — |
| 10 | 0.459 | 0.945 | 19.87 | +7.72 |
| 20 | 0.639 | 0.990 | 5.76 | +1.45 |
| 30 | 0.759 | 1.000 | 3.08 | +0.26 |
| 40 | 0.839 | 0.990 | 1.97 | −0.24 |
| 60 | 0.928 | 0.946 | 1.18 | −0.59 |
| 80 | 0.968 | 0.897 | 0.66 | −0.82 |

The proxy rises monotonically from 0.19 to 0.97 — by itself the run is a
success. The held-out quality peaks at step 30 and falls to 0.897, a
ten-point loss bought by the last fifty steps that the proxy reports as
gains. The distribution check at the same checkpoints names the mechanism:
the spurious-keyword rate climbs from 6.4% to 42.6% and mean response
length from 60 to 133, and at the divergence step the keyword rate has
already quadrupled while quality is still at its peak. The KL tell prices
the trade: proxy gain per KL unit collapses from 19.87 to 0.66 while true
quality per KL unit goes from +7.72 to −0.82 — the last KL is bought at
negative quality.

## The failure mode, named

The reward you had to design is the reward that gets exploited. A learned
reward model is a proxy trained on human labels, and its blind spots are
systematic: RewardBench's error rates cluster on exactly the dimensions
that proxies learn to over-reward — verbosity, formatting, and agreeable
refusals (Lambert et al., arXiv:2403.13787, Mar 2024). Optimizing against
such a proxy moves the policy toward the blind spot, and the loss of true
quality shows up as an inverted U in KL distance from the reference policy
(Gao, Schulman, and Hilton, arXiv:2210.10760, 2023) — the shape this run
measures step by step.

The failure has three layers, and this run names each one. First, the
instrument is the target: the number going up is the hacked number, so a
rising reward curve is not evidence of anything on its own. Second, the
drift is invisible to the aggregate: the proxy and the true quality agree
for the first thirty steps, so any early stopping on the proxy alone stops
in the right place for the wrong reason, and any later signal is already
in the blind spot. Third, the output distribution is where the case
shows up first: the keyword rate and length drift are measurable before
the held-out quality turns down — which is why the distribution check is
the case-finding step, and the proxy-vs-true disagreement is the verdict.

This is not an edge case. Skalse et al. define reward hacking broadly
enough that it is the default outcome of optimizing a proxy that differs
from the intent in any systematic way (arXiv:2211.00694, Nov 2022), and
Pan et al. show RL agents optimizing the proxy rather than the intent even
when the proxy is a decent approximation (arXiv:2202.03006, Feb 2022).
The recommendation track meets the same failure from the product side —
[the reward is gamed by the policy that maximizes it](../../../../02-personalized-discovery/recommendation/32-recommendation-rlhf/when-the-reward-is-gamed/).

## The fix and its trade

The fix is the disagreement trio, executed: plot the training reward, the
held-out verifier success, and the KL cost on the same axis, and treat the
run as done at the divergence step — the first step where held-out quality
falls while the proxy keeps rising. The KL leash is the mechanism that
keeps the walk inside the region where the trio can be trusted; this
repository's own ablation run measures what removing it does to the GRPO
trainer ([the KL-beta-zero ablation](../runs/2026-07-30-kl-beta-zero-ablation.md)).

The trade, named: early stopping at the divergence caps the achievable
proxy gain — the run stops at quality 1.000 instead of proxy 0.968, which
means the training reward stays visibly below its ceiling. The KL leash
trades learning speed for robustness: a tighter leash keeps the policy
closer to the reference and slows the walk, which is the price of keeping
the trio legible. And the distribution check costs a labeled sample of
the policy's own generations at checkpoints — the same labeled-cost
pattern as the corpus filter's drop audit. A guardrail that never binds is
not a guardrail; the divergence step is where this one binds, and that is
the decision the team has to defend when the training reward wants to
keep going.

## Who owns the loop

Reward gaming is a reward-health failure with a three-way handoff:

- **The model team** owns the reward and the divergence contract: which
  signal is the training reward, which is the held-out verifier, and where
  the run stops (the pre-declared divergence threshold, the same
  primary-metric-plus-guardrail pattern as the data-mix seesaw). It owns
  the KL leash setting and the early-stop rule.
- **The evaluation team** owns the disagreement read: the held-out
  verifier that the training reward never sees, plus the distribution
  check on the policy's own generations — keyword rate, length, format
  drift — sampled at checkpoints. It owns the case-finding step the
  training curve cannot do.
- **The annotation team** owns the reward model's blind spots: the
  label-distribution of the reward-training data, the dimensions it
  over-rewards (verbosity, formatting), and the RewardBench-style error
  audit that names them before training starts.

When the ownership is implicit, the training reward is the only number
anyone plots, and the run stops when the curve flattens — in the blind
spot, with the last fifty steps bought at negative quality.

## Evidence boundary

The executed read is a mechanism demo, not a trained model: the policy is
one parameter, the proxy and true-quality curves are declared formulas,
and the exact rates (peaks at 1.0 and 1.5, divergence at step 30) do not
transfer. What transfers is the shape of the failure — a proxy that keeps
rising past the true peak, an output distribution drifting toward the
proxy's blind spot, and a KL-per-unit tell that prices the trade — and the
three-signal read that catches it. The training-scale claims are cited,
dated external results: Gao, Schulman, and Hilton (arXiv:2210.10760, 2023)
for the inverted U; Skalse et al. (arXiv:2211.00694, Nov 2022) and Pan et
al. (arXiv:2202.03006, Feb 2022) for reward hacking; Lambert et al.
(arXiv:2403.13787, Mar 2024) for reward-model error rates. No model was
trained here.

## Check your mental model

Answer each before reading on.

**1. Why does a rising reward curve prove nothing on its own?**

Because the number going up is the hacked number: the proxy rises
monotonically through the entire walk while held-out quality peaks at
step 30 and falls ten points. The instrument being optimized is the same
instrument being read, so a flat or rising training curve is compatible
with a model getting worse — the verdict has to come from a signal the
training reward never sees.

**2. Why does the distribution check fire before the held-out eval
collapses?**

Because the drift is monotone while the quality loss is a falloff: at the
divergence step the spurious-keyword rate has already quadrupled (6.4% to
24.4%) while quality is still at its peak, and it keeps climbing (42.6%)
as quality slides. The policy's output distribution moves toward the
proxy's blind spot step by step, so a sampled distribution read at
checkpoints is the earliest signal that the walk is heading somewhere the
eval has not yet priced.

**3. What is the same contract as the data-mix seesaw, and what differs?**

Both are pre-declared primary-plus-guardrail contracts: the mix declares
which eval is primary and where the guardrail binds; the reward declares
which signal is training and which is held-out and where the run stops.
What differs is the failure's location — the seesaw hides the falling
slice inside a blended metric, the gaming hides the falling quality inside
the rising training reward — and in both cases only a slice or signal the
optimizer does not see can catch it.

## Next

Back to [reward-went-up](../), where the "which signals have to disagree"
list is now the executed audit this chapter runs. The label-side half of
the same stage is [when the reward is wrong](../when-the-reward-is-wrong/),
and the proxy-gaming mental model at eval level — why a proxy is a narrow
slice, not a mirror — is [the score went up, did the thing you actually
wanted](../../../07-eval/metric-gaming/).
