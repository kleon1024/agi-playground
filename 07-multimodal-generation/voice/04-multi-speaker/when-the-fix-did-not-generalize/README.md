---
status: verified
level: applied
base: scratch
label: When the fix did not generalize
verified: 2026-08-06
---

# The fix that did not generalize

**Question:** [stage 04](../) retrains the codec at 10 speakers to test
whether the fix that escaped collapse on stage 03's narrow baseline
generalizes. The stage's verdict
is seed-dependent health — this chapter reads the three seeds' final
codebook usage to make the frontier concrete.

**Before this:** [stage 04's multi-speaker run](../) and the codebook-health
line (the collapse chapter, the reset chapter).

## The health, measured

The run ([record](runs/2026-08-06-multi-speaker-health.md)) reads the three
seeds' final usage and MSE:

| seed | codes used | entropy ratio | MSE |
|---:|---:|---:|---:|
| 0 | 18/64 | 0.405 | 0.0271 |
| 1 | 63/64 | 0.760 | 0.0170 |
| 2 | 32/64 | 0.644 | 0.0212 |

## Two readings

**The stage-03 fix does not generalize.** At 10 speakers the codebook
health is seed-dependent again — seed 1 healthy (63/64), seed 0 collapsed
(18/64), seed 2 partial (32/64) — the same seed-dependence the codebook
chapters measured on stage 03's narrow baseline, now at the frontier. A fix
that holds
for a narrow baseline is not a fix for the population; the mechanism (dead
codes, seed-dependent recovery) re-emerges as the data grows.

**The collapsed seed pays a measurable price.** Reconstruction MSE tracks
usage: 0.027 at 18/64 versus 0.017 at 63/64. The collapse is not a usage
count footnote; it is a real quality cost on the worst seed, which is why
the stage reports it and why the reset/EMA 2x2 (stage 05/06) exists as the
next line of the fix.

## Evidence boundary

Three seeds, 10 speakers, the stage's recorded runs. It reads the final
health and its seed dependence; it does not re-train, does not isolate which
speakers drive the collapse, and does not claim the reset/EMA fix would
recover at 10 speakers — that is stage 05's question, unanswered here.

## Check your mental model

Answer each before opening it.

**1. Stage 03's recipe escaped collapse on its narrow baseline — 51-63/64
codes in all three seeds. Why does the same recipe collapse seed-dependently
at 10?**

<details>
<summary>Answer</summary>

Because the fix's effect was measured on a small population; at 10 speakers
the input distribution is wider and the codebook's dead-code dynamics
re-emerge seed-dependently. The fix held where the data was narrow and
failed where it was not — a generalization failure of the intervention, not
of the mechanism, which is exactly why the stage reports the frontier
instead of assuming the fix carries.

</details>

**2. The MSE difference between the collapsed (0.027) and healthy (0.017)
seeds looks small. Why does it still matter?**

<details>
<summary>Answer</summary>

Because a realtime voice contract is per-request: the collapsed seed's
quality penalty lands on every user routed to that model, not on an
average. A 0.010 MSE gap at the codec level propagates through the
reconstruction, and the mission's p50/p95 reporting rule exists precisely
because the tail — here, the worst seed — is what a user experiences.

</details>

## Next

Back to [stage 04's multi-speaker run](../), or to
[stage 05's codebook reset](../../05-codebook-reset/) where the next line
of the fix is measured.
