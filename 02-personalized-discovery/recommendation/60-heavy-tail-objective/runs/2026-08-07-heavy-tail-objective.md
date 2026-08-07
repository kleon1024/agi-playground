# Run: 60 — heavy-tail objective

- **Command:** `uv run python core/heavy_tail.py` (from
  `02-personalized-discovery/recommendation/60-heavy-tail-objective/`)
- **Config:** GMV regression variants over a synthetic order distribution:
  raw MSE, log(1+GMV), and a decomposed order-probability plus conditional
  amount. Deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 3.85s
- **Cost:** \$0
- **Metrics:**
  - raw MSE: relative error 1.409, whale rows own 21.2% of the gradient
  - log(1+GMV): relative error 1.045, whale gradient share 5.2%
  - decomposed: relative error 1.290, gradient share not applicable

The full printed read, reproduced verbatim on 2026-08-07:

```text
heavy-tail objective, read (gmv regression variants):
  method           rel err  whale grad share
  raw mse            1.409             21.2%
  log(1+gmv)         1.045              5.2%
  decomposed         1.290                 -

reading: raw MSE fits the whale rows, whose residual owns a fifth
of the gradient; the log transform cuts that to a twentieth. the
decomposition lands between the two on pure error but splits the
problem into a binary order probability and a conditional amount
regression, so each piece is interpretable and re-tunable on its
own — its payoff is structure, not the headline number.
```
