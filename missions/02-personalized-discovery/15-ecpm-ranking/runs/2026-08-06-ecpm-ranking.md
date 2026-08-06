# Run — eCPM ranking, executed on the stage's revenue objective

**Date:** 2026-08-06
**Command:** `uv run python core/ecpm_ranking.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

An ad's value is expected revenue — bid times pCTR, scaled to eCPM. This
run executes the ranking and shows the lower bid winning.

## Output

```
  Ad B  bid 0.50  pCTR 0.30  eCPM 150.00
  Ad C  bid 1.00  pCTR 0.12  eCPM 120.00
  Ad A  bid 2.00  pCTR 0.05  eCPM 100.00
```

## Notes

- Ad B has the lowest bid but the highest eCPM — it wins. Ranking by bid
  would show the wrong ad; ranking by expected revenue is what the
  platform actually earns.
