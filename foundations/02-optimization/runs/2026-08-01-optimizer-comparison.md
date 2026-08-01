# Run — optimizer comparison on an ill-conditioned quadratic bowl

**Date:** 2026-08-01
**Hardware:** any CPU (Apple M-series laptop used here) — no GPU, no framework
dependency beyond numpy for the optimizers themselves.
**Software:** Python 3.11/3.12, numpy. Plotting uses matplotlib, run outside
this repository's `uv` environment (not a project dependency; see note below).
**Cost:** \$0. Wall-clock for all three optimizers combined: 1.7-1.9
milliseconds.

## Command

```bash
python core/optimizers.py
python core/plot_trajectories.py
```

No arguments — configuration is constants at the top of `core/optimizers.py`
(bowl curvatures `A=100, B=1`, start point `(1, 1)`, loss tolerance `1e-6`,
each optimizer's own learning rate and, for momentum, `mu=0.9`).

## Output

```
sgd        343 steps                    final_loss=9.636e-07  flips=341
momentum   138 steps                    final_loss=9.491e-07  flips=47
adam       82 steps                     final_loss=2.167e-07  flips=4

wall_clock_s=0.0019
```

Full numbers, including final `(x, y)` for each optimizer, are in
`optimizer-comparison.json`. Chart: [`trajectories.png`](trajectories.png).

## Notes

- **Deterministic, not seed-dependent.** The loss surface, start point, and
  every optimizer update are closed-form arithmetic — no randomness anywhere
  in `core/optimizers.py`, so re-running reproduces these exact numbers
  (confirmed: ran twice, byte-identical `optimizer-comparison.json`).
- **matplotlib is not a dependency of this repository's `uv` project**
  (checked `pyproject.toml`: only `pytest`/`ruff` are in the default `dev`
  group, plus opt-in `torch`/`chem`/`game`/`vision` groups). `core/optimizers.py`
  itself runs fine under `uv run` (numpy is already a transitive dependency).
  `core/plot_trajectories.py` was run with a system Python that already had
  matplotlib installed, exactly as this repository's other plotted charts
  (e.g. `foundations/01-first-training-loop/runs/loss.png`) were produced
  outside the CPU-only test environment. No new dependency was added to
  `pyproject.toml` for this chapter.
- **Sign-flip counts are the direct oscillation measure** referenced in the
  README: counting how many times the steep-axis coordinate changes sign
  between consecutive steps. SGD flips on all but two of its 343 steps;
  momentum cuts that by 7x; Adam by 85x.
