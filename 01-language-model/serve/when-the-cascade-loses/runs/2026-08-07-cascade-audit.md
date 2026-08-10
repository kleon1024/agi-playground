# Run — early-exit cascade: confidence gate, escalation tax, budget cliff

## Command

```bash
cd 01-language-model/05-serve/when-the-cascade-loses/core
uv run --group torch python3 cascade.py
```

## Hardware and software

| | |
|---|---|
| CPU | Apple M1 Pro (local lane) |
| GPU | none — `torch.cuda.is_available()` is `False` in this environment, confirmed before this chapter was built |
| OS | macOS 15.6.1, Darwin 24.6.0 |
| torch | 2.10.0 |
| Data | tinyshakespeare (`karpathy/char-rnn`), character-level tokenizer, 65 symbols |
| Total wall-clock | ~189s for the full script (training dominates) |
| Cost | \$0 (local CPU lane) |

## Models trained from scratch for this run

```
target (expensive): 4 layers, d_model=256, n_head=4, n_kv_head=2 -> 2,903,552 params (2.9M)
cheap:              2 layers, d_model=96,  n_head=2, n_kv_head=2 ->   227,904 params (0.2M)
```

`cheap-good` and `cheap-poor` share this exact cheap architecture and differ
only in training steps (600 vs 40) — isolating cheap-model quality as the one
variable under test, holding the gate mechanism, the target, and the prompt
fixed.

```
target train:     600 steps, final loss 1.4756, wall-clock 144.50s
cheap-good train: 600 steps, final loss 1.8840, wall-clock  34.17s
cheap-poor train:  40 steps, final loss 3.2372, wall-clock   2.46s
```

## Result — 100 generated tokens from prompt `ROMEO:`

```
config                        wall_s vs target  exp calls  accept% target CE  match%
------------------------------------------------------------------------------------
target-only                     0.53      1.00         --       --     1.006   100.0
cheap-only (good)               0.12      4.57         --       --     1.547    18.0
cheap-only (poor)               0.11      4.98         --       --     1.860     2.0
cascade good tau=0.3            0.30      1.78     40/100       60     1.512    18.0
cascade good tau=0.5            0.37      1.45     57/100       43     1.219    58.0
cascade good tau=0.7            0.54      0.98     92/100        8     1.006   100.0
cascade good tau=0.9            0.58      0.91     99/100        1     1.006   100.0
cascade poor tau=0.7            0.60      0.89    100/100        0     1.006   100.0
cascade good tau=0.9 budget=5    0.12      4.40      5/100       95     1.494    13.0 (forced 94)
```

`target CE` is the expensive model's average cross-entropy over the generated
tokens — how much the target dislikes an output it was not asked to produce;
`match%` is the share of positions where the config's output equals the
target-only greedy output. Run-to-run wall-clock varies (0.46-0.53s for
target-only across two runs) while every quality metric is identical, because
the whole pipeline is seeded and deterministic.

## Reading the three failure modes

**Confidence is not correctness.** At `tau=0.3` the good cheap model accepts
60 of 100 steps on its own confidence, yet only 18% of positions match the
target's choice and target CE (1.512) is barely better than cheap-only
(1.547). The gate selects on self-reported confidence, which is not the same
as accuracy; low-threshold acceptance is confident garbage.

**The escalation tax.** At `tau=0.7` and `tau=0.9` the good cheap model
escalates 92% and 99% of steps, so the cascade pays cheap plus target almost
every step and is *slower* than calling the target directly (0.98x, 0.91x).
The poor cheap model cannot even clear `tau=0.7`: it escalates 100/100 steps
(0.89x). When the gate escalates everything, the cascade is strictly worse
than the expensive model alone.

**The budget cliff.** With a 5-expensive-call budget at `tau=0.9`, 94 of 100
steps are forced onto the cheap path after the budget is spent: match%
collapses from 100% to 13% and target CE rises from 1.006 to 1.494. The
latency budget converted a quality-preserving gate into a garbage fallback
the moment the sequence outlasted it.

## Where the cascade wins

`tau=0.5` with the good cheap model is the band where the trade is real:
1.45x faster than target-only at 58% match and target CE 1.219 — a quality
loss the serving team can price against the latency gain. Everything else on
the table is either a quality collapse or an escalation tax.

## Evidence boundary

Mechanism demo at tiny scale (2.9M target / 0.2M cheap on one prompt, one
seed), per the evidence-scale rule: it proves the three failure modes exist
and measures their shape; it does not claim these thresholds or ratios carry
to production models. The gate mechanism is cited to BranchyNet
(Teerapittayanon et al., ICPR 2016; arXiv:1709.01686), and the
confident-but-wrong observation is the calibration failure that
prediction-based early-exit systems must measure per slice, not globally.
