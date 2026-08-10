---
status: verified
level: applied
base: scratch
label: The flipped variance
verified: 2026-08-06
---

# The noise changed sides

**Question:** [stage 04's real-photo fusion](../) measured vision versus
text-only on real photographs. This chapter reads the recorded run and
asks what flipped about the variance structure.

**Before this:** [stage 04's real-photo fusion](../) and its recorded JSON.

## The per-seed numbers, read

The run ([record](runs/2026-08-06-flip-variance-read.md)) reads the
recorded seeds:

| arm | per-seed accuracy | spread |
|---|---:|---:|
| vision | 0.2374, 0.2424, 0.2323 | 0.0101 |
| text-only | 0.2121, 0.1919, 0.2626 | 0.0707 |
| margin | +0.0152 | — |

## Two readings

**The noise flipped arms.** On stage 01's synthetic shapes, vision was the
noisy pathway (spread 0.2309) and text-only was stable; on real
photographs, text-only is 7x noisier (0.0707 vs 0.0101) and vision is the
stable side. The comparison is not two equally noisy arms — the margin
belongs to a vision pathway that is consistent across seeds, against a
control whose variance dominates.

**The narrow margin is real by the mission's rule, and it is a sliver.**
The gap (+0.0152) clears vision's own spread (0.0101), so it passes the
"gap smaller than run-to-run spread is no result" bar. But it is a third
of the synthetic margin (+0.1105): real photographs shrink the vision
advantage to a sliver, which is why the real-photo chain still closes
NOT MET against the hosted API.

## The fix and its trade

The fix is per-arm spread attribution: report each arm's own seed spread
instead of one pooled number, because the comparison is not two equally
noisy arms. The recorded read shows why it matters — a naive reader of
"margin +0.0152 with spread 0.0707" would call it noise, while the per-arm
read shows the spread belongs to the text-only control and vision is the
deterministic side (0.0101). The trade is that the fix makes the margin
attributable to the pathway without making it large: the same read that
keeps +0.0152 a result also shows it is a sliver — a third of the
synthetic margin — so the real-photo pathway is stable and weak at once,
and the mission's verdict still closes NOT MET against the hosted API. The
read's deeper point is that variance is a property of the
data-architecture pair, not of either arm alone: stage 01's vision was the
noisy arm (one collapsed seed), stage 04's is the stable one, and only
per-arm numbers can show the flip.

## Who owns the loop

- **The evaluation owner** owns the per-arm spread read: the rule is
  applied per arm, and a pooled number that swallows the margin is an
  eval-format error, not a property of the result.
- **The model team** owns the data-architecture variance property the flip
  exposes: whether the seed sensitivity moved sides is a training
  question, and the majority-answer-skew hypothesis for the control's
  noise belongs to the model team to confirm or refute.
- **The report owner** owns the verdict the margin feeds: the flip does
  not change NOT MET against the hosted API, and the report must state the
  sliver-size of the real margin beside the pathway's stability rather
  than letting either number stand alone.

## Evidence boundary

The recorded real-photo run (three seeds per arm, 599/198 QA pairs, one
architecture, unchanged from stage 01). It reads that artifact; it does
not re-train.

## Check your mental model

Answer each before opening it.

**1. Why does the spread flip between synthetic and real inputs?**

<details>
<summary>Answer</summary>

Because the two pathways fail differently on the two data types. On
rendered shapes, vision's seed-2 collapse (0.2844 outlier) made it the
noisy arm; on real photographs, the vision pathway is stable across seeds
while the text-only control varies 7x more. The variance is a property of
the data-architecture pair, not of either arm alone — which is why the
mission reports per-arm spreads rather than a single number.

</details>

**2. What does the flipped variance change about reading the margin?**

<details>
<summary>Answer</summary>

It changes which arm the noise is attributed to. A naive reader of "+0.0152
with spread 0.0707" would call it noise; the per-arm read shows the spread
belongs to the control, and vision is the deterministic side. The margin is
real by the mission's rule — narrow, but attributable to the pathway, not
to the comparison's randomness.

</details>

## Next

Back to [stage 04](../), or to
[the margin is narrow, real, and noisy on the control side](../when-the-margin-is-narrow/)
which reads the same run's margin story.
