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
