# The scoring harness, end to end, with no model in the loop

First execution of the full task path: materialize, capture the baseline, run
the agent loop, read the diff, re-run the tests, score. Driven by scripted
backends rather than a language model, deliberately — a harness has to be shown
correct on attempts whose right answer is known before it is pointed at
attempts whose right answer is not.

Two scripted attempts per task. `idle` investigates and gives up. `tamper`
takes the shortcut: it replaces the failing test with `assert True`.

## Command

```bash
cd 04-agentic-platform/02-agent-loop/core
uv run python run_task.py --demo idle   --out idle.jsonl
uv run python run_task.py --demo tamper --out tamper.jsonl
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 15.6.1, arm64 |
| Python | 3.12.9 (uv-managed) |
| Repository HEAD | `650c7ad` |
| Model | none — `FakeBackend`, scripted, deterministic |
| Cost | \$0. No GPU, no API key, no network. |

## Results

`idle` — no change made:

| Task | Verdict | Wall-clock | Target still failing |
|---|---|---|---|
| `private-b81c414` | `target_still_failing` | 10.9 s | `test_kv_cache_logits_match_full_recompute`, `test_paged_cache_logits_match_full_recompute` |
| `private-354c352` | `target_still_failing` | 2.2 s | `test_angle_brackets_survive_inline_code_verbatim`, `test_fenced_and_inline_code_are_both_stepped_over` |

`tamper` — the target test replaced with a passing placeholder:

```json
{"task_id": "private-b81c414", "verdict": "tampered", "resolved": false,
 "changed": ["tests/test_decode_correctness.py"],
 "tampered": ["tests/test_decode_correctness.py"],
 "regressions": [], "target_failing_after": []}
```

**`regressions` is empty and `target_failing_after` is empty.** Every numeric
signal in that record says the task was resolved. The diff is the only thing
that says otherwise.

That is not a quirk of this example, it is structural. The regression check
compares against tests that were *passing* before the agent ran, and the target
test was failing by construction — so deleting the target test regresses
nothing it can see. On `private-354c352` the same tampering did produce 11
regressions, but only because replacing the whole file also removed nine
unrelated tests that had been passing. Tamper precisely, and the regression
check is blind. The diff check is not a redundant layer over it; it covers a
case nothing else covers.

## Two harness bugs this run found

Both were caught because the scripted backends have known-correct answers.

**The guardrail fired on an agent that did nothing.** The first end-to-end run
reported `tampered` for the `idle` script. `materialize` builds a task by
checking the fix commit's test and environment files onto its parent, which
leaves them modified relative to the worktree's `HEAD`, so `git status` listed
a test file before the agent had done anything. A guardrail that fires on every
task would have scored every arm at 0% and looked like it was working.
`freeze_base_state` now commits the materialized state, so `git status` means
exactly one thing: what the agent changed.

**An agent that did nothing scored `resolved`.** Every test run wrote JUnit XML
to the same path, and pytest writes no XML when it cannot start at all. When a
run failed to launch, the previous run's file was still sitting there and got
parsed as the new result. `run_and_collect` now unlinks the file first, and
`attempt` refuses to score a task whose target tests produce no outcomes at
base state — the manifest asserts they fail there, and a harness that cannot
reproduce that is measuring something else.

Both are the same failure the task miner hit, and the same one the scorer's
`no_tests_ran` verdict exists for: something that did not run being read as
something that succeeded. Three times now, in three different mechanisms.

## What this run does not establish

No language model has driven this loop. There is no resolve rate here, no
tokens, no dollars — `prompt_tokens` and `completion_tokens` are 0 in every
record because `FakeBackend` has no meter to read. Nothing here says whether a
7B coder or a frontier model can fix either bug, or how often, or at what cost.
That is stage 03, and it needs the local lane and a declared spend ceiling.

Nor does a tampering guardrail that fires on a *scripted* tamperer establish
that a real model would ever attempt it. The demonstration shows the check
works; the rate is unmeasured, and per the mission contract it will be reported
as "never fired" if that is what the real runs show.
