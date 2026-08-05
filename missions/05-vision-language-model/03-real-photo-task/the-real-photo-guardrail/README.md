---
status: verified
level: applied
base: none
label: The real-photo guardrail
verified: 2026-08-06
---

# The real-photo guardrail: why image ID, not pixel hash

**Question:** [stage 03](../) filters real photographs into scoreable QA
pairs and splits them train/eval. The synthetic stage's guardrail checked
pixel hashes; this stage's checks image IDs. Why the difference, and what
does the filter keep?

**Before this:** [stage 03's real-photo dataset](../) and the synthetic
stage's seed-vs-pixels lesson.

## The record, read

The run ([record](runs/2026-08-06-real-photo-guardrail.md)) tabulates the
recorded dataset build:

| | |
|---|---|
| source | VQA v2 / COCO (public) |
| filter | answer_type kept iff the majority answer is exactly scoreable |
| images with >=1 scoreable pair | 40,474 of 40,474 |
| disjointness check | COCO image ID, 0 overlap asserted |

Split by answer type (recorded): train 237/101/261, eval 80/25/93 for
yes_no / number / other.

## Two readings

**The filter matches the scoreable contract.** Only majority-answerable
yes/no or single-word answers survive, because those are the ones exact
string match can score — the same convention stage 00 established for
synthetic shapes, applied to real photographs. The filter is what makes
the held-out comparison a real evaluation instead of a paraphrase game.

**The guardrail keys the object that can actually overlap.** The synthetic
stage's failure was procedural — disjoint seeds rendered identical pixels,
so the check had to hash pixels. Real photographs do not collide by
rendering; they overlap by identity (the same COCO image appearing in both
sets). The ID check asserts zero overlap and re-checks the written records
— the guardrail is the same discipline (check the thing that leaks) aimed
at the leak that real data actually has.

## Evidence boundary

The recorded dataset record, no images downloaded. It reads the filter and
the guardrail's key; it does not re-run the download or measure the 32x32
downsample's information loss (the record names that as stage 04's
modeling question).

## Check your mental model

Answer each before opening it.

**1. Why is "the answer is exactly scoreable" the right filter for a held-out
evaluation?**

<details>
<summary>Answer</summary>

Because exact string match needs an unambiguous target: a yes/no or a
single-word majority answer has one correct string, so the pathway's
output can be scored mechanically. An open-ended answer would require a
judge, and a judge is a different evaluation contract. The filter keeps the
comparison honest by keeping every held-out item mechanically scoreable —
the same reason the synthetic stage built its questions the way it did.

</details>

**2. The synthetic guardrail hashed pixels; this one checks IDs. Is that a
weaker check?**

<details>
<summary>Answer</summary>

No — it is the same check aimed at the right object. Pixels were the thing
that could collide in the synthetic generator; in real data, the thing that
can appear on both sides of a split is an image's identity (the same COCO
ID), not a rendered duplicate. Checking IDs catches the real leak directly,
and the recorded run asserts 0 overlap plus a post-hoc re-check on the
written records — a stronger statement than a hash comparison on data that
does not render procedurally.

</details>

## Next

Back to [stage 03's real-photo task](../../03-real-photo-task/), or to
[stage 04's real-photo fusion](../../04-real-photo-vision-fusion/) where
the pathway is scored on this guarded split.
