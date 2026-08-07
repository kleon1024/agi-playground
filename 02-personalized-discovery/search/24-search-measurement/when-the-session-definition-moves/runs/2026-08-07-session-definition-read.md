# Run — the session definition that moves

**Date:** 2026-08-07
**Command:** `uv run python core/session_definition.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Show the funnel's dependence on the session definition: the same log,
segmented two ways, reports different health for the same search
experience.

## Output

```
session definition, read (one 6-event log, two segmentations):
  30-min timeout       sessions 2  success 100%  zero-sessions 0%  queries/session 3.0
  topic continuation   sessions 5  success 40%  zero-sessions 60%  queries/session 1.2

reading: the same log yields 2 sessions under a 30-minute
timeout and 5 under topic continuation. The timeout merges
four distinct topics into one session and reports 100%
success; the topic splitter exposes the failed queries as
60% zero-result sessions. Two teams with two definitions
disagree about whether search improved. The funnel is a
statement about the definition, so the definition has to be
owned, documented, and frozen before the numbers mean
anything.
```

## Notes

- The log is six events: a misspelled query and its correction, a
  running-shoes failure and its trail-runners recovery, a later
  headphones search, and a failed gaming-chair search. The timeout
  merges the last four topics into one session; the topic splitter
  keeps them separate.
- Jones and Klinkner, "Beyond the Session Timeout: Automatic
  Hierarchical Segmentation of Search Topics in Query Logs", CIKM
  2008, pages 699-708, is the reference for why a fixed timeout is a
  weak proxy for the real topic boundary.
- The offline-consistency version of the question: is the metric
  stable under the definition, or is the definition what moved? A
  funnel comparison across months is only valid with a frozen,
  documented segmentation.
