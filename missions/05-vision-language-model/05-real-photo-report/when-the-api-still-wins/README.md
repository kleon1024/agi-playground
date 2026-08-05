---
status: verified
level: applied
base: none
label: When the API still wins
verified: 2026-08-06
---

# The build-vs-buy verdict, on real photos

**Question:** [mission 05's real-photo report](../) compared the vision
pathway, the text-only baseline, and the hosted API on real photographs.
The synthetic set's verdict (hosted dominates) was already a NOT MET; this
chapter reads whether real photos change the answer.

**Before this:** [mission 05's real-photo report](../) and the
margin-is-narrow chapter.

## The comparison, read

The run ([record](runs/2026-08-06-real-photo-api.md)) recomputes the API's
accuracy from the recorded raw log:

| arm | accuracy |
|---|---:|
| vision | 0.2374 ± 0.0101 |
| text-only | 0.2222 |
| hosted API | 0.460 (recomputed; recorded 0.4596) |

Hosted API by answer type: yes_no 63.7%, other 36.6%, number 24.0%.

## Two readings

**Real photos do not change the verdict.** Vision beats text-only beyond its
own spread (+0.0152) — the pathway does see real pixels — but the hosted
API beats vision by -0.2222, far beyond any spread. The build-vs-buy answer
holds on the harder input: the API dominates both self-trained arms, so the
mission is NOT MET on real photographs exactly as on the synthetic set.

**The API's edge is answer-type-shaped.** Its accuracy is 63.7% on yes/no
but 24.0% on number questions — the strongest on the easiest type and
weakest where counting is required. The recomputation (0.460 vs recorded
0.4596, per-type within rounding) confirms the log and the report agree,
so the type split is not an artifact.

## Evidence boundary

The recorded raw log (198 questions) and the report's per-arm numbers. It
recomputes the API's accuracy and reads the three-arm comparison; it does
not re-call the API and does not change the mission's NOT MET verdict.

## Check your mental model

Answer each before opening it.

**1. The vision pathway beats text-only on real photos, yet the verdict is
NOT MET. Why is that not a contradiction?**

<details>
<summary>Answer</summary>

Because the mission's acceptance is the build-vs-buy comparison, not the
vision-vs-text comparison. The pathway proves it sees pixels (beats the
blind baseline), but the metric that decides the verdict is whether
building the pathway beats what the hosted API already offers — and the API
dominates by -0.2222. The mission is not about proving vision works; it is
about proving a self-trained pathway is worth building, and on real photos
it is not.

</details>

**2. Why does the answer-type split matter for the verdict?**

<details>
<summary>Answer</summary>

Because it shows where the API's dominance comes from and where it does
not. On yes/no (63.7%) the API is strong; on number questions (24.0%) it
is weak — close to the self-trained arms. A future build-vs-buy decision
could target the type where the API is weakest rather than competing
head-on, and the split is the evidence for that. The verdict is NOT MET
overall, but the type structure is where a different build might find
ground.

</details>

## Next

Back to [mission 05's real-photo report](../../05-real-photo-report/), or
to [the warmup chapter](../../06-warmup-stability/) where the pathway's
stability is the one thing the API comparison does not measure.
