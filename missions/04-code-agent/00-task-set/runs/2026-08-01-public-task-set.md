# Mining the public task set from more-itertools' history

Construction of the companion task set `mission.yaml` calls for and stage 00's
first build never produced: the same admission rule applied to a public
repository instead of this one. The question is the same as the private run —
how many candidates survive fail-at-base/pass-at-gold, not how many can be
found — and the answer, 2 of 6, from a repository whose default-branch history
runs to 2423 commits, is the finding.

## Source repository

[more-itertools](https://github.com/more-itertools/more-itertools) (MIT).
Small, pure Python, no runtime dependencies, pytest test suite — chosen so a
materialized task needs nothing beyond pytest itself to run, and so its
history is plausibly inside the training data of models tested here, which is
the entire point of a public set: it is the contamination-*prone* counterpart
to the private set, not another contamination control.

Not vendored. `00-task-set/core/mine_public.py` clones it on demand into
`00-task-set/data/cache/more-itertools` (gitignored, matching the
`**/data/cache/` convention mission 05 and mission 07 established for fetched
datasets) and pins to one commit so re-mining does not chase a moving
upstream default branch.

## Command

```bash
cd missions/04-code-agent/00-task-set/core
uv run python mine_public.py candidates
uv run python mine_public.py mine            # -> tasks/public-candidates.jsonl
uv run python mine_public.py verify --write  # -> tasks/public.jsonl
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 15.6.1, arm64 |
| Python | 3.11.14 (uv-managed) |
| git | present via `uv`'s environment |
| Source repo pin | `9ddc55c57390707d97d96302eea1992919c8d930` (more-itertools default branch at clone time) |
| Wall-clock, full verify of 6 candidates (warm cache) | 4:45 total (`user` 237s, `sys` 31s) |

Each candidate runs the full `tests/test_more.py` file twice (base and gold),
under `uv run --no-project --with=pytest pytest -q ...` — an isolated,
ephemeral environment per invocation rather than a shared project venv, which
is most of the wall-clock here, not the tests themselves (each pytest
invocation completes in 1.5-4s once running).

## Yield

| Stage | Count |
|---|---|
| Commits in history (`--all`) | 2423 |
| Subject begins lowercase `fix` (this repository's own convention, applied unmodified — a narrowing, not a relaxation) | 6 |
| **Verified: fails at base, passes with gold** | **2** |

The two that verified:

| Task | Target test | Gold patch |
|---|---|---|
| `public-f51a53b` | `tests/test_more.py` (`InterleaveEvenlyTests::test_no_iterables`) | `more_itertools/more.py` |
| `public-cca3294` | `tests/test_more.py` (`LastTests::test_reversed_is_none`) | `more_itertools/more.py` |

`public-f51a53b` is an empty-input bug in `interleave_evenly`: an unguarded
`lengths_desc[0]` raises `IndexError` when no iterables are given at all.
`public-cca3294` is a `last()` bug that assumes any object exposing
`__reversed__` returns something usable; when it returns `None` instead, the
fallback path is never reached and `last()` raises the wrong way.

## What the verifier rejected, and why

Four of six candidates were rejected, three of them for the same reason as
half of the private set's candidates: **the target tests already pass at the
base state** (`d71c4ad`, `0de4155`, `4a8b7ee`) — the fix commit's test additions
exercise behavior the parent commit's source already handled correctly, or the
"fix" is non-functional (`4a8b7ee`, a flake8/black formatting pass with no
behavior change at all). The admission rule catches both the same way: a test
that cannot fail cannot prove anything was broken.

The fourth, `fb89af0` ("fixed repeat_each() to accept infinite iterators as
input"), rejected differently: the base-state run exited **137** (killed, not
failed) rather than 0 or 1. `repeat_each`'s pre-fix implementation appears to
consume an infinite iterator without bound when the new test's assertion
touches it, hanging until the process was killed. This is not a task the
admission rule can score — a hang is not a recorded test failure, `f(base)`
never resolves to `FAIL` — so it is skipped rather than forced through, the
same discipline `mine_history.py` applies to `PYTEST_NOTHING_COLLECTED`: a
result other than a clean pass or fail disqualifies the candidate instead of
being coerced into one.

## A real difference from the private miner, caught before it silently broke scoring

The test command initially built was
`["uv", "run", "--no-project", "--with", "pytest", "pytest", "-q", ...]` —
`--with` and its value `pytest` as two separate list elements. This breaks
`02-agent-loop/core/scoring.py`'s `instrument()`, which finds *the first* list
element equal to the literal string `"pytest"` and splices JUnit-XML flags in
immediately after it, to retarget a task's command at the whole suite or add
`--junit-xml`. With two tokens, that first match is the `--with` value, not
the actual pytest subcommand, and every spliced flag lands as an argument to
`uv run` instead of to `pytest` — caught when a smoke-test invocation of
`run_task.py` against `public-f51a53b` failed with `uv`: `unexpected argument
'--tb' found`. The fix is `--with=pytest` as a single token, which has no
element that reads as the literal string `"pytest"` except the subcommand
itself. Confirmed by re-running both scripted demo backends
(`run_task.py --demo idle` and `--demo tamper`) against a public task after the
fix: `idle` correctly resolves nothing (`target_still_failing`), and `tamper`
correctly trips the test-tampering guardrail (`GUARDRAIL FIRED`).

## Wiring into the harness

`02-agent-loop/core/run_task.py` and `claude_arm.py` both hardcoded the
private-set miner module. Both now dispatch on the task's own `"source"`
field (`_miner_for()` in `run_task.py`) to the matching miner — `mine_history`
for `private-*`, `mine_public` for `public-*` — so everything past
materialization (the scorer, the agent loop, cost accounting) is unmodified
and reads either task set identically, per the mission's own "same loop,
different job" reuse convention.

## A real haiku run against the new set

Three independent repeats per task, `claude_arm.py --model haiku --repeats 3`,
headless Claude Code, same guardrails and permission policy as every other
real attempt this mission has recorded:

| Task | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `public-f51a53b` | resolved, 12 turns, 89.8s, $0.1046 | resolved, 14 turns, 102.1s, $0.1861 | resolved, 9 turns, 79.6s, $0.0842 |
| `public-cca3294` | resolved, 7 turns, 100.9s, $0.1051 | resolved, 11 turns, 70.6s, $0.0916 | resolved, 6 turns, 59.7s, $0.0691 |

6/6 resolved, 0 tampered, 0 regressions. `$0.6407` total across all six
attempts (list-price equivalent, per `claude -p`'s own `total_cost_usd`, same
caveat stage 03 and stage 01 already state). Every patch touched only
`more_itertools/more.py`; the guardrail did not fire on a real attempt here,
extending the "never fired on a real model attempt" finding from
[stage 04](../../04-how-it-fails/) across a second, previously unseen
repository — 42 real attempts total across this mission now, none tampered.

Cumulative mission hosted-API spend: **$14.9045** of the **$30** ceiling
([stage 01](../../01-no-harness/runs/2026-08-01-no-harness-baseline.md) had
already spent $14.2638; this run added $0.6407).

## What this run does not establish

Resolve rate on this set is not comparable to the private set's — different
repository, different bug shapes, and a small N=2 each, per `mission.yaml`'s
guardrail that the two are reported separately and never pooled. A single
model tier (haiku) resolving 6/6 here says only that haiku can fix these two
specific, narrowly-scoped bugs in a repository it may have memorized; it does
not establish anything about resolve rate on unseen public bugs, nor does it
run sonnet or opus against this set, which stage 03 did for the private set.
Whether more-itertools' history is *actually* inside haiku's training data was
not tested directly (e.g. by asking the model to recite the fix); "public and
plausibly memorized" is a property of the repository's visibility, not a
verified fact about any specific model's training set.

The mining rule selects the same narrow way it does for the private set: only
fix commits whose author wrote a test in the same commit, and only where that
commit's subject happens to start with lowercase `fix` rather than this
repository's more common `Fix`. Both are severe narrowings a larger public
set would need to relax, deliberately left as-is here to keep the same rule
applied identically to both sets.
