# Vision pathway vs. text-only baseline, 3 seeds each

## Command

```bash
cd missions/05-vision-language-model/01-vision-fusion/core
uv run --group torch python train.py --seeds 3 --epochs 30 --batch-size 64
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 24.6.0, arm64 |
| Python | 3.12.9 (uv-managed), torch 2.13.0 |
| Device | CPU. A single-seed pilot at these settings ran in 424.6s; MPS is available on this machine but was not needed — the full 3-seed, 2-model run completed in 19.7 minutes on CPU alone, and this stage's own mission.yaml does not budget for GPU time, so there was nothing to buy by moving it. |
| Repository HEAD | `9ab6faf` |

$0 marginal cost, no hosted API calls.

## What ran

Both models are the identical `VisionLanguageTransformer` class and `Config`
(d_model=128, n_layer=4, n_head=4, n_kv_head=2, d_ff=336) -- the only
difference is `use_vision`. Vision: 732,928 parameters. Text-only: 718,464
parameters (the gap is exactly the patch-embed projection and vision
position table). Each trained for 30 epochs over 3,924 train QA pairs
(batch size 64, AdamW, lr 3e-3, no schedule), then evaluated by greedy
decode + exact string match against the 784 held-out QA pairs, for 3
independent seeds.

## Results

```
vision     eval exact-match   mean=0.4375  spread=0.2309  per_seed=[0.5128, 0.5153, 0.2844]
text_only  eval exact-match   mean=0.3270  spread=0.0459  per_seed=[0.3304, 0.3482, 0.3023]

vision     final train loss   mean=0.5689  spread=0.1957  per_seed=[0.5317, 0.4896, 0.6853]
text_only  final train loss   mean=0.6349  spread=0.1157  per_seed=[0.6746, 0.5589, 0.6712]

wall-clock: 1181.4s (19.7 min) for all 6 (model, seed) runs combined, CPU only
```

## The honest verdict, not the clean one

Two of the vision pathway's three seeds (0.513, 0.515) decisively beat every
text-only seed (0.330, 0.348, 0.302) -- a ~17-18 point gap, far larger than
text-only's own 0.046 seed spread. On those two seeds, the vision pathway is
unambiguously using the image: exact-match on questions like "what color is
the circle" or "how many squares are there" requires information the
text-only model structurally cannot see.

The third vision seed (0.284) falls *below every text-only seed*, including
the ones it should be beating. That single collapse is enough that vision's
own spread across seeds (0.231) is larger than the gap between the two
means (0.4375 - 0.3270 = 0.1105). Per this repository's own rule --
architecture ablations report a difference smaller than run-to-run spread as
no result, not as a win -- the honest reading is **not** "the vision pathway
beats the baseline," full stop. It is: *the vision pathway can clearly learn
to use the image, and does so in 2 of 3 runs by a wide margin, but training
at this scale is unstable enough that one seed failed to learn it at all* --
a partial result, not a clean one.

This is very likely an optimization-stability finding, not an architecture
one: seed 2's final train loss (0.6853) is close to text-only's own losses
and far worse than the other two vision seeds (0.53, 0.49), meaning that
run's vision pathway never really left a poorly-fit region during the fixed,
un-scheduled, no-warmup 3e-3 learning rate used for all six runs. A learning
rate schedule or warmup was in scope to add and was not added, on the
judgment that reporting the instability honestly is more informative for
this stage's purpose (does the mechanism work at all) than hiding it behind
a hyperparameter search tuned after seeing which seed embarrassed the result.
That tuning question is left to stage 02.

## What this run does not establish

No hosted-API comparison -- that baseline is stage 02's job, per mission
05's own stage table. No claim about which architecture choice (patch size,
fusion point, mask design) is best; only this one configuration was run.
No claim about training stability at a different learning rate or schedule
-- three seeds at one fixed setting is what ran, and a different setting
could plausibly close or widen the seed-2 gap; that is future work, not this
run's finding. The eval set is the same synthetic, disjoint-checked set
[stage 00](../../00-image-caption-task/) produced; nothing here says
anything about real photographs.
