---
status: verified
level: applied
base: scratch
label: When the margin is narrow
verified: 2026-08-06
---

# The margin is narrow, real, and noisy on the control side

**Question:** [stage 04](../) measured vision versus text-only on real
photographs and reported a +0.0152 margin. A narrow margin is exactly where
the spread rule matters: this chapter reads the three numbers the verdict
depends on.

**Before this:** [stage 04's real-photo run](../) and its recorded verdict.

## The comparison, read

The run ([record](runs/2026-08-06-real-photo-margin.md)) reads the recorded
seeds:

| arm | mean | seed spread | per-seed |
|---|---:|---:|---|
| vision | 0.2374 | 0.0051 | 0.237 / 0.242 / 0.232 |
| text-only | 0.2222 | 0.0354 | 0.212 / 0.192 / 0.263 |
| margin | +0.0152 | — | — |

## Two readings

**The margin is real by the mission's own rule — and it is narrow.** The
gap (+0.0152) is beyond vision's seed spread (0.0051), so it clears the
"a gap smaller than run-to-run spread is no result" bar. But it is a third
of the synthetic set's margin (+0.1105): real photographs shrink the vision
advantage to a sliver, which is why the mission's verdict on the real-photo
chain is NOT MET — the hosted API's margin dwarfs both.

**The noise lives on the control side.** Text-only's spread (0.0354) is 7x
vision's. The comparison is not two equally noisy arms; the vision arm is
the stable one and the text-only baseline is where the variance sits. A
naive reader of "margin +0.0152 with spread 0.0354" would call it noise;
the per-arm read shows the spread belongs to the control, and the vision
pathway is the deterministic side of the comparison.

## The fix and its trade

The fix is applying the spread rule per arm: a margin is a result when it
exceeds the arm's own run-to-run spread, and vision's spread (0.0051) is a
third of the margin — not the pooled-looking 0.0354, which belongs to the
text-only control. The trade is that the rule's per-arm form is exactly
what makes a narrow result legible, and the same form exposes how narrow
it is: the real-photo margin is a third of the synthetic one (+0.1105), so
the pathway's edge is task-dependent and shrinks on harder input. The
narrowing is the honest measure of how much of the synthetic result
carries to real photographs, and the chapter's verdict is that the mission
must report it rather than extrapolate from the synthetic number — the
sliver margin is real by the rule and far below what the hosted API
achieves, which is why the real-photo chain still closes NOT MET.

## Who owns the loop

- **The evaluation owner** owns the per-arm form of the spread rule: a
  pooled spread would misread this run, and the rule's application is an
  eval-standard decision written before the margin is read.
- **The model team** owns the task-dependence read: why the edge shrinks
  from synthetic to real input is a modeling question (harder input,
  majority-answer skew on the control), and the hypothesis belongs to the
  team that would test it.
- **The report owner** owns the verdict the three numbers feed: real by
  the rule, narrow in size, noisy on the control — all three must appear
  together, because each one alone misstates the result.

## Evidence boundary

Three seeds each, the recorded real-photo run; the synthetic margin is the
recorded stage-01 number. It reads the recorded comparison; it does not
re-train, and it does not claim the narrow margin is deployable value — the
mission's NOT MET verdict sits on the hosted-API comparison.

## Check your mental model

Answer each before opening it.

**1. Why is +0.0152 a real margin when the spread rule sounds like it should
swallow it?**

<details>
<summary>Answer</summary>

Because the spread rule is per-arm: a margin is a result when it exceeds the
arm's own run-to-run spread, and vision's spread is 0.0051 — a third of the
margin. The aggregate "spread" that looks larger (0.0354) belongs to the
text-only control, whose noise is a property of the baseline, not of the
vision comparison. Per-arm spreads are what the rule needs, not a pooled
number.

</details>

**2. The real-photo margin is a third of the synthetic one. What does that
narrowing establish about the pathway?**

<details>
<summary>Answer</summary>

That the vision pathway's edge is task-dependent and shrinks on harder
input: synthetic rendered shapes give the pathway its cleanest separation,
and real photographs compress it to a sliver — still beyond the pathway's
own noise, but far below what the hosted API achieves. The narrowing is the
honest measure of how much of the synthetic result carries to real input,
which is why the mission reports it rather than extrapolating from the
synthetic number.

</details>

## Next

Back to [stage 04's real-photo fusion](../),
or to [stage 05's real-photo report](../../05-real-photo-report/) where the
hosted-API comparison closes the verdict.
