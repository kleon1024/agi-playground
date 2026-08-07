# Run — the rank-error revenue audit

**Date:** 2026-08-07
**Command:** `uv run python core/ecpm_rank_error.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

The stage run ranks three ads by estimated eCPM and shows the low bidder
wins. The audit asks the case-finding question: what does the platform
actually earn when the ranking runs on estimates? It perturbs each ad's
pCTR by a multiplier, re-ranks by estimated eCPM (ties broken by bid),
and measures realized revenue against the optimal 150.00 per impression.
Errors that keep the winner on top cost nothing; errors that flip the
winner cost 30-50 per impression. This is the revenue consequence of the
"knife-edge" detour, and the column an online check must reproduce.

## Output

```
rank-error audit: estimates = true pCTR; optimal revenue per
impression = 150.00 (Ad B). Perturb one ad's pCTR at a
time; re-rank by estimated eCPM, ties broken by bid; realized
revenue uses the winner's true eCPM.

  perturbed  error  winner  realized   loss
       Ad A   0.50    Ad B    150.00   0.00
       Ad A   1.25    Ad B    150.00   0.00
       Ad A   1.50    Ad A    100.00  50.00
       Ad A   2.00    Ad A    100.00  50.00
       Ad B   0.50    Ad C    120.00  30.00
       Ad B   1.25    Ad B    150.00   0.00
       Ad B   1.50    Ad B    150.00   0.00
       Ad B   2.00    Ad B    150.00   0.00
       Ad C   0.50    Ad B    150.00   0.00
       Ad C   1.25    Ad C    120.00  30.00
       Ad C   1.50    Ad C    120.00  30.00
       Ad C   2.00    Ad C    120.00  30.00

grid: 18 perturbations; winner flips in 7 (38.9%)
mean realized revenue 136.11 vs optimal 150.00 (mean loss 13.89)
```

## Notes

- Half-measure pCTR errors that leave Ad B on top cost nothing (0.00
  loss); errors large enough to flip the winner cost 30-50 per
  impression. The ranking is only as good as the estimate.
- A mean loss of 13.89 per impression over the perturbation grid means a
  ranking with unchecked estimates runs at roughly 91 percent of optimal
  revenue when a third of the grid flips the winner.
- Ad B's own underestimate (mult 0.5) costs 30 by handing the slot to Ad
  C; Ad A's overestimate (mult 1.5+) costs 50 by handing the slot to Ad
  A. The realized column is the online check that catches a flip before
  the revenue report does.
