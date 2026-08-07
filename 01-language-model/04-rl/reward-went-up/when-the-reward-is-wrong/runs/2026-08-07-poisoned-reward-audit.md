# Run — poisoned-reward audit: what the curve hides when labels are wrong or late

**Date:** 2026-08-07
**Command:**

```bash
cd 01-language-model/04-rl/reward-went-up/when-the-reward-is-wrong/core
uv run --group torch python poison_audit.py --warm-steps 250 \
    --distortion-groups 20 --rl-steps 30
```

**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; torch 2.10.0.
**Wall-clock:** 184.2s real (150.5s user, 125.5s sys — torch CPU thread
pool, ~3 minutes).
**Cost:** \$0 (local lane).
**Seed:** 1337 (deterministic single seed; rerun reproduces the numbers).

## Purpose

[The parent chapter](../README.md) measured the reward curve lying when the
policy hacks a *correct* reward (reward hacking, KL-leash zero, inverted U).
This run breaks the label supply instead, on the same real GRPO trainer
(`04-rl/core/grpo.py`): the warm start the parent's Exercise 1 asks for
(executed), advantage distortion under flipped labels, a clean-vs-poisoned
training comparison with a held-out true-correctness read, and delay priced
as a poison rate.

## Output (verbatim)

```
poisoned-reward audit (real 04-rl GRPO trainer, CPU, seed 1337):

  1. warm start, executed:
     250 supervised steps over 24 hand-written examples
     tag fire rate: 79.2% (76/96 completions carry <think>/<answer>)

  2. advantage distortion, executed (real rollouts, 20 groups x 8):
     flip rate 5%: 10.0% of groups change which completion is pushed (2/20); 10.0% push a wrong completion; poisoned-vs-true rank corr 0.478
     flip rate 10%: 35.0% of groups change which completion is pushed (7/20); 35.0% push a wrong completion; poisoned-vs-true rank corr 0.439
     flip rate 20%: 60.0% of groups change which completion is pushed (12/20); 60.0% push a wrong completion; poisoned-vs-true rank corr 0.403

  3. training comparison, executed (30 GRPO steps, clean vs 10%-flipped, same seed and problems):
     step | clean reward | clean true | poison reward | poison true
        0 |       0.110 |      0.000 |        0.166 |       0.000
        1 |       0.114 |      0.000 |        0.268 |       0.000
        2 |       0.126 |      0.000 |        0.201 |       0.000
        3 |       0.108 |      0.000 |        0.217 |       0.000
        4 |       0.135 |      0.000 |        0.234 |       0.000
        5 |       0.092 |      0.000 |        0.237 |       0.000
        6 |       0.145 |      0.000 |        0.314 |       0.000
        7 |       0.162 |      0.000 |        0.214 |       0.000
        8 |       0.158 |      0.031 |        0.226 |       0.062
        9 |       0.150 |      0.000 |        0.226 |       0.000
       10 |       0.126 |      0.000 |        0.204 |       0.000
       11 |       0.141 |      0.000 |        0.223 |       0.000
       12 |       0.160 |      0.000 |        0.198 |       0.000
       13 |       0.159 |      0.000 |        0.209 |       0.000
       14 |       0.148 |      0.000 |        0.249 |       0.000
       15 |       0.125 |      0.000 |        0.254 |       0.000
       16 |       0.152 |      0.000 |        0.251 |       0.000
       17 |       0.168 |      0.031 |        0.318 |       0.000
       18 |       0.166 |      0.000 |        0.196 |       0.000
       19 |       0.146 |      0.000 |        0.374 |       0.031
       20 |       0.139 |      0.000 |        0.312 |       0.000
       21 |       0.181 |      0.031 |        0.391 |       0.031
       22 |       0.149 |      0.000 |        0.245 |       0.000
       23 |       0.192 |      0.042 |        0.281 |       0.000
       24 |       0.158 |      0.000 |        0.316 |       0.000
       25 |       0.307 |      0.156 |        0.334 |       0.125
       26 |       0.250 |      0.125 |        0.385 |       0.188
       27 |       0.116 |      0.000 |        0.212 |       0.031
       28 |       0.160 |      0.000 |        0.183 |       0.042
       29 |       0.151 |      0.000 |        0.290 |       0.000

  4. delay priced as poison, executed (truth flips with prob drift per step; the label lags L steps):
     drift | lag | label agreement | label error rate
     2%  |   1 |          97.8% |            2.2%
     2%  |   5 |          90.5% |            9.5%
     2%  |  10 |          83.0% |           17.0%
     2%  |  20 |          71.7% |           28.3%
     5%  |   1 |          94.6% |            5.4%
     5%  |   5 |          78.6% |           21.4%
     5%  |  10 |          67.4% |           32.6%
     5%  |  20 |          55.5% |           44.5%

  verdict: a rising reward curve is evidence only when the labels
  it rises against are trusted. A clean held-out verifier that
  disagrees with the training reward is the detection; a stale
  label is a poisoned label with error rate = drift x lag, and
  the budget belongs in the label pipeline, not the optimizer.
```

## Reading the output

- **Warm start works.** 250 supervised steps over 24 well-formed examples
  bring the tag fire rate to 79.2% — the cold-start baseline was the base
  run's 200/200 degenerate groups ([the base run
  record](../../../runs/2026-07-30-base-grpo-run.md)). This is parent
  Exercise 1, executed: GRPO fires because the policy can emit the format
  the reward requires.
- **Flipped labels move the decision, not just the score.** At a 20% flip
  rate, 6 in 10 groups change which completion gets pushed to the top
  advantage, and the pushed completion is wrong every time the choice
  changed. The poisoned-vs-true rank correlation slides from 0.478 at 5%
  to 0.403 at 20%.
- **The curve lies in both arms.** Both the clean and the poisoned arm's
  training reward rises across the 30 steps; the poisoned arm's reward
  runs visibly higher (roughly 0.20-0.39 vs 0.09-0.31) while its held-out
  true correctness is not better (both mostly 0.0-0.2). A rising curve
  therefore proves nothing about the labels; the gap between the training
  reward and a clean verifier is the signal.
- **Stale labels are poisoned labels.** Agreement with current truth
  decays as `0.5 + 0.5 (1 - 2·drift)^lag`; at drift 5% and lag 20 the
  label is a coin flip (55.5% agreement). The first-order rule from the
  verdict — error ≈ drift × lag — matches the measured table at small
  `drift × lag` and saturates at 50% for a binary label.

## Evidence boundary

Deterministic single seed; 24 hand-written warm-start examples; a
128-dimension, 4-layer char-level policy; toy scale. This is a mechanism
demo — it shows *that* flipped and delayed labels distort the GRPO
decision and *that* training reward stops being trustworthy, not the
magnitude on a production checkpoint. The same failure family on real
RLHF pipelines is documented in dated external work: poisoned human
feedback can embed a universal jailbreak backdoor from a small slice of
the preference data (Rando & Tramèr, ICLR 2024, arXiv:2311.14455), and
poisoned instruction-tuning examples survive into behavior on held-out
tasks (Wan et al., ICML 2023, arXiv:2305.00944). The delay arm is a
deterministic model of label staleness, not a measurement of a real
label pipeline.
