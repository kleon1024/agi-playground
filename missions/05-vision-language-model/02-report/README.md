---
status: verified
level: applied
verified: 2026-07-31
label: Outcome report
---

# Did building the vision pathway pay for itself?

**Before this:** [stage 01](../01-vision-fusion/) trained the vision pathway
and reported it beats the text-only baseline on 2 of 3 seeds by a wide
margin, but not by more than its own seed-to-seed spread -- a partial result,
not a clean one.

This stage holds that result, plus a third real baseline never run before in
this repository, against the contract [`mission.yaml`](../mission.yaml)
declared before any of stages 00-01 existed. It does not get to soften the
comparison after seeing the numbers.

## The contract, and the answer it produces

Mission 05's acceptance bar: the vision pathway must beat **both** the
text-only baseline and a hosted VLM API, by more than its own run-to-run
spread. `core/report.py` computes this mechanically from three real,
measured inputs and prints `MET` or `NOT MET` -- never a paraphrase.

```
vision:      mean=0.4375  spread=0.2309  per_seed=[0.5128, 0.5153, 0.2844]
text-only:   mean=0.3270  per_seed=[0.3304, 0.3482, 0.3023]
hosted API:  0.8329  (784 questions, single run -- no seeds, it is a fixed API)

vs text-only: margin +0.1105 vs spread 0.2309 -> does NOT beat the noise band
vs hosted API: margin -0.3954 vs spread 0.2309 -> does NOT beat the noise band

VERDICT: NOT MET
```

The hosted API result is the sharper of the two failures: a stock call to
`openai/gpt-4o-mini`, no training, \$1.00 total, scores almost twice this
mission's self-trained vision pathway. Building the vision pathway was the
right thing to try -- stage 01 showed it can learn to use pixels -- but at
this scale, buying beat building outright. That is exactly the build-vs-buy
question mission 05's `mission.yaml` was written to answer, and the honest
answer is buy, not build.

## Where all three pathways actually fail

Acceptance also requires failure modes catalogued by category, not just one
aggregate number. `core/eval_by_category.py` re-ran stage 01's exact 3-seed
comparison keeping each question's category
(`total_count`/`shape_count`/`presence`/`shape_color`/`column_shape`); the
hosted API's per-category accuracy came from the same 784-question call.

```
                  vision       text-only     hosted API
shape_color       50.1%        27.2%         96.9%
presence          57.4%        51.4%         91.6%
column_shape      35.0%        33.3%         81.2%
shape_count       43.2%        42.2%         76.2%
total_count       37.3%        20.3%         53.0%
```

`total_count` is the hardest category for every pathway, including the
hosted API (53.0%, its own single worst category, against a 96.9% peak on
`shape_color`) -- a floor set by the task, not by any one architecture. The
per-question economics: \$1.0033 over 784 questions is \$0.00128/question; the
vision pathway's own training cost was \$0 marginal (CPU only, ~20 minutes
wall-clock) -- there is no volume of hosted-API questions that reaches that
floor, since any nonzero per-question price already exceeds it; the real
tradeoff is entirely on the accuracy axis, where hosted still leads
decisively.

<!-- interactive: CategoryBreakdown -->

Per-category accuracy breakdown rather than one aggregate score is standard
VQA evaluation practice going back to the original VQA dataset (Antol et al.,
2015), specifically because an aggregate can hide a model exploiting
question-type frequency rather than image content.

Two things stand out. First, `shape_color` is exactly where vision should
separate from text-only if it is really seeing the image -- color is not
recoverable from the question's wording -- and it does, by the widest margin
of any category (50.1% vs 27.2%). That is the clearest evidence in this
mission that the vision pathway is conditioning on pixels, not memorizing
question phrasing, even though it does not clear the mission's overall
acceptance bar. Second, `total_count` is the hardest category for every
pathway, hosted API included (53.0%, its own worst category) -- counting
shapes in a small image is evidently a hard sub-task in general here, not a
defect specific to this mission's architecture.

Digging into `total_count` further explains stage 01's seed-2 collapse
concretely rather than leaving it as an unexplained spread number: at seed 2,
both the vision and text-only models score exactly 0/100 on `total_count`,
because the model emits the end-of-sequence token immediately after the
question -- a generation collapse confined to one category, not a
degradation across the board. Full numbers and the actual empty predictions
are in
[`runs/2026-07-31-category-breakdown.md`](runs/2026-07-31-category-breakdown.md).

## Cost

```
hosted API: $1.0033 total over 784 questions ($0.00128/question)
vision + text-only training: $0 marginal cost, ~20 minutes CPU (stage 01 + this stage's re-run)
```

Run details, including the pilot call that priced the full run before it
started, in
[`runs/2026-07-31-hosted-api-pilot.md`](runs/2026-07-31-hosted-api-pilot.md)
and
[`runs/2026-07-31-hosted-api-full.md`](runs/2026-07-31-hosted-api-full.md).

## Run it

```bash
cd missions/05-vision-language-model/02-report/core
export OPENROUTER_API_KEY=...
uv run python call_hosted_api.py --resume         # ~22 min, ~$1, real hosted calls
uv run --group torch python eval_by_category.py   # ~17 min CPU, retrains stage 01's 6 runs
uv run python report.py                           # combines both into the verdict above
```

`report.py` refuses to print a verdict if either upstream artifact is
missing -- it says `CANNOT DETERMINE` and names exactly which file is
absent, the same discipline missions 02's `09-report` and 03's `05-report`
already established for this repository's report stages.

## What this does not establish

Only one hosted model (`openai/gpt-4o-mini`) and one prompt were tried; a
different model, a few-shot prompt, or a larger self-trained pathway could
plausibly change which side of the acceptance bar the result lands on. This
report does not re-run stage 01's training -- `eval_by_category.py` reruns
the identical configuration, and the two are consistent (the pooled category
counts sum to stage 01's exact reported per-seed accuracies), which is a
determinism check, not new evidence about a different setting. Nothing here
says anything about real photographs, video, audio, or frontier-scale
vision-language capability, per mission 05's own `does_not_prove`.

## What a `NOT MET` verdict still established

Mission 05 set out to test a reuse claim as much as a build-vs-buy one: that
RoPE, RMSNorm, SwiGLU, and the training loop from mission 01's decoder
transfer to a new modality with only a genuinely new input path, not a
rewrite. That claim held -- stage 01's patch embedding and fused-attention
mask are the only new mechanism this mission needed to write. A `NOT MET`
verdict on the build-vs-buy question does not undo that; it says the vision
pathway this mission built is not yet worth deploying over a \$0.00128/question
API call, which is a real, useful, and unflattering answer to a real
question a stakeholder would have asked before writing any training code.

A detour from here: [where the NOT MET verdict hides the pathway's real
signal](when-the-category-breaks-down/) — the same comparison read by
category: the vision pathway's separation from text-only concentrates where
the question cannot leak (shape_color +0.229, total_count +0.170), inside a
verdict that is still NOT MET.

Another detour: [the \$0.00128/question that decides build-vs-buy](the-economics-per-question/) — the recorded economics read: any nonzero per-question price already exceeds the \$0 training cost, so the entire tradeoff is on the accuracy axis.
