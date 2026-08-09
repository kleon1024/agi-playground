# Run — the conversational surface, read from the recorded search runs

**Date:** 2026-08-08
**Command:** `uv run python core/conversational_surface.py`
**Hardware:** Apple M1 Pro (32 GB), macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.10s real.
**Cost:** \$0 (local lane; the inputs were the mission's own recorded runs,
and no model was called).

## Purpose

The chapter's question is what changes when the result page becomes a
conversation. This run reads the two recorded search reads — the AOL
query-log session-recovery read (stage 24's detour) and the
conversational-search resolution audit (stage 36) — and prints the
per-query-versus-session verdict, the recovery split by stratum, and the
correction channel, which is the evidence the chapter's argument stands on.

## Output

```
the conversational surface, read from the recorded search runs:

per-query verdict counts 46.6% of queries as failures;
the session read reclassifies 19.9% of those as recovered

stratum  recovered   reformulated   abandoned
head          4.3           5.2       90.5
body         13.0          12.9       74.1
tail         27.5          21.2       51.3

correction channel: 23.2% near-edit typo fix, 76.8% semantic reformulation

session resolution: aggregate 0.680 is a short-session artifact --
head 0.980 vs tail 0.380 on the recorded audit

reading: the unit of measurement is the session, not the query.
Recovery concentrates in the tail, and the tail is exactly where
resolution is hardest -- the conversational surface's addressable
gap is the reformulated-but-unresolved share, not the click rate.
```

## Notes

- Every number above is re-read from committed runs, not re-measured: the
  per-query failure share (46.6%), the recovered share (19.9%), the stratum
  table, and the correction channel come from
  `search/24-search-measurement/when-the-click-is-a-query/runs/2026-08-08-query-log-session-recovery.md`;
  the resolution split (aggregate 0.680, head 0.980, tail 0.380) comes from
  `search/36-conversational-search/runs/2026-08-07-session-audit.md`.
- The two reads were made for different purposes; this chapter joins them
  deliberately: the session verdict is what a conversational surface
  optimizes, and the stratum split is where the surface's addressable gap
  sits (the reformulated-but-unresolved tail).
