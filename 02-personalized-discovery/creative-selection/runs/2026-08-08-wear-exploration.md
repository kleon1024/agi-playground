# Run — the wear-exploration audit

**Date:** 2026-08-08
**Command:** `uv run python core/wear_exploration.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.10s.
**Cost:** \$0 (local lane).

## Purpose

The stage run scores creatives per context. The audit asks the
case-finding question at production scale: what happens to selection
when the creative that wins on history is wearing out? It serves 20,000
placements (fixed seed) to a mature creative whose lifetime CTR is 0.06
but whose true rate decays from 0.06 toward 0.025, and a new creative
whose true rate is 0.04, under four selection policies. Each policy
sees its own Bernoulli click stream and the creatives wear as they are
served.

## Output

```
wear-exploration audit: 20,000 placements, fixed seed
creative A: lifetime CTR 0.06, true rate decays 0.06 -> 0.025
creative B: true rate 0.04, cold-start prior 0.03

                        policy   clicks  served A  served B clicks/imp
          greedy, lifetime CTR      635     20000         0     0.0318
  epsilon-greedy 0.10, lifetime      645     18981      1019     0.0323
  greedy, recency-weighted (EWMA)      828      7700     12300     0.0414
     Thompson, decaying counts      807      8444     11556     0.0403

reading: greedy on lifetime CTR crowns the stale winner — A's
0.06 history hides the decay to 0.025, so the policy keeps serving
it and never estimates B. Exploration alone barely helps: the
greedy arm still reads the same sticky average. The fix is the
estimator, not the policy: a recency-weighted estimate or a
decaying Bayesian posterior lets selection see the wear and
switch to the creative that is actually better.
```

## Notes

- Greedy on lifetime CTR serves A for all 20,000 placements and earns
  635 clicks: A's 0.06 lifetime average hides the decay to 0.025, so
  the policy never estimates B. This is the stale-winner failure the
  stage's logged-CTR detour warns about, now measured end to end.
- Epsilon-greedy (0.10) explores B 1,019 times and earns 645 clicks —
  exploration corrects B's cold-start estimate but the greedy arm still
  reads the same sticky lifetime average, so the corrected estimate
  cannot switch selection.
- The fix is the estimator, not the policy: a recency-weighted EWMA
  (828 clicks) and Thompson sampling with decaying counts (807 clicks)
  both serve B for most of the run and recover about 30 percent more
  clicks than greedy.
- Clicks drawn as Bernoulli from the creatives' true rates at serve
  time; wear is a declared decay function of cumulative served
  impressions. Illustrative and deterministic per seed, not real
  creative logs.
