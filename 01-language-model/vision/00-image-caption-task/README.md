---
status: verified
level: applied
base: none
verified: 2026-07-31
label: The image-caption task
---

# What makes a synthetic image+question pair actually require looking at the image?

**Question:** before any vision pathway can be trained, you need a set of
image+question+answer instances with a specific property: the question cannot
be answered correctly without the image. Get that property wrong and a model
that ignores pixels entirely can still score well, and the eval would never
catch it.

**The artifact this chapter produces** is one instance — `vqa-6` from the
committed fixtures, a 32x32 image with three shapes (`R`=red, `G`=green,
`B`=blue, `.`=background):

```
................................
......................B.........
......................B.........
..........R..........BBB........
........RRRRR.......BBBBB.......
........RRRRR.......BBBBB.......
.......RRRRRRR......BBBBB.......
........RRRRR......BBBBBBB......
........RRRRR.....BBBBBBBBB.....
..........R.......BBBBBBBBB.....
................................
....GGGGGGGGGGG.................
....GGGGGGGGGGG.................
....GGGGGGGGGGG.................
....GGGGGGGGGGG.................
....GGGGGGGGGGG.................
....GGGGGGGGGGG.................
....GGGGGGGGGGG.................
....GGGGGGGGGGG.................
....GGGGGGGGGGG.................
....GGGGGGGGGGG.................
................................
```

Question: *"What color is the circle?"* Answer: *"red"*. Question: *"How many
triangles are there?"* Answer: *"1"*. Neither answer is guessable from the
question text alone — the next section explains why that had to be enforced,
not assumed.

**Before this:** [why this mission exists](../README.md) — a text-only decoder
that is about to be asked to condition on pixels for the first time, and the
leakage trap a careless synthetic dataset falls into without anyone noticing.

## The leakage trap, and how the templates avoid it

A synthetic VQA set is easy to build so that the *question* gives away the
answer regardless of the image — "what color is the only shape" doesn't need
the image if there is always exactly one shape. Every question template here
is built to fail that test:

- **"How many shapes are there?" and "How many circles/squares/triangles are
  there?"** are always askable, and the count is genuinely random (0-3 per
  shape type, 1-3 total), so the answer distribution has real entropy — a
  model that always guesses "2" will be wrong most of the time.
- **"What color is the circle (or square, or triangle)?"** is askable *only*
  when the image contains exactly one instance of that shape type. If an
  image has two circles, this question is never generated for it, because the
  answer would be ambiguous.
- **"What shape is on the left (or right)?"** is askable *only* when exactly
  one shape sits in that column.
- **"Is there a circle (or square, or triangle)?"** is a yes/no question whose
  balance comes from the same randomness as the count questions.

Each image gets two questions sampled from whichever of these are actually
applicable to it, biased toward the conditional ones (color, column) when
available, since those are the harder pair to answer from text alone.

## Images are rendered, not downloaded

`core/generate_dataset.py` uses nothing beyond the standard library. Each
image is a 32x32 grid split into four 16x16 cells (top/bottom x left/right);
between one and three cells hold a filled shape (circle, square, or triangle)
in one of four colors, placed with a random size and small position jitter so
no two shapes ever overlap — the grid does that for free. Images are written
as PPM (`P6`), the plainest binary image format that exists: a three-line
header followed by raw RGB bytes.

## Two real defects this run found, and fixed

