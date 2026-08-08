# Run — what the loop owns, read from the recorded arms

**Date:** 2026-08-08
**Command:** `uv run python core/harness_anatomy.py`
**Hardware:** Apple M1 Pro (32 GB), macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.07s real.
**Cost:** \$0 (local lane; the inputs were the mission's own recorded model
attempts, and no model was called).

## Purpose

The chapter's question is what the software around the model actually owns.
This run reads the recorded no-harness, full-harness (private), full-harness
(public), and closing-the-loop arms and prints, per arm, the columns a
control-plane audit needs: attempts, delivered, cost per delivered, mean
turns, mean tokens (input + output), and mean wall-clock.

## Output

```
what the loop owns, read from the recorded mission-04 arms:

arm                    n  delivered $/delivered   turns   tokens   wall s
no-harness            18    4/18         1.2859       -    45276     99.6
harness (private)     18   18/18         0.5066    10.5   606755     86.4
harness (public)       6    6/6          0.1068     9.8   409672     83.8
closing-the-loop      12    2/12         1.5256       -    50035     70.9

reading: the loop owns delivery -- 2/12 retries
resolved with feedback but no tools, 2/12 patches applied;
the control-plane columns above are what a harness audit must measure
before any claim about 'the model' is read from a score.
```

## Notes

- The no-harness and closing-the-loop arms record no `turns` column, so that
  cell reads `-`; they are single-call arms by construction.
- The harness arm's mean token count (about 607k per attempt) is the loop
  itself: tool observations and the scored test output are written back into
  the transcript. The blind arm's 45k mean is the same tasks read once.
- Cost per delivered: \$1.2859 (blind) vs \$0.5066 (private harness) vs
  \$0.1068 (public harness, haiku) — the loop is cheaper per delivery and
  delivers more.
