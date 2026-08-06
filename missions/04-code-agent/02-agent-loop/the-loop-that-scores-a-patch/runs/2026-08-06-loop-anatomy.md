# Run — the agent-loop anatomy, read from the recorded harness run

**Date:** 2026-08-06
**Command:** `uv run python core/loop_anatomy.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the harness run was the stage's recorded
2026-07-29 run).

## Purpose

The code-agent's "model" is the loop, not one network. This run reads the
recorded harness-end-to-end run and lays out the loop's steps and its two
scripted branches.

## Output

```
agent-loop anatomy (recorded harness run), read:
  steps: materialize -> capture baseline -> agent loop ->
         read diff -> re-run tests -> score
  scripted attempt private-b81c414: verdict target_still_failing, 10.9s
  scripted attempt private-354c352: verdict target_still_failing, 2.2s
```

## Notes

- The tamper branch is the guardrail's reason to exist: a tampered record
  shows every numeric signal (regressions empty, target_failing_after
  empty) as resolved, and only the diff says otherwise.
- The guardrail is a check on the diff, not on the agent's own report —
  which is the whole point of mission 04's scoring design.