The first version of this generator used disjoint seed *ranges* for train and
eval — seeds `0..1999` for train, `100000..100399` for eval — on the
assumption that different seeds mean different images. The mission's own
guardrail ("checked programmatically, so no eval instance is a near-duplicate
of a training instance") caught that assumption directly: **116 pixel-hash
collisions** between the two sets, out of 2,400 images. With only 3 shapes, 4
colors, 4 cells, and 1-3 occupied cells, a single-shape image has just 48
possible pixel-identical outcomes — far fewer than the ~700 single-shape
images a 2,000-example train set draws, so the same image recurs by the
birthday paradox, and a later eval draw from the same tiny space lands on one
already in train.

This is the birthday paradox. With `k` possible pixel-identical outcomes and
`n` independent draws, the probability at least one pair collides is
approximately `1 - exp(-n(n-1) / 2k)` for `n << k`. At the original
single-shape state space (`k=48`) and roughly 700 single-shape draws
(`n≈700`), that formula gives `1 - exp(-5098) ≈ 1.0` -- collisions were
essentially certain before a single image was rendered. Widening size and
position jitter to `k=3,600` changes the exponent to roughly `-68`, still
nominally "certain" in the pure math but spread thinly enough across 3,600
outcomes that a train/eval collision specifically becomes rare, matching the
guardrail's zero-collision result.

<!-- interactive: CollisionProbability -->

Near-duplicate detection between train and eval splits is a known failure
mode in dataset curation at every scale: CCNet (Wenzek et al., 2019) and
GPT-3's training corpus documentation (Brown et al., 2020) both report
fuzzy-deduplication passes for the same reason -- an overlapping held-out set
silently inflates every downstream metric.

Rejection sampling — skip any eval candidate whose pixel hash already exists in
train, advance the seed, try again — fixed the collision count to exactly
zero. But it exposed a second, quieter defect: with train having already
covered nearly all 48 single-shape states, *every* fresh single-shape eval
candidate collided, and the sampler silently dropped the entire bucket. Eval's
shape-count distribution came back as 124 two-shape and 276 three-shape
images — zero single-shape images at all. A guardrail can report a clean pass
and the dataset can still be broken in a way the guardrail was never built to
see.

The real fix was to widen the state space at its source: each shape now also
draws a size and a small position jitter, raising the single-shape space from
48 to 3,600. Collisions stayed at zero and eval's distribution came back
proportional to train's — 105 one-shape, 150 two-shape, 145 three-shape.
Full numbers for all three attempts are in
[`runs/2026-07-31-dataset-gen.md`](runs/2026-07-31-dataset-gen.md).

## Run it

```bash
cd core
uv run python generate_dataset.py dataset --train 2000 --eval 400 --out ../data/raw
uv run python generate_dataset.py fixtures --fixtures 8 --fixtures-seed-start 0 --out ../fixtures
```

CPU only, no network, no dependencies beyond the standard library, under a
second for 2,400 images.

## What this run actually produced

```
train  n=2000   1-shape 696  2-shape 658  3-shape 646
       shapes   circle 1300  square 1340  triangle 1310
       questions column_shape 1220  shape_color 1276  shape_count 475
                 total_count 461  presence 492

eval   n=400    1-shape 105  2-shape 150  3-shape 145
       shapes   circle 290  square 264  triangle 286
       questions column_shape 239  shape_color 261  shape_count 101
                 total_count 100  presence 83

train-internal pixel-hash duplicates : 79 of 2,000 (disclosed, not a leakage guardrail)
train/eval pixel-hash collisions     : 0 (the guardrail this stage exists to satisfy)
```

Full manifests (`data/raw/train.jsonl`, `data/raw/eval.jsonl`) are git-ignored
and regenerated by the command above; eight real example images and their
manifest are committed under `fixtures/` for direct inspection.

## What this task set is and is not

Every image is a flat-color shape on a plain background, generated by this
mission's own code with a fixed, recorded seed range — there is no external
attribution or license question, and no claim that any of it resembles a real
photograph. It is sized to make a text-only decoder's blind guess and a vision
pathway's real answer measurably different, which is the property mission 05's
[text-only baseline](../mission.yaml) depends on — nothing more. Full boundary
in [`../mission.yaml`](../mission.yaml)'s `does_not_prove`.

**Next:** stage 01 builds the patch-embedding and vision-token fusion path that
turns these images into something the decoder can condition on, and measures
whether it beats a decoder that never sees them.

A detour from here: [why does a leakage guardrail need to check pixels, not
seeds?](seed-vs-pixels/) — the two recorded defects reproduced on the current
generator: disjoint seeds still collide (17 without rejection), and the
rejection sampler that fixed it can silently distort the eval distribution.

Another detour: [disjoint seeds are not disjoint images](the-collision-that-closed-the-gap/) — the recorded dataset run read: 116 pixel collisions across seed streams, plus the empty-bucket defect the pixels-only check missed.
