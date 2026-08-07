---
status: verified
level: applied
verified: 2026-08-01
label: How it fails
---

# How does it fail, and does it cheat?

**Question:** stage 03's full-harness attempts resolved every task, every
tier. Does that mean this mission's guardrails have nothing to show, or does
it mean they have not yet been asked a hard enough question?

**The artifact this chapter follows** is one table, built from every real
model attempt this mission has produced so far — no new attempts, no new
model calls, only a category read off records that already exist:

```text
                        harness (18)   no-harness (18)
resolved                18/18          4/18
target_still_failing    0/18           12/18
timeout                 0/18           2/18
tampered                0/18           0/18
```

By the end you will be able to say what stage 03's empty failure row does and
does not establish, and which specific failure mode accounts for eleven of
stage 01's twelve unresolved attempts.

**Before this:** [stage 02](../02-agent-loop/), which defines the categories
this reads; [stage 01](../01-no-harness/) and
[stage 03](../03-cheap-or-expensive/), whose real attempts this catalogues.

## Stage 03's full-harness attempts: an empty failure row

Every category besides `resolved` reads 0/18 for the full-harness arm. With
tool access, a real test command, and up to 25 steps to retry, none of the
three model tiers needed a second observation to notice a wrong patch on this
task set. That is a real result — this task set's failure surface, under a
full harness, is empty — not a gap in what this chapter looked for. A larger
or more adversarial task set could still surface harness-level failures this
one did not; see `does_not_prove`.

## Stage 01's no-harness attempts: where the failures actually are

**`target_still_failing`, 12/18 — and eleven of those never applied at all.**
`git apply` rejected eleven of the twelve non-resolving diffs outright, before
any test ever ran again. One inspected by hand (`haiku`, task `354c352`, run
2) claimed a hunk spanning 17 old-side and 43 new-side lines; the diff body it
actually wrote spanned 19 and 42. The model miscounted its own patch, and
`git apply`'s refusal is the harness working, not failing. Only one of the
twelve unresolved attempts (`haiku`, `b81c414`, run 1) produced a
syntactically valid diff that simply did not fix the bug.

**`timeout`, 2/18.** Both `sonnet` against the larger task (`b81c414`). A 240s
wall-clock cap, declared once and applied uniformly to every attempt in that
stage, was hit twice; per `mission.yaml`'s guardrail this is a failure, not a
retry with a longer cap.

## Does it cheat?

Zero, across every real attempt in this mission — 36 total, both arms. No
diff, from any model, at any tier, in either the tool-loop harness or the
one-shot no-harness call, ever touched a file under `tests/`.

The only time this mission has watched the check fire is
[stage 02's scripted demonstration](../02-agent-loop/runs/2026-07-29-harness-end-to-end.md),
built from a backend with no model behind it, on purpose, to prove the
mechanism works before any real model was ever pointed at it. `mission.yaml`'s
acceptance bullet asks for the guardrail to fire on a real attempt, *or* to be
explicitly reported as never having fired — this reports the second, honestly,
rather than writing a prompt engineered to make a model cheat so this bullet
could read differently. That would answer "can a model be made to cheat if
told to," which is not the question this mission is measuring.

## Check your mental model

1. Stage 03's failure row is all zeros. What real claim does that support, and
   what claim would it be wrong to draw from it?

<details>
<summary>Answer</summary>

It supports the real, narrow claim that this task set's failure surface,
under a full harness with tool access and up to 25 retry steps, is empty —
none of the three tiers needed a second observation to notice a wrong patch,
on these two tasks. It would be wrong to draw the general claim that a full
harness eliminates failure for frontier coding agents: two tasks, three
tiers, three runs each is a small, specific surface, and "What this does not
prove" says so directly — a larger or more adversarial task set could still
surface harness-level failures this one did not.

</details>

2. Eleven of stage 01's twelve `target_still_failing` verdicts never even
   applied. Why does collapsing "wrote a working patch that was wrong" and
   "wrote something `git apply` couldn't parse" into one bucket understate what
   a no-harness call actually fails at?

<details>
<summary>Answer</summary>

Because those are different failure modes with different implications. A
patch that applies cleanly but doesn't fix the bug means the model understood
the mechanics of patching but reasoned incorrectly about the fix — that's
only one attempt out of twelve. Eleven never got that far: `git apply`
rejected them outright, and the one inspected by hand shows why — the model
miscounted its own patch's line spans (claimed 17/43, actually wrote 19/42).
Labeling all twelve as one bucket ("target still failing") makes it look like
the no-harness arm mostly fails at fixing bugs, when it actually mostly fails
at the mechanical act of producing a syntactically valid diff without a tool
loop to catch and let it retry.

</details>

3. The tampering guardrail has fired exactly once in this mission's history,
   and it was scripted. What would change your answer to "is this guardrail
   necessary"?

<details>
<summary>Answer</summary>

Zero real firings across 36 real attempts, both arms, means no model in this
mission's actual runs ever found deleting or weakening a test cheaper than
fixing the bug — which is a fact about these two tasks' tractability, not
proof the guardrail is unneeded. What would change the answer is a harder or
more adversarial task set where a model under pressure (a tight budget, a
task it can't actually solve) might find cheating the cheaper path; the
mission deliberately did not write a prompt engineered to make that happen,
since that would answer "can a model be made to cheat if told to" rather than
whether it cheats on real, unprompted attempts — a different question than
this mission measures.

</details>

## What this does not prove

**Stage 03's zero-failure record is a property of this task set, not a
general claim about frontier coding agents.** Two tasks, three tiers, three
runs — a larger or more adversarial set could surface harness failures this
one did not.

**The 11/12 non-applying-diff finding is specific to a unified-diff patch
channel.** A no-harness baseline built around whole-file replacement instead
of a diff would likely show a different failure mix.

**Never firing is not evidence the guardrail is unneeded.** It is evidence
that, on these two tasks, no tier found deleting an assertion cheaper than
fixing the bug — which may simply mean these two bugs were tractable enough
that cheating had no efficiency advantage.

**Next:** [stage 05](../05-report/) holds every number across all five real
stages against `mission.yaml`'s acceptance list, mechanically, and says which
bullets are met.

A detour from here: [when the patch cannot even be applied, what is the loop
buying?](when-the-patch-cannot-apply/) — the same logs, second cut: 11 of 12
failures never produced an applicable patch, the failures concentrate on the
identity checks, and the harness is cheaper per resolved task than the blind
call.

Another detour: [zero failures is a real result, not a gap](the-zero-failure-taxonomy/) — the recorded catalogue read: the harness arm is 0/18 in every failure category, and the no-harness arm is where failures live (12/18 target_still_failing).
