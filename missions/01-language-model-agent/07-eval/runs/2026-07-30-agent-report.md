# agent report — 2026-07-30T09:20:52+00:00

transcripts  6 across 2 tasks
harness configs seen: 1
  count-py-files           success 0.00 +/- 0.00  (3 rollouts, 6.0 steps avg)
  find-resolve-in-jail     success 0.00 +/- 0.00  (3 rollouts, 6.0 steps avg)
overall      0.000  95% CI [0.000, 0.000]
baseline     chance (arbitrary tool-call sequence succeeding) = 0.0  (no ReAct-formatted examples in this checkpoint's SFT mix; task requires at least one parseable Action)

does not prove:
  - Success rate is a property of (model, harness) jointly; it says nothing about how the same model would score under a different tool set, loop design, or context-management policy.
  - If harness_configs_seen > 1, the aggregate mixes non-comparable runs — read the per-transcript harness blocks in that case, not the aggregate.