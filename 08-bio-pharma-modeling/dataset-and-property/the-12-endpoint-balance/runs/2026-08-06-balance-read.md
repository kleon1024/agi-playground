# Run — the 12-endpoint balance table, read from the recorded dataset run

**Date:** 2026-08-06
**Command:** `uv run python core/balance_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the dataset run was the stage's recorded).

## Purpose

Stage 00 computed every Tox21 endpoint's label balance before choosing
SR-MMP. This run reads the table and lays out why the choice was made
from balance.

## Output

```
  NR-AR 4.3%, NR-AR-LBD 3.5%, NR-AhR 11.7%, NR-Aromatase 5.2%,
  NR-ER 12.8%, NR-ER-LBD 5.0%, NR-PPAR-gamma 2.9%, SR-ARE 16.2%,
  SR-ATAD5 3.7%, SR-HSE 5.8%, SR-MMP 15.8%, SR-p53 6.2%
```

## Notes

- SR-MMP (15.8%) is the best-balanced endpoint with a single statable
  mechanism.
- The choice is made from balance and assay semantics before any model
  sees the data — the guardrail against choosing after seeing which
  endpoint flatters a number.
