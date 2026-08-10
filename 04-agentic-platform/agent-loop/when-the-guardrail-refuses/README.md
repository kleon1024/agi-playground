---
status: verified
level: applied
base: none
label: When the guardrail refuses
verified: 2026-08-06
---

# When does the test-file guardrail refuse a patch?

**Question:** [stage 02](../) refuses any patch that touches a test file,
because a tampered patch's remaining evidence is worthless. Where exactly
is that boundary — and does it catch a model that *creates* a new test
file to escape it?

**Before this:** [stage 02's harness and scorer](../), including its
scripted guardrail demo.

## The boundary, demonstrated

The run ([record](runs/2026-08-06-guardrail-demo.md)) builds five miniature
worktrees and runs the guardrail's own path logic:

| scenario | test paths found | refused |
|---|---:|---:|
| agent edited a test file | `tests/test_parser.py` | yes |
| agent created a new test file | `tests/test_noop.py` | yes |
| agent edited a source file | — | no |
| agent created a new source file | — | no |
| agent touched nothing | — | no |

## Two readings

**The boundary is the diff's paths, not the model's intent.** Any test path
in the changed set refuses the patch — whether the model meant to tamper or
not. The scorer does not ask why; it reasons that a patch touching the test
that scores it is evidence the model was measured by can no longer be
trusted, so the attempt is refused outright. That is the structural
guardrail the mission builds in place of a system-prompt line asking the
agent to behave.

**Creating a new test file is caught, closing the escape hatch.** The
guardrail reads `git status --porcelain --untracked-files=all`, which sees
untracked files — so a model that responds to "the test fails" by writing
a new test file that asserts nothing is refused exactly like a tamper. The
stage's docstring names this hole ("a new test file that asserts nothing
would slip past"), and the demo shows the worktree-based check closes it.

## The fix and its trade

The fix is a structural guardrail: any test path in the changed set
refuses the patch, with no attempt to read intent, and the untracked-file
check closes the escape hatch of creating a new test file that asserts
nothing. The trade is that the boundary is deliberately blunt — a
legitimate test edit is refused too, because the scorer cannot
distinguish intent and does not try: once the model can change the test
that scores it, the score stops meaning what it claims. The structural
check replaces the system-prompt line, and its price is that some real
work is refused so that no tampered work is believed.

## Who owns the loop

- **The harness owner** owns the guardrail's path logic and the demo that
  proves it fires — the worktree-based `changed_paths` read is the
  mechanism, and the docstring's named hole is the checklist.
- **The task owner** owns the placement that makes the guardrail work:
  tests are the score's measure, so test files are the protected class,
  and source-only changes must pass.
- **The model team** inherits the refusal: a patch touching tests is
  scored as failure regardless of the model's intent, and that is the
  contract, not a judgment about any particular attempt.

## Evidence boundary

Five synthetic worktrees, the stage's own `changed_paths` and `is_test_path`
unmodified. It demonstrates the decision boundary and the untracked-file
catch; it does not re-run the full scorer or measure how the boundary
behaves on real agent output — the recorded harness run does that.

## Check your mental model

Answer each before opening it.

**1. Why refuse any test-path change rather than scoring it and looking at
the result?**

<details>
<summary>Answer</summary>

Because once the model can change the test that scores it, the score stops
meaning what it claims: a tampered test makes "passed" true by editing the
measurement, not by fixing the bug. Scoring the attempt anyway would let a
tamper count as evidence, and the guardrail's job is to keep the scoreboard
honest before any number is recorded — refuse first, ask never.

</details>

**2. The guardrail sees untracked files. Why does that matter for a "new
test file" escape?**

<details>
<summary>Answer</summary>

Because a model could otherwise respond to a failing test by writing a new
test file that asserts nothing, so the suite "passes" without the target
ever being exercised. `git status --porcelain --untracked-files=all` lists
created-but-uncommitted files, so the new test file is in the changed set
and the patch is refused exactly like an edit to an existing test. The
escape hatch is closed by checking the worktree, not the diff alone.

</details>

## Next

Back to [stage 02's harness](../), or forward to
[stage 03's cost comparison](../../03-cheap-or-expensive/) where the
guardrail-protected scores get priced.
