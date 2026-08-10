# Run — blend bias, the measured cost of the random start

**Date:** 2026-08-08
**Command:** `uv run python core/blend_variance.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 1.4s.
**Cost:** \$0 (local lane).

## Purpose

Stage 38's audit measured the naive blend crediting team A with 59.2
percent of clicked sessions against equal teams, and the random start
landing at 49.7/50.3. This run quantifies the trade the fix carries
instead of asserting it: how the credited share spreads across repeated
experiments, where the interval centers at scale, and how many more
sessions the balanced design needs for the same confidence-interval
width.

## Output

```
blend bias, measured: what does the random start cost?
  position click probs: 0.30 0.20 0.14 0.10 0.07 0.05
  teams equal; proposals disjoint; 2000 experiments x 3000 sessions, seed per experiment

naive blend (team A starts every session): mean 59.3% across 2000 experiments of 3000 sessions each
  spread: SD 0.99%, 95% of experiments land in [57.4%, 61.3%]
balanced blend (random start per session): mean 50.0% across 2000 experiments of 3000 sessions each
  spread: SD 1.00%, 95% of experiments land in [48.1%, 52.0%]

per-session outcome variance, exact from the model:
  naive 0.2413 vs balanced 0.2500; the random
  start raises it by 3.6%, so the same CI
  width needs 3.6% more sessions (empirical SDs above: 0.99% vs 1.00%)

bias at scale (200000 sessions, seed 11):
  naive: credited A share 59.3% (95% CI +/-0.23%)
  balanced: credited A share 50.0% (95% CI +/-0.24%)
  the naive interval excludes the true 50/50 by 78 standard errors — more traffic only pins
  the wrong center down more tightly

verdict: the random start removes a fixed bias the naive
blend cannot see — 9.3% of credited share
that more traffic pins down more tightly. The price is
small: 3.6% more sessions for the same
interval width. Bias is dominant: a tight interval around
the wrong center is a confident wrong answer (Chapelle
et al., 2012, TOIS; Joachims et al., 2005, SIGIR; Radlinski
& Craswell, 2010, SIGIR).
```

## Notes

- Across 2,000 experiments of 3,000 sessions each, the naive blend's
  credited-share mean is 59.3 percent and the balanced design's is
  50.0 percent. The spread is nearly identical — SD 0.99 percent versus
  1.00 percent — so the naive design does not fail through variance; it
  fails through a center that is wrong.
- The per-session outcome variance is exact from the model: naive
  0.2413, balanced 0.2500 (the start flip adds 0.0087 of variance). The
  same confidence-interval width therefore needs 3.6 percent more
  sessions in the balanced design, and the empirical SDs match that
  prediction.
- At 200,000 sessions the naive interval is +/-0.23 percent around
  59.3 percent — the true 50/50 is 78 standard errors away, and more
  traffic only pins the wrong center down more tightly. The random
  start is nearly free variance-wise; the failure it removes is a fixed
  bias no sample size can shrink.
