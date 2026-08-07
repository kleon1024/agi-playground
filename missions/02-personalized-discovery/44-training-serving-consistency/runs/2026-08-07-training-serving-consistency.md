# Run — training-serving consistency, executed on the skew read

**Date:** 2026-08-07
**Command:** `uv run python core/skew.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 44 introduces training-serving consistency. This run ranks the same
items by the logged CTR and by the live CTR, and reads the disagreement.

## Output

```
training-serving skew, read:
  offline order (logged CTR):
    P1001: logged ctr 0.042
    P1002: logged ctr 0.023
    P1003: logged ctr 0.018
  live truth (CTR at the price actually served):
    P1003: live ctr 0.030
    P1001: live ctr 0.026
    P1002: live ctr 0.026

reading: offline says P1001 wins; live reality
says P1003 wins. The logged price is the model's
world, and that world ended. Serving-time feature logging and
re-validation on live features are the fix, not a better model.
```

## Notes

- Offline says P1001 wins; live reality says P1003 wins. The logged price is the model's world, and that world ended.
- Serving-time feature logging and re-validation on live features are the fix, not a better model.
