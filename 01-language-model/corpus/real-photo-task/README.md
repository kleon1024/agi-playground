---
status: verified
level: applied
base: none
verified: 2026-08-01
label: The real-photo task
---

# Does the leakage discipline that worked on synthetic shapes survive real photographs?

**Question:** stages 00-02 built the vision-vs-text-only comparison on a
synthetic dataset generated to guarantee no answer is guessable from question
wording alone. Real photographs have none of that control built in — the
question set has to come from somewhere that already asked real people real
questions about real images, and the exact-match scoring stage 01/02 rely on
has to survive answers that are no longer single-word by construction.

**The artifact this stage produces** is 300 train and 100 eval real COCO
photographs, each with 1-2 real human-written questions and a real
majority-vote answer, disjoint by COCO image id.

**Before this:** [why this mission exists](../../README.md) and
[stage 02's NOT MET verdict](../02-report/) on synthetic shapes — the
question this stage answers is whether that verdict changes, gets sharper,
or stays the same once the images are real.

## Where the questions and images come from

[VQA v2](https://arxiv.org/abs/1612.00837) (Goyal et al., 2017) pairs COCO
photographs with real human-written questions and ten independent human
answers per question, released as a public research dataset (annotations
CC BY 4.0; images inherit COCO's Flickr ToU — non-commercial research and
educational use only, no commercial-rights claim made here). This stage
downloads the val2014 questions and annotations directly from VQA's own S3
mirror, and fetches each selected image from
`images.cocodataset.org/val2014/`.

## Keeping it exact-match scoreable

Stages 00-02's greedy-decode evaluation compares a short generated string
against a ground-truth string. VQA v2's own `answer_type` field makes that
possible without inventing a new scoring rule: `yes/no` questions are kept
only when the majority answer is literally "yes" or "no"; `number` and
`other` questions are kept only when the majority answer is a single
alphanumeric word. Multi-word answers ("a pair of scissors") are dropped
rather than silently truncated — truncating would score a partial match as
if the model had produced the intended answer, which it did not.

## Disjointness moves from pixel hash to image id

Stage 00's synthetic images could collide by pixel hash — the same rendered
image reachable from two different seeds — so pixel hash was the right
disjointness check there. A real photograph essentially never repeats
byte-for-byte, but the same COCO image can appear in different question
sets; the guardrail that actually matters here is that no COCO **image id**
appears in both train and eval, checked programmatically before the files
are written.

## What this run actually produced

```
images with >=1 scoreable QA pair: 40,474 (of 40,474 images with any question)
train images  : 300  (599 QA pairs)
eval images   : 100  (198 QA pairs)
image-id overlap between train and eval (must be 0): 0
```

Answer-type mix stayed close to VQA v2's own known distribution (roughly
40% yes/no, 40% other, 20% number) across both splits — train: 237 yes/no,
101 number, 261 other; eval: 80 yes/no, 25 number, 93 other. Full command,
hardware, and wall-clock in
[`runs/2026-08-01-real-photo-dataset.md`](runs/2026-08-01-real-photo-dataset.md).

## Run it

```bash
cd core
uv run --group vision python prepare_dataset.py --train 300 --eval 100 --seed 0
```

CPU only, network required (VQA v2's S3 mirror and COCO's image host), about
9.3 minutes end to end — almost entirely image-download wall-clock, well
inside the 30-minute ceiling `mission.yaml`'s stages 03-05 extension
declares.

## The fix and its trade

The fix is to key each guardrail to the object that actually leaks in the
new data regime. Pixel-hash disjointness was the right check for
procedurally rendered shapes — the same image is reachable from two seeds —
but real photographs are unique artifacts, so the realistic leak is the
same COCO image appearing in both splits by id. The check moves to image
id (asserted zero overlap before the files are written), and the scoring
contract moves to VQA v2's own `answer_type` field: yes/no questions are
kept only when the majority answer is literally "yes" or "no," and
`number`/`other` only when the majority answer is a single alphanumeric
word. The trade is priced in what the filter refuses: multi-word answers
("a pair of scissors") are dropped rather than truncated, because
truncating would score a partial match as if the model produced the
intended answer — the filter makes every held-out item mechanically
scoreable at the cost of excluding the free-form questions a judge-based
contract would need. The second trade is the 32x32 downsample: it lets
stage 04 reuse stage 01's architecture completely unchanged, and it may
destroy information a larger patch grid would keep — a modeling question
the data stage names and hands forward, not one it answers. The measured
build keeps the answer-type mix close to VQA v2's known distribution
(train 237 yes/no, 101 number, 261 other; eval 80/25/93), so the harder
and easier categories stay represented on both sides of the split.

## Who owns the loop

- **The data pipeline** owns the filter and the id-based disjointness
  check: which answer types survive the scoreable contract, and the
  asserted zero image-id overlap, are pipeline decisions made before the
  files are written.
- **The evaluation owner** owns the scoreable contract itself: exact
  string match needs an unambiguous target, and the filter is what keeps
  the held-out comparison a real evaluation instead of a paraphrase game.
- **The model team** owns the downsample question the data stage hands
  forward: stage 04 inherits the 32x32 input and must report whether the
  downsampling limited what the pathway could learn, rather than assuming
  the reuse was free.

## What this task set is and is not

300 train and 100 eval images is a few hundred, not VQA v2's full ~40,000-image
validation set — nowhere near large enough to be comparable to a published
VQA v2 leaderboard number, and this stage makes no such claim. Images are
resized to this mission's existing 32x32 input so stage 04 can reuse stage
01's `VisionPatchEmbed`/`VisionLanguageTransformer` completely unchanged;
that downsampling itself may destroy information a larger patch grid would
keep, which is a modeling question stage 04 inherits, not one this stage
answers. Full boundary in [`../../mission.yaml`](../../mission.yaml)'s
`does_not_prove`.

**Next:** stage 04 retrains the same vision-token-prefix architecture from
stage 01 on this real-photo data and measures whether it still beats a
text-only decoder and a hosted VLM API.

A detour from here: [the real-photo guardrail: why image ID, not pixel
hash](the-real-photo-guardrail/) — the recorded dataset build read: the
exact-match filter and the ID-based disjointness check that real data
actually needs.

Another detour: [why real photos are checked by ID, not by pixel](the-id-based-guardrail/) — the recorded build read: image-id overlap is 0 by construction, because real photographs leak by id, not by rendering.
