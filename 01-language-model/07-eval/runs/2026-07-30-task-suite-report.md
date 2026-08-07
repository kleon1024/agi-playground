# task_suite report — 2026-07-30T08:55:07+00:00

checkpoint   /home/ding/agi-playground/stage03/ckpt/ckpt.pt
context      1024 tokens
loglik tasks 8
  accuracy   0.625  95% CI [0.250, 0.875]  (bootstrap, n=8)
generate tasks 4
  accuracy   0.050 +/- 0.100  across 5 seeds  [0.0, 0.0, 0.0, 0.25, 0.0]
baseline     random choice among 3 options = 0.333 (1/3, chance floor for the loglik instances)  (computed: every loglik instance in this suite has 3 choices)

does not prove:
  - A suite sized for an 88M model to plausibly attempt at all is not a capability benchmark comparable to frontier-model leaderboards.
  - The loglik confidence interval reflects instance-sampling uncertainty, not run-to-run stochasticity; only the generate-task numbers reflect genuine seed variance.