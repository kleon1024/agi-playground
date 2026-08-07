# Run — when the click is a query, executed on the session model

**Date:** 2026-08-07
**Command:** `uv run python core/query_sessions.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 24 measures search. This run reads a two-query session where the
first query fails and the reformulation succeeds.

## Output

```
session, read:
  'heaphones' -> no click
  'headphones' -> click on d2

reading: judged alone, the first query is a failure. Judged as
a session, it is the intent that the second query satisfied. The
reformulation is the correction signal — session metrics catch
the recovery that per-query metrics call a miss.
```

## Notes

- Judged per query, 'heaphones' is a zero-click failure; judged as a
  session, it is the intent the corrected query satisfied.
- The reformulation is itself a signal: session metrics catch the
  recovery that per-query metrics call a miss.
