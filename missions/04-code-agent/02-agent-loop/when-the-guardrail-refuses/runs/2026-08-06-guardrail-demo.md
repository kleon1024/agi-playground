# Run — the test-file guardrail's decision boundary, on miniature worktrees

**Date:** 2026-08-06
**Command:** `uv run python core/guardrail_demo.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; reuses the stage's `scoring.py`
unmodified.
**Wall-clock:** 0.05s (five git-init'd temp worktrees).
**Cost:** \$0 (local lane).

## Purpose

Stage 02's scorer refuses a patch that touches a test file. This run builds
five miniature worktrees with the scenario's files and runs the guardrail's
own `changed_paths` and `is_test_path`, so the boundary is the code's
decision.

## Output

```
scenario                                 test paths found  refused
agent edited a test file (tamper)        ['tests/test_parser.py']  yes
agent edited a source file (legit)                         []  no
agent created a new test file            ['tests/test_noop.py']   yes
agent created a new source file                           []  no
agent did not touch anything                               []  no
```

## Notes

- Editing a test file is refused; creating a new test file is also refused —
  `changed_paths` reads `git status --porcelain --untracked-files=all`, which
  sees untracked files, closing the "new test file that asserts nothing"
  hole the stage's docstring names.
- Source-only and empty worktrees pass. The guardrail checks the diff's
  paths, not the model's intent: any test path in the changed set refuses
  the patch, because a tampered patch's remaining evidence is worthless.
