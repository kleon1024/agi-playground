---
label: Paired bootstrap significance
---

# Run record: paired bootstrap over two item-set sizes

**Command:**

```bash
cd platform/evaluation-observability/02-statistical-significance/core
python3 bootstrap_significance.py --seed 0 --out ../runs/bootstrap-run.json
```

**Hardware:** CPU only (pure Python, stdlib `random`), local machine, wall-clock
well under 1 second for 2,000 resamples at each of two item-set sizes. \$0 cost.

**Construction:** both item sets are drawn from the same generator
(`generate_paired_outcomes`) with the identical `true_effect = 0.06` — Model A
carries a genuine +0.06 edge in per-item pass probability over Model B, added
symmetrically around each item's own difficulty, then a single Bernoulli draw
per item produces the observed pass/fail. The only thing that differs between
the two conditions below is `n_items`: 300 vs 25, both seeded independently
from the same `--seed 0` run.

**Results:**

| | n=300 | n=25 |
|---|---|---|
| score A | 0.6933 | 0.6400 |
| score B | 0.5600 | 0.4400 |
| observed gap (A − B) | 0.1333 | 0.2000 |
| 95% bootstrap CI (2,000 resamples) | (0.0600, 0.2067) | (−0.0400, 0.4400) |
| excludes zero | **True** | **False** |

The n=25 condition shows a *larger* observed gap (0.2000 vs 0.1333) than the
n=300 condition — the same underlying true effect, sampled with more noise at
low N can easily look bigger by chance — but its interval is wide enough to
include zero, while the n=300 condition's narrower interval sits entirely
above zero. Point estimate size and statistical confidence are not the same
axis; this run is the concrete case where they disagree.

Full JSON: [`bootstrap-run.json`](bootstrap-run.json).
