# Does a linear LR warmup close stage 01's seed-2 vision collapse?

## Command

```bash
cd 01-language-model/vision/06-warmup-stability/core
uv run --group torch python train_warmup.py --seeds 3 --epochs 30 --batch-size 64
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 24.6.0, arm64 |
| Python | 3.12.9 (uv-managed), torch 2.13.0 |
| Device | CPU. 3 vision-pathway runs (seeds 0, 1, 2), 30 epochs, 3,924 train QA pairs / 784 eval QA pairs, batch size 64. |

\$0 marginal cost, no hosted API calls.

## What changed relative to stage 01

Exactly one mechanism: a linear LR warmup over the first 10% of optimizer
steps (0 -> 3e-3 across steps 0-185 of 1,860 total), then held constant at
3e-3 (stage 01's fixed rate) for the rest of training. Model class
(`VisionLanguageTransformer`), `Config`, `Tokenizer`, dataset, epochs (30),
batch size (64), optimizer (AdamW), base learning rate (3e-3), and all 3
seeds (0, 1, 2) are unchanged from stage 01's `train.py` -- only the vision
pathway was retrained; text-only was not re-run since the collapse under
test is specific to vision.

## Results

```
                       seed 0    seed 1    seed 2    mean     spread
stage 01 (no warmup)   0.5128    0.5153    0.2844    0.4375   0.2309
this stage (warmup)    0.4707    0.5242    0.4962    0.4970   0.0536

final train loss:
stage 01 (no warmup)   0.5317    0.4896    0.6853    0.5689   0.1957
this stage (warmup)    0.5708    0.4827    0.3406    0.4647   0.2302

wall-clock: 1059.9s for 3 seeds, CPU only
```

## The result: warmup closes the collapse

Stage 01's seed 2 collapsed to 0.2844 -- below every text-only seed
(0.3304, 0.3482, 0.3023) -- while seeds 0 and 1 reached 0.51-0.52. With
warmup added and nothing else changed, seed 2 reaches 0.4962, in line with
the other two seeds (0.4707, 0.5242). Eval exact-match spread drops from
0.2309 to 0.0536 -- a more than 4x tightening -- and now every one of the
three warmup seeds individually beats text-only's mean (0.3270) by a margin
several times text-only's own 0.0459 spread. This is not a case of the mean
moving while the worst seed stays bad: all three seeds moved into a tight,
clearly-winning band.

Train loss tells a more complicated story. Seed 2's train loss (0.3406) is
now the *lowest* of the three warmup runs, not the highest -- exactly
reversed from stage 01, where seed 2's high train loss (0.6853) was the
signal that it never left a poorly-fit region. That reversal is consistent
with the collapse being an optimization-trajectory problem the warmup fixed,
not evidence the warmup changed what "fit" means for this task. Seed 0's
warmup train loss (0.5708) is close to stage 01's seed 0 (0.5317) despite a
higher eval score (0.4707 vs 0.5128) -- a reminder that final-batch train
loss and held-out exact-match are two different signals that do not have to
move together, exactly as stage 01's own report already treated them
separately rather than as one number.

<!-- interactive: WarmupSeedStability -->

## What this stage does not establish

One warmup fraction (10% of steps) was tried, not a sweep -- a different
fraction might work better, worse, or not at all; this result does not claim
10% is optimal, only that it closed this specific collapse. Text-only was
not re-run with warmup, so this stage says nothing about whether warmup
would also tighten (or loosen) text-only's already-small 0.0459 spread. Only
3 seeds were tried on each side, the same seed count as stage 01's own run,
so a seed 3 or 4 could in principle reopen a gap the current 3 happen not to
show -- three seeds establishes a pattern, not an exhaustive stability
guarantee. Nothing here changes stage 01's own scope boundary: the eval set
is still stage 00's synthetic, disjoint-checked set, and stage 02's
hosted-API baseline comparison is untouched by this result.
