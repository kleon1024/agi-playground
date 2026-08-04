# Run: proxy-only vs true-objective hill-climbing (Goodhart toy)

## Command

```bash
cd platform/evaluation-observability/01-metric-gaming/core
python goodhart.py --steps 2000 --window 200 --seed 0 --out ../runs/goodhart-run.json
```

**Hardware:** local dev box (CPU only, pure Python + stdlib `math`/`random`,
no GPU involved).

**Software:** Python 3.11, no third-party dependencies.

**Wall-clock:** under 0.1s (4,000 objective evaluations across two 2,000-step
hill-climbs).

**Cost:** \$0.

## Setup

Two functions share one genuine-quality term (`10*sqrt(i)`, diminishing
returns, capped at `i=50`) and differ only in how they treat a second knob
`p` that is cheap to move and has no ceiling in this run:

```
true_objective(i, p) = 10*sqrt(i) - 0.6*p
proxy_metric(i, p)   = 10*sqrt(i) + 0.4*p
```

Two greedy hill-climbers start at `(i=0, p=0)` and run 2,000 steps each,
proposing a random perturbation to one randomly chosen dimension per step
and accepting only if the objective they can see improves:

- `proxy_hillclimb` — accepts only if `proxy_metric` improves. Never
  evaluates `true_objective` to decide a move (it is only logged alongside,
  for this record).
- `true_hillclimb` — accepts only if `true_objective` improves. Control.

## Result

Full per-window data in `goodhart-run.json`.

**Proxy-only optimizer, windowed correlation (200-step windows) between
`proxy_metric` and `true_objective` along its own trajectory:**

| window (steps) | correlation | mean i | mean p |
|---|---:|---:|---:|
| 0-199 | 0.807 | 23.22 | 42.80 |
| 200-399 | -0.998 | 49.95 | 105.54 |
| 400-599 | -1.000 | 50.00 | 163.71 |
| 600-799 | -1.000 | 50.00 | 236.25 |
| 800-999 | -1.000 | 50.00 | 317.83 |
| 1000-1199 | -1.000 | 50.00 | 396.78 |
| 1200-1399 | -1.000 | 50.00 | 469.11 |
| 1400-1599 | -1.000 | 50.00 | 554.71 |
| 1600-1799 | -1.000 | 50.00 | 633.78 |
| 1800-1999 | -1.000 | 50.00 | 715.68 |

**Final states, step 1999:**

- `proxy_hillclimb`: `i=50.0, p=752.86` &rarr; `proxy=371.85` (up from 0),
  `true=-381.00` (down from 0).
- `true_hillclimb` (control): `i=50.0, p=0.0` &rarr; `proxy=70.71`,
  `true=70.71` — the true-objective optimum given the `i` cap, and it never
  touches `p`.

## Notes

An earlier version of this script capped `p` at 300. The proxy-only run
saturated both `i` and `p` against their caps well before step 2000, at
which point both `proxy_metric` and `true_objective` become literal
constants — zero true variance — and the windowed-correlation computation on
constant series returned spurious values near +-1 from floating-point noise
rather than a meaningful correlation. Raising the `p` cap to 1e6 (never
reached in 2000 steps at this step size) removed the artifact; every
correlation value in the table above is computed over a window with genuine
variance in both series.
