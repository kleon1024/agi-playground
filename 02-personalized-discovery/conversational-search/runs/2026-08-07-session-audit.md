# Run — resolution-stability audit, executed on the head/tail session log

**Date:** 2026-08-07
**Command:** `uv run python core/session_context.py --emit-log /tmp/session-envelope.json` then `uv run python prod/conversation_audit.py /tmp/session-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; core script stdlib only, audit script pandas.
**Wall-clock:** 0.5s total.
**Cost:** \$0 (local lane).

## Purpose

Stage 36 resolves follow-ups through session context. This run
stratifies resolution by session length on a 10-session log and finds
where the session stops resolving — the case-finding that shows when
truncation loses the first-turn grounding.

## Output

```
resolution-stability audit over the 10-session log:
  aggregate resolution: 0.680

  stratum  sessions  mean turns  resolution
  head     5         3.2         0.980
  tail     5         17.8        0.380

verdict: RESOLUTION LOST IN LONG SESSIONS -- the
aggregate resolution 0.680 is a
short-session artifact: head resolves at 0.980 while tail resolution is
0.380. Truncation drops the oldest turns first, and
the first-turn topic is exactly the grounding the follow-up
needs. Pin the first-turn grounding (or compress the middle
turns) so the referent survives the window.
```

## Notes

- Aggregate resolution of 0.680 is a short-session artifact: sessions of
  2-4 turns resolve at 0.980, sessions of 12-24 turns at 0.380.
- Truncation drops the oldest turns first, and the first-turn topic is
  the grounding a follow-up that says "back to the first pair" needs.
- The decision that follows: pin the first-turn grounding or compress
  the middle turns so the referent survives the window. This matches
  the "lost in the middle" finding that long-context models use the
  beginning and end of the input far better than the middle (Liu et
  al., TACL 2024).
