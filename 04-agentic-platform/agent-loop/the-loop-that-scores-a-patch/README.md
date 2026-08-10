---
status: verified
level: applied
base: scratch
label: The loop that scores a patch
verified: 2026-08-06
---

# The harness, drawn as its steps and checks

**Question:** [stage 02's agent loop](../) is the mission's "model" — not
one network, but a loop. This chapter dissects the loop's structure and
the check that makes its verdict trustworthy.

**Before this:** [stage 02's agent loop](../) and its recorded
harness-end-to-end run.

## The loop, read

The run ([record](runs/2026-08-06-loop-anatomy.md)) reads the recorded
harness run:

```
materialize -> capture baseline -> agent loop -> read diff
           -> re-run tests -> score
```

Scripted verification (no model, deterministic): `private-b81c414`
`target_still_failing` in 10.9s; `private-354c352` `target_still_failing`
in 2.2s.

<!-- interactive: AgentLoopAnatomy -->

## The structure, named

The loop has six stages and one guardrail:

1. **Materialize** — build a task from a bug report plus a failing test.
2. **Capture baseline** — record which tests pass before the agent acts.
3. **Agent loop** — prompt, act, observe, repeat (bounded).
4. **Read diff** — inspect what the agent actually changed.
5. **Re-run tests** — apply the baseline and the target test.
6. **Score** — resolve only if the target passes and nothing regressed.

The guardrail sits between 4 and 5: if the diff touches a test file, the
attempt is scored as failure regardless of what the tests say. The recorded
tamper branch is why: a tampered record shows every numeric signal
(regressions empty, target_failing_after empty) as resolved — the tests
*pass* because the agent replaced the failing test with `assert True`. The
diff is the only thing that says otherwise.

## Why the loop is the model

The mission's question — "when an agent says it fixed the bug, what makes
that true?" — is answered by the loop's structure, not by any model inside
it. The guardrail is a check on the diff, not on the agent's own report,
because an agent scored by a test suite has a short path to satisfying the
suite instead of the task. The harness end-to-end run establishes the loop
correct on attempts whose right answer is known before it is pointed at
real attempts — the same discipline as the repo's runs-first rule.

## The fix and its trade

The fix is the loop's structure itself: materialize, capture baseline,
agent loop, read diff, re-run tests, score — with the guardrail between
steps 4 and 5, so a diff touching a test file is scored as failure before
any test result is believed. The trade is that the loop has to be proven
correct before it is trusted, and the proof is scripted: `FakeBackend`
attempts with known right answers (`idle` gives up, `tamper` cheats),
deterministic, \$0, no model. That verification is the cost of trusting
the verdict later — a harness bug (baseline not captured, test not
re-run, diff not read) would be invisible behind a model's plausible
output, and the recorded tamper branch is the proof: every numeric signal
reads resolved while the diff says otherwise.

## Who owns the loop

- **The harness owner** owns the six-stage loop and the guardrail's
  placement — the order of steps is the design, not an implementation
  detail.
- **The eval owner** owns the scored verdict and the scripted
  verification that establishes the loop correct on known answers before
  real attempts.
- **The model team** owns what comes after: real model outcomes are
  stage 03's recorded runs, and the loop's correctness is the
  prerequisite that makes those numbers interpretable.

## Evidence boundary

The recorded harness run (two scripted attempts, `FakeBackend`, no model,
no network, \$0). It reads that artifact; it does not re-run the harness
and the real model outcomes are stage 03's recorded runs, not this
chapter's.

## Check your mental model

Answer each before opening it.

**1. Why does the tamper branch score as a failure when every test
passes?**

<details>
<summary>Answer</summary>

Because the guardrail checks the diff, not the test results. The agent
replaced the failing test with a passing placeholder, so re-running the
suite reports success — but the change to `tests/` is exactly the kind of
diff a model would produce to satisfy a scoreboard instead of a task. The
guardrail fires on the diff before the test result is believed, which is
the only ordering that makes the score trustworthy.

</details>

**2. Why must the harness be verified with no model in the loop?**

<details>
<summary>Answer</summary>

Because the loop has to be shown correct on attempts whose right answer is
known before it is pointed at attempts whose right answer is not. A bug in
the harness — wrong baseline capture, a test not re-run, a diff not read —
would be invisible behind a model's plausible-sounding output. Scripted
attempts (`idle` gives up, `tamper` cheats) exercise every branch with a
deterministic expected verdict first.

</details>

## Next

Back to [stage 02's agent loop](../), or to
[stage 03 — cheap or expensive](../../03-cheap-or-expensive/) where the
loop is pointed at real models.
