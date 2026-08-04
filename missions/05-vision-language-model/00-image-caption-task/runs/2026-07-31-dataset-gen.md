# Generating the synthetic image+question+answer set

First real run of `core/generate_dataset.py`. The interesting result is not the
2,000/400 split — it is that the naive version of this script, using disjoint
seed *ranges* for train and eval, still produced 116 pixel-identical
collisions between the two sets on its first run, and a second defect that
collisions alone did not reveal: the eval set's single-shape bucket came out
empty. Both are recorded below rather than quietly fixed and forgotten,
because they are the actual lesson this stage teaches about small synthetic
task spaces.

## Command

```bash
cd missions/05-vision-language-model/00-image-caption-task/core
uv run python generate_dataset.py dataset --train 2000 --eval 400 --out ../data/raw
uv run python generate_dataset.py fixtures --fixtures 8 --fixtures-seed-start 0 --out ../fixtures
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 24.6.0, arm64 |
| Python | 3.12.9 (uv-managed) |
| Dependencies | none beyond the standard library (`random`, `hashlib`, `json`) |
| Repository HEAD | `e88f5cc` |

CPU only, no network, no GPU, \$0.

## Attempt 1: disjoint seed ranges are not disjoint images

Train used seeds `0..1999`, eval used seeds `100000..100399` — different seeds,
different pseudo-random streams. The check this stage's guardrail requires
(`mission.yaml`: "checked programmatically, so no eval instance is a
near-duplicate of a training instance") still found:

| | |
|---|---|
| Train examples | 2,000 |
| Eval examples | 400 |
| Wall-clock | 0.932s |
| **Pixel-hash collisions, train vs eval** | **116** |

The cause: with 3 shape types, 4 colors, 4 grid cells, and 1-3 occupied cells,
a single-shape image has only `4 cells x 3 shapes x 4 colors = 48` possible
pixel-identical outcomes. Drawing ~700 single-shape images for train (a third
of 2,000, since shape count is uniform over 1-3) draws far more times than
there are outcomes, so by the birthday paradox the same image recurs — and a
later eval draw from the same 48-point space has good odds of landing on one
train already produced. Disjoint seeds guarantee disjoint *random-number
streams*, not disjoint *renders*, whenever the render space is this small.

## Attempt 2: rejection sampling, and the distortion it exposed

`make_eval_set_disjoint_from()` fixes the guardrail unconditionally: draw eval
candidates past the seed-100000 start, hash each one, and skip any hash
already seen in train or in the eval set built so far, advancing the seed
until `n` genuinely new examples exist. Re-running with the same train set:

| | |
|---|---|
| Train examples | 2,000 |
| Eval examples | 400 |
| Wall-clock | 0.924s |
| Train-internal pixel-hash duplicates | 79 |
| Eval candidates rejected (collided with train or a prior eval draw) | 507 |
| **Pixel-hash collisions, train vs eval** | **0** |

The collision guardrail now holds exactly — but the eval set's shape-count
distribution came out 124 two-shape and 276 three-shape images, with **zero**
single-shape images. Train's ~700 single-shape draws had already covered
nearly all 48 single-shape states; every fresh single-shape candidate the
rejection sampler tried necessarily collided with one already in train, so the
sampler silently filtered the entire bucket out of eval. A guardrail can pass
and the dataset can still be broken in a way the guardrail was never built to
see.

## Attempt 3: widen the state space, not just the sampler

Fixed at the source: each shape now also draws a size (`half`, three options)
and a position jitter (`dx, dy`, five options each), still safely inside its
16px cell. That raises the single-shape state space from 48 to
`4 x 3 x 4 x 3 x 5 x 5 = 3,600` — comfortably larger than the ~700 draws per
num-shapes bucket. Re-running with jitter enabled, same seeds:

| | |
|---|---|
| Train examples | 2,000 |
| Eval examples | 400 |
| Wall-clock | 0.924s |
| Train-internal pixel-hash duplicates | 79 |
| Eval candidates rejected | 29 |
| **Pixel-hash collisions, train vs eval** | **0** |

Rejections dropped from 507 to 29, and the eval shape-count distribution is
now 105 one-shape, 150 two-shape, 145 three-shape — every bucket present,
roughly proportional to train's 696 one-shape, 658 two-shape, 646 three-shape.
Train-internal duplicates (79 of 2,000) are reported but not eliminated: the
guardrail is about train/eval leakage specifically, and a small number of
repeated training images does not violate it, though it is a real, disclosed
limit of a state space this size.

## Distribution, final run

```
train  n=2000   1-shape 696  2-shape 658  3-shape 646
       shapes   circle 1300  square 1340  triangle 1310
       colors   red 920  green 980  blue 1017  yellow 1033
       questions column_shape 1220  shape_color 1276  shape_count 475
                 total_count 461  presence 492

eval   n=400    1-shape 105  2-shape 150  3-shape 145
       shapes   circle 290  square 264  triangle 286
       colors   red 212  green 213  blue 218  yellow 197
       questions column_shape 239  shape_color 261  shape_count 101
                 total_count 100  presence 83
```

Full manifests: `data/raw/train.jsonl`, `data/raw/eval.jsonl` (git-ignored,
regenerate with the command above). Eight committed example images and their
manifest: `fixtures/`.

## What this run does not establish

Nothing about a trained model — no model has touched this data yet. Nothing
about real-photo relevance; every image is a flat-color shape on a plain
background, by construction. The state-space finding above is specific to this
generator's grid size, shape count, and color count — a larger canvas or more
colors would need its own collision check, not an assumption that this run's
numbers still hold.
