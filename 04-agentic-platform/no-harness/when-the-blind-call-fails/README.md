---
status: verified
level: applied
base: scratch
label: When the blind call fails
verified: 2026-08-06
---

# The blind call, read: what one attempt without a loop costs

**Question:** [stage 01](../) is the mission's control — one blind model
call per task, no tools, no feedback, no retry. The harness resolved
18/18; this chapter reads the recorded no-harness matrix and asks what the
baseline actually costs per tier.

**Before this:** [stage 01's no-harness run](../) and its recorded JSONL.

## The matrix, read

The run ([record](runs/2026-08-06-blind-call-read.md)) reads the recorded
18-attempt matrix:

| tier | resolved | total cost | \$/resolved |
|---|---:|---:|---:|
| haiku | 0/6 | \$0.49 | never resolved |
| sonnet | 1/6 | \$1.37 | \$1.37 |
| opus | 3/6 | \$3.28 | \$1.09 |

## Two readings

**Resolve is the number, not cost per attempt.** Haiku is the cheapest arm
per attempt and never resolved — its \$0.49 is pure cost. Cost per attempt
flatters whichever model fails fastest, which is exactly why the mission's
metric is dollars per resolved task, not per attempt. A baseline that
resolves nothing is not cheaper than the loop; it is a floor the loop has
already beaten.

**A lower-resolving arm can cost more per success — and so can a more
expensive one.** Opus costs 6.7x haiku per attempt yet is cheapest per
resolved (\$1.09 vs sonnet's \$1.37), because it resolves 3x more often.
The per-attempt price is a poor predictor of the per-success price, and the
mission's whole cost argument depends on which of the two you read.

## The fix and its trade

The fix is the per-resolved metric: dollars divided by resolved tasks, not
by attempts, because a baseline that resolves nothing is not cheaper than
the loop — it is a floor the loop has already beaten (haiku's \$0.49 buys
0/6). The trade is that the metric makes the control look bad on purpose:
cost per attempt flatters whichever arm fails fastest, and the mission's
decision — what a correct patch costs — is the only number a maintainer
actually pays.

## Who owns the loop

- **The routing owner** owns the metric choice: per-resolved beside
  resolve rate, and the rejection of per-attempt as the flattering
  alternative.
- **The benchmark owner** owns the control's terms — the oracle
  concession and the 240s cap — which set what "one blind call" means.
- **The eval owner** owns the reading that a zero-resolve arm has no
  price, only a cost, and that opus's cheaper-per-success is a resolve
  story, not a bargain per attempt.

## Evidence boundary

The recorded no-harness JSONL (18 attempts, 2 private tasks x 3 tiers x 3
seeds, one declared 240s wall-clock cap); it reads that matrix and does not
re-call any model. It does not compare against the harness here — that is
stage 05's bullet-1 comparison.

## Check your mental model

Answer each before opening it.

**1. Haiku is the cheapest per attempt. Why does the chapter call its row a
floor rather than a bargain?**

<details>
<summary>Answer</summary>

Because it never resolved. Zero successes means the arm bought nothing for
its \$0.49, and per-attempt cost cannot be divided by zero successes into a
meaningful per-success price. In the mission's decision — how much does a
correct patch cost — an arm that produces no correct patches has no price,
only a cost.

</details>

**2. Why does opus, the most expensive per attempt, end up cheapest per
success?**

<details>
<summary>Answer</summary>

Because it resolves 3/6 versus sonnet's 1/6. \$3.28 / 3 successes is \$1.09,
below sonnet's \$1.37/1. The per-attempt price and the per-success price
measure different things, and the mission's metric (dollars per resolved
task) is the one a maintainer actually pays.

</details>

## Next

Back to [stage 01](../), or forward to
[stage 05's report](../../05-report/) which holds this baseline against the
harness bullet by bullet.
