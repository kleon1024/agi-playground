---
status: verified
level: applied
base: scratch
label: When the margin is the spread
verified: 2026-08-06
---

# The verdict is honest because the margin is checked against the spread

**Question:** [stage 02's report](../) returned NOT MET. This chapter reads
the recorded outcome and asks what made the verdict decisive rather than
inconclusive.

**Before this:** [stage 02's report](../) and its recorded outcome.

## The arithmetic, read

The run ([record](runs/2026-08-06-margin-read.md)) reads the recorded
comparison:

| comparison | margin | GRPO seed spread | reading |
|---|---:|---:|---|
| greedy decode vs random | -0.1493 | 0.0160 | decisively loses |
| greedy decode vs greedy baseline | -0.7513 | 0.0160 | decisively loses |

## Two readings

**A margin inside the spread is a no-result; these margins are not.** The
mission's rule is "a gap smaller than run-to-run spread is no result."
Here the policy loses to both baselines by far more than its own seed
spread — the losses are decisive, not coin-flips. The per-seed structure
(0.078, 0.062, 0.078) is tight, which makes the -0.1493 and -0.7513
margins unambiguous.

**The mechanism behind the decisive losses is the fixed action string.**
The report records that greedy decode emits the same action on every
held-out board in 3/3 seeds — 'RRRR...' for seed 0, 'UUUU...' for seed 1,
'LLLL...' for seed 2. A policy that ignores the board cannot beat
baselines that use it, and the fixed strings are the evidence, not an
inference.

## The fix and its trade

The fix is the margin-vs-spread rule, applied mechanically: a comparison
is a result only when the margin exceeds the policy's own seed spread,
and these two comparisons pass that bar decisively (the -0.1493 and
-0.7513 margins against a 0.016 spread). The trade is that the rule's
strictness is a floor, not a substitute for mechanism: the spread check
proves the loss is not a coin-flip, but the *reason* it is a loss — the
fixed action string — is what the catalogue carries, and a report that
stops at the arithmetic would be a number without a diagnosis. The rule
also deliberately refuses to report small real effects: a margin inside
the spread is a no-result by design, which is the correct bias for a
mission whose acceptance bar demands beating baselines by more than
run-to-run noise.

## Who owns this loop

- **The report owner** owns the comparison rule and its enforcement: the
  margins are computed from committed artifacts, and the per-seed spread
  is the unit of honesty — without it, the -0.1493 could read as a real
  loss when it is, in fact, a decisive one for the wrong reason.
- **The evaluation owner** owns the mechanism read behind the numbers:
  the fixed action strings are the evidence that the loss is structural,
  not marginal.
- **The RL team** owns the seed spread as an input: 3 seeds is the stated
  boundary of the comparison, and a team that wants a tighter verdict
  must add seeds, not soften the rule.

## Evidence boundary

The recorded outcome report (baselines and seed JSONs read mechanically).
It reads that artifact; it does not re-run the policy.

## Check your mental model

Answer each before opening it.

**1. Why is a decisive loss reported, not "inconclusive"?**

<details>
<summary>Answer</summary>

Because the margin rule decides. An inconclusive result is a margin inside
the run-to-run spread — the difference could be a lucky draw. Here the
losses (-0.1493, -0.7513) dwarf the spread (0.0160), so the outcome is
decisive in the mission's own terms: the policy loses, repeatably, and
reporting that plainly is what the declared bar was written for.

</details>

**2. What does the fixed action string add to the numbers?**

<details>
<summary>Answer</summary>

It explains the mechanism. The margins say "the policy loses," and the
fixed strings say why: a policy emitting the same action on every board
has not learned to use the board at all. The two together make the NOT MET
a diagnosable result — the training signal, not the evaluation, is where
the failure lives.

</details>

## Next

Back to [stage 02's report](../), or to
[the honest NOT MET: how the verdict is built](../when-the-verdict-is-not-met/)
which reads the same report's verdict structure.
