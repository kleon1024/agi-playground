# Run — budget pacing, executed on the stage's delivery simulation

**Date:** 2026-08-06
**Command:** `uv run python core/budget_pacing.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

An advertiser has a daily budget, and the platform must deliver it across
the day. This run simulates naive versus paced delivery under a
front-loaded demand curve.

## Output

```
  hour    naive    paced
    0     36.3      8.3
    1     33.2      8.3
    2     30.2      8.3
    3      0.3      8.3
    4      0.0      8.3
    ...
    8      0.0      7.3
   11      0.0      3.6
  naive exhausts at hour 3 (spent 100 of 100.0)
  paced survives the day: 88.4 spent, 11.6 unused
```

## Notes

- Naive spends as fast as impressions arrive, so a morning spike exhausts
  the budget by hour 3 and the campaign is dark for the rest of the day.
- Pacing caps the per-hour spend so delivery survives the whole day.
