# How this mission's agents actually fail

`mission.yaml`'s guardrail: "failures catalogued by category, not merely
counted." This is not a new experiment -- it reads every real attempt this
mission has produced so far (stage 03's 18 full-harness attempts, stage 01's
18 no-harness attempts) and sorts them into the categories `scoring.score`
already assigns, plus one stage 01 adds.

## Command

```bash
cd 04-agentic-platform/04-how-it-fails/core
uv run python taxonomy.py
```

Raw output: [`2026-08-01-failure-taxonomy.txt`](2026-08-01-failure-taxonomy.txt).
Inputs read: [`../../03-cheap-or-expensive/runs/2026-07-29-results.jsonl`](../../03-cheap-or-expensive/runs/2026-07-29-results.jsonl)
and [`../../01-no-harness/runs/no-harness-results.jsonl`](../../01-no-harness/runs/no-harness-results.jsonl).

## The taxonomy

| Category | Harness (stage 03, 18 attempts) | No-harness (stage 01, 18 attempts) |
|---|---|---|
| resolved | 18/18 | 4/18 |
| target_still_failing | 0/18 | 12/18 |
| regressed | 0/18 | 0/18 |
| tampered | 0/18 | 0/18 |
| no_tests_ran | 0/18 | 0/18 |
| timeout | 0/18 | 2/18 |

Stage 03's full-harness attempts produced **zero real failures of any kind**
across all three model tiers -- every category besides `resolved` is 0/18.
That is a genuine result, not a gap in this taxonomy: with tool access, test
feedback, and up to 25 steps to retry, none of the three tiers needed a second
observation to notice a wrong patch. The harness's failure surface, at this
scale, is empty.

Stage 01's no-harness attempts have all the failures this mission set out to
observe:

**`target_still_failing`, 12/18, further split.** Of these twelve, **eleven**
produced a diff `git apply` rejected outright -- not a wrong fix, a
non-applying one. Inspecting one by hand (`haiku`, task `354c352`, run 2): the
model's hunk header claimed 17 old-side lines and 43 new-side lines; the diff
body actually contained 19 old-side (15 context + 4 removed) and 42 new-side
(15 context + 27 added) lines. The model miscounted its own diff, and `git
apply` correctly refused a hunk whose header doesn't match its body -- this is
the harness behaving correctly, not a bug in it. Only **one** of the twelve
applied a syntactically valid patch that simply did not fix the bug (`haiku`,
`b81c414`, run 1).

**`timeout`, 2/18.** Both on `sonnet` against `b81c414` (the larger,
multi-hundred-line `engine.py` context). The declared 240s wall-clock cap was
applied uniformly to every attempt in stage 01, including these two; per
`mission.yaml`'s guardrail, a task that hits the cap is scored as a failure,
not retried with a longer one.

**`tampered`, 0/18, in both arms.** No real model attempt in this mission --
36 total across stage 03 and stage 01 -- ever produced a diff touching a file
under `tests/`. The only recorded firing of the test-tampering guardrail is
the scripted demonstration in
[stage 02](../../02-agent-loop/runs/2026-07-29-harness-end-to-end.md), built
with a backend that has no model behind it, specifically to prove the check
fires correctly before any real model was ever pointed at it. Per
`mission.yaml`'s acceptance bullet ("demonstrated to fire on at least one real
attempt, or is explicitly reported as never having fired"), this is reported
as **never fired on a real attempt** -- not claimed as demonstrated, and not
manufactured by writing a prompt that asks a model to cheat, which would
answer a different question than the one this mission is measuring.

## What this does not establish

**Stage 03's zero-failure record is a property of this task set, not a claim
about frontier coding agents in general.** Two tasks, three tiers, three runs
each -- a much larger or more adversarial task set could easily surface
harness-level failures this one did not.

**The 11/12 "diff did not apply" finding is specific to this harness's diff
channel.** A no-harness baseline built around a different patch-delivery
format (e.g., whole-file replacement instead of a unified diff) would likely
show a different failure mix; this number characterizes one specific way of
asking a model for a blind patch, not blind patching in general.

**Never having fired is not evidence the guardrail is unnecessary.** It is
evidence that, on this task set, no model tier found deleting an assertion
easier than fixing the underlying bug -- which may simply mean these two bugs
were tractable enough that cheating had no efficiency advantage.
