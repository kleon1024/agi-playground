---
status: verified
level: applied
base: scratch
label: The bimodal retry
verified: 2026-08-06
---

# Feedback fixed the fix, not the apply

**Question:** [stage 06's closing the loop](../) gave every failed
no-harness attempt one retry turn with real outcome feedback. This chapter
reads the recorded run and asks what the retry actually changed.

**Before this:** [stage 06's closing the loop](../) and its recorded JSONL.

## The retry, read

The run ([record](runs/2026-08-06-bimodal-read.md)) reads the recorded
matrix:

| tier | retried | diffs applied | resolved |
|---|---:|---:|---:|
| haiku | 6 | 0/6 | 0/6 |
| sonnet | 3 | 1/3 | 1/3 |
| opus | 3 | 1/3 | 1/3 |

## Two readings

**The retry is bimodal: either the corrected diff applied and the fix was
correct, or it did not apply at all.** Applied and resolved coincide in
every row — there is no case of a diff applying but leaving the target
failing. Ten of twelve corrected diffs were rejected by git apply the same
way the first attempts were. The feedback changed the patch's content but
not the apply gate that blocked it.

**The feedback loop's value is visible precisely because the gate did not
move.** Two of twelve retries resolved (sonnet, opus) — the loop is not
useless, it is narrowly useful: it fixes tasks whose failure was in the
patch, not in the apply. Haiku's 0/6 says the cheapest tier's failure was
the apply problem, which no amount of feedback fixes. The bimodality is
what makes that diagnosis legible.

## The fix and its trade

The fix is the applied/resolved coincidence used as a diagnosis: applied
and resolved coincide in every row, so the retry's bottleneck is the
apply gate, not patch quality — a corrected diff either passes git apply
(and the fix was already correct, since the feedback told the model what
the test expected) or is rejected (and nothing was fixed). The trade is
that the diagnosis is only visible because the loop's value is stated
narrowly: two of twelve retries resolved, the loop is not useless, it is
narrowly useful — it fixes tasks whose failure was in the patch, and
haiku's 0/6 is the negative control attributing the cheapest tier's
failure to the gate, which no amount of feedback fixes.

## Who owns the loop

- **The harness owner** owns the apply gate and the diff-construction
  path: haiku's 0/6 points at a tooling fix (better diff construction),
  not a model-feedback fix, and that attribution is the owner's to make.
- **The model team** owns the tier-by-tier reading: the retry's value is
  attributable per tier, and the bimodality keeps "feedback helps" from
  overclaiming across tiers.
- **The eval owner** owns the negative control: haiku's row is what makes
  the sonnet/opus flips interpretable as patch-level fixes rather than
  apply-level ones.

## Evidence boundary

The recorded closing-the-loop JSONL (12 retry attempts, real claude -p
calls, one declared budget and timeout). It reads that artifact; it does
not re-call any model.

## Check your mental model

Answer each before opening it.

**1. Why does "applied" predict "resolved" perfectly here?**

<details>
<summary>Answer</summary>

Because the retry's failure mode is the apply gate, not patch quality. A
corrected diff either passes git apply — in which case the fix was already
correct, since the feedback told the model what the test expected — or it
is rejected, in which case nothing was fixed. The perfect coincidence is
evidence the bottleneck is apply, not correctness.

</details>

**2. What does haiku's 0/6 say about where its failures live?**

<details>
<summary>Answer</summary>

That haiku's no-harness failures were apply failures, not reasoning
failures — feedback gave it the right information and the corrected diff
still did not apply (0/6). The loop cannot fix that gate; a different tool
path (better diff construction) would. The tier-by-tier split is what
attributes the retry's value, and haiku's row is the negative control.

</details>

## Next

Back to [stage 06](../), or to
[does seeing the real outcome help](../does-feedback-help/) which reads the
same run's feedback side.
