# Real-photo dataset build — 2026-08-01

**Command:**
```
uv run --group vision python prepare_dataset.py --train 300 --eval 100 --seed 0
```

**Hardware:** local CPU (no GPU used for this stage — dataset fetch and resize only).

**Sources:**
- Questions: `https://s3.amazonaws.com/cvmlp/vqa/mscoco/vqa/v2_Questions_Val_mscoco.zip`
- Annotations: `https://s3.amazonaws.com/cvmlp/vqa/mscoco/vqa/v2_Annotations_Val_mscoco.zip`
- Images: `http://images.cocodataset.org/val2014/COCO_val2014_{image_id:012d}.jpg`

**Filter:** VQA v2's own `answer_type`. `yes/no` kept iff the majority-vote answer is
literally "yes" or "no". `number`/`other` kept iff the majority-vote answer is a single
alphanumeric word (exact-match scoreable, matching stage 00's synthetic-answer convention).

**Results:**
```
images with >=1 scoreable QA pair: 40,474 (of 40,474 images with any question)
train images  : 300  (599 QA pairs)
eval images   : 100  (198 QA pairs)
image-id overlap between train and eval (must be 0): 0
image download wall-clock: 555.1s
total wall-clock: 557.6s
```

**Answer-type distribution:**

| split | yes_no | number | other |
|---|---|---|---|
| train | 237 | 101 | 261 |
| eval | 80 | 25 | 93 |

**Disjointness guardrail:** checked programmatically by COCO image id (not pixel hash,
since these are real photographs, not procedurally generated) — 0 overlap, confirmed
above by the script's own assertion (`assert not (set(train_ids) & set(eval_ids))`)
plus a second post-hoc check on the written records.

**Cost:** \$0 — public dataset mirrors, no paid API calls in this stage.

**License note:** VQA v2 annotations are CC BY 4.0 (Goyal et al., 2017); COCO images
follow Flickr ToU — non-commercial research/educational use only. This mission makes
no commercial-rights claim over any image used.

**What this does not check:** whether the 32x32 downsample destroys information a
larger patch grid would keep — that is a modeling question for stage 04, not this
stage's dataset-prep concern.
