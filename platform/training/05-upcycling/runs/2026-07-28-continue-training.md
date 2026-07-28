# Continued training: dense parent against upcycled MoE, 200M tokens each

The comparison the surgery run could not make. Two arms start from the *same*
88M checkpoint at the same validation loss; one keeps training as a dense
model, the other is upcycled to 258M and trains from there. Same batches, same
order, same schedule, same held-out evaluation.

## Command

```bash
cd platform/training/05-upcycling/core
python continue_training.py --arm dense --checkpoint ckpt.pt \
    --data ~/agi-playground/data/tokens --tokens 2e8 \
    --eval-every 250 --eval-iters 20 --out ~/upcycle-dense.json
python continue_training.py --arm moe --checkpoint moe-upcycled.pt \
    --data ~/agi-playground/data/tokens --tokens 2e8 \
    --eval-every 250 --eval-iters 20 --out ~/upcycle-moe.json
```

## What is held equal

| | |
|---|---|
| Budget | equal additional tokens: 199,999,488 per arm |
| Starting point | the same checkpoint, both arms at val 3.0576 |
| Batches | `seed=1234`, identical sequence and order for both arms |
| Evaluation | `seed=999`, 20 batches of 8x1024, identical for both arms |
| Learning rate | 1e-4 peak, cosine, identical schedule |
| GPU | NVIDIA GeForce RTX 4090, driver 591.86, WSL2 on Ubuntu 22.04.3 |
| torch | 2.13.0+cu130, bf16 autocast |
| Cost | $0 (local lane) |

## Result

| | dense continue | upcycled MoE |
|---|---:|---:|
| Parameters | 88,197,888 | 258,104,064 (144,838,656 active) |
| Start | 3.0576 | 3.0576 |
| Worst point | 3.1446 at 53.2M tokens | 3.1443 at 53.2M tokens |
| Final at 200M | 3.0939 | **3.0851** |
| Against its own start | +0.0363 | +0.0275 |
| Wall-clock | 31.3 min, 106,369 tok/s | 60.5 min, 55,069 tok/s |

**Neither arm recovered its starting loss.** Both got worse for the first 53M
tokens, peaking 0.087 above where they began, then improved monotonically for
the remaining 147M without either one getting back to 3.0576. Restarting a
checkpoint that finished a cosine schedule at nearly zero learning rate, at
1e-4, costs more than 200M tokens to undo. That is the dominant effect in this
run, and it applies to both arms equally.

**The upcycled arm ends 0.0088 nats ahead, and it did not start that way.**
The gap over the run:

| Tokens | dense | MoE | MoE minus dense |
|---:|---:|---:|---:|
| 0 | 3.0576 | 3.0576 | 0.0000 |
| 16.4M | 3.1244 | 3.1263 | +0.0019 |
| 32.8M | 3.1364 | 3.1362 | -0.0002 |
| 65.5M | 3.1421 | 3.1395 | -0.0026 |
| 131.1M | 3.1145 | 3.1084 | -0.0061 |
| 200.0M | 3.0939 | 3.0851 | **-0.0088** |

The MoE arm is *behind* for the first 32.8M tokens, crosses over, and then
pulls away monotonically for the remaining 167M with no sign of flattening.
That shape is what the surgery predicts: at step 0 the four experts are
identical copies, so the extra 170M parameters compute nothing the dense model
did not already compute, and the router is churning without yet affecting the
output. The extra capacity only starts paying once the experts have diverged
into different functions, and that takes tokens.

An experiment stopped at 30M tokens would have reported the opposite result
with a straight face.

## Wall-clock, where the answer reverses

The MoE arm took 1.93x as long for the same tokens: 55,069 tok/s against
106,369. **Under an equal-wall-clock budget the dense arm gets 1.93x the data,
and at 200M tokens it was still improving by roughly 0.005 per 16M tokens.**
Whether it would close 0.0088 nats in another 186M tokens was not measured, so
this run reports a result under equal tokens and no result under equal
wall-clock — the same split the
[MoE ablation rung](../../02-architecture-ablations/runs/2026-07-28-moe-rung.md)
found from the other direction.

This also corrects the earlier smoke measurement. The 244-step run recorded in
[`2026-07-28-upcycle-88m.md`](2026-07-28-upcycle-88m.md) reported 16.6k tok/s
for the upcycled model; that figure is dominated by startup over 4M tokens.
Sustained over 200M it is 55,069 tok/s, and the honest comparison is against
the 106,369 the dense arm reached in the same script on the same data rather
than against a differently-configured pretraining run.

## What this run does not establish

- **That upcycling beats dense continuation.** It establishes that it does at
  an equal *token* budget, at this scale, after 33M tokens, by 0.0088 nats. It
  says nothing under an equal wall-clock or equal storage budget.
- **That 0.0088 is outside run-to-run variance.** One seed per arm. What
  supports the result is not the endpoint but its shape: the gap is monotone
  across the 25 consecutive evaluations after the crossover, which is not what
  seed noise looks like. It is still one seed, and the ablation ladder's own
  rule applies here as much as there.
- **That either model is good.** Both ended worse than the checkpoint they
  started from. The interesting quantity is the difference between the arms,
  not either arm's absolute loss.
- **That 4 experts at top-2 is the right shape.** It was chosen to make the
  step-0 identity check exact, not because it was tuned.
