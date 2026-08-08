---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Real-photo outcome report
---

# Does the real-photo vision pathway hold up against a hosted VLM, not just a text-only guess?

**Before this:** [stage 04](../04-real-photo-vision-fusion/) retrained stage
01's exact architecture on stage 03's real photographs and found the vision
pathway beats text-only by a narrow but real margin (+0.0152, larger than
vision's own 0.0101 seed spread). That settles only half of mission 05's
acceptance bar. This stage adds the second, harder comparison: the same
hosted VLM API stage 02 already used, called on the identical real-photo
eval set, then computes the mission's verdict mechanically -- `MET` or `NOT
MET`, never a softened paraphrase.

## The result

```
vision      mean=0.2374  spread=0.0101  per_seed=[0.2374, 0.2424, 0.2323]
text_only   mean=0.2222  per_seed=[0.2121, 0.1919, 0.2626]
hosted API: 0.4596  (198 questions, single run -- no seeds, a fixed API)

vs text-only: margin +0.0152 vs spread 0.0101 -> beats the noise band
vs hosted API: margin -0.2222 vs spread 0.0101 -> does NOT beat the noise band

VERDICT: NOT MET
```

One arm, two comparisons, opposite verdicts. Switch between them and the vision
row does not move — only what it is held against:

<!-- interactive: RealPhotoMargins -->

`gpt-4o-mini`, called with no training at all, nearly doubles the from-scratch
858K-parameter model's accuracy on real photographs. This is not a surprise
in direction -- a production hosted model trained on internet-scale
image-text data should beat an 858K-parameter model trained on 300 images --
but mission 05 declared the bar in advance specifically so that "of course it
would win" could not quietly replace an actual measurement.

## Where the gap concentrates

```
                number    other    yes_no
hosted API      24.0%     36.6%    63.8%
```

Yes/no questions are the hosted API's strongest category by a wide margin --
consistent with a real 50/50-ish prior making that category easiest for any
model, from-scratch or hosted, to score well on by chance-adjacent guessing.
Free-form ("other") and exact-numeric answers are where visual grounding
actually has to do work, and both sit far below the yes/no rate even for the
hosted model, suggesting VQA v2's harder categories remain hard in general,
not just for this mission's small model.

## Cost

```
hosted API: $0.2534 total over 198 questions ($0.00128/question)
vision + text-only training: $0 (local CPU, 497.3s wall-clock, stage 04)
```

Same per-question rate stage 02 measured on the synthetic set
(\$0.00128/question) -- the hosted API's pricing does not depend on whether
the images are synthetic renders or real photographs, only on token count,
which stayed essentially fixed (fixed prompt template, fixed 32x32 image
size).

## The fix and its trade

The fix is completing the mission's acceptance bar: the real-photo chain
had measured the vision pathway against the text-only control (stage 04),
and this stage adds the second, harder comparison — the hosted VLM API on
the identical 198-question eval set — then lets `report.py` compute the
verdict mechanically, refusing to print without both artifacts. The trade
is that the completed bar confirms the synthetic verdict on real data
instead of softening it: the API (0.4596) nearly doubles the self-trained
pathway (0.2374), a -0.2222 margin far beyond any spread, so the mission is
NOT MET on real photographs exactly as on synthetic shapes. The fix does
not flatten the result into one number: the per-type read (yes/no 0.638,
other 0.366, number 0.240) shows the API's edge is answer-type-shaped —
strongest where a real 50/50-ish prior makes the category easiest for any
model, weakest where visual counting actually has to work — which is the
evidence for where a future build could compete (number questions, where
the API is closest to the self-trained arms) instead of head-on. What the
verdict preserves is the reuse claim: stage 01's pathway learned a real,
if narrow, signal from real photographs with zero code changes, and the
build-vs-buy answer — buy, not build, at this scale — is now confirmed on
real data rather than only on rendered shapes. The yes/no prior and the
answer-type distribution this read leans on are VQA v2's own structure
(Goyal et al., 2017).

## Who owns the loop

- **The report owner** owns the verdict contract: the mechanical MET/NOT
  MET read, the refusal to print without stage 04's results and this
  stage's raw log, and the verdict-plus-diagnosis pair (NOT MET overall,
  answer-type-shaped gap) stated together.
- **The model team** owns the reuse claim the verdict does not undo: the
  zero-code-change path from stage 01 to stage 04 is the evidence, and the
  team owns stating that the claim holds on real data even where the
  accuracy does not.
- **The stakeholder** owns the buy-not-build decision the report feeds; the
  per-type read is the part of the report that tells them where a
  different build could still find ground.
- **The evaluation owner** owns the per-arm spread read and the cost
  record (\$0.2534 over 198 questions from the bill), the two numbers the
  verdict's noise band and its economics come from.

## Run it

```bash
cd 01-language-model/vision/05-real-photo-report/core
export OPENROUTER_API_KEY=...
uv run python call_hosted_api.py --resume   # ~6 min, ~$0.25, 198 real hosted calls
uv run python report.py                     # combines stage 04's results + this call into the verdict above
```

`report.py` refuses to print a verdict if either upstream artifact (stage
04's `real-photo-results.json` or this stage's `hosted-api-raw.jsonl`) is
missing -- it prints `CANNOT DETERMINE` and names the missing file, the same
discipline stage 02's `report.py` established. Full trace:
[`runs/2026-08-01-real-photo-report.md`](runs/2026-08-01-real-photo-report.md).

## What this does not establish

Only one hosted model (`openai/gpt-4o-mini`) and one prompt were tried on the
real-photo set, same as stage 02's synthetic-set limitation. 300 training /
100 eval images is a small slice of VQA v2's roughly 40,000-image validation
set -- this result says nothing about how the vision pathway would fare with
more real-photo training data, only that at this budget it does not close
the gap to a hosted model. Nothing here says anything about video, audio, or
frontier-scale vision-language capability; full boundary in
[`../mission.yaml`](../mission.yaml)'s `does_not_prove`.

## What a `NOT MET` verdict still established

The reuse claim held on real data, not just synthetic: stage 01's patch
embedding, fusion mask, and training loop needed zero code changes to learn a
real (if narrow) signal from real photographs, and that signal's direction
matches the synthetic-shapes result from stage 01/02. The build-vs-buy answer
mission 05 set out to test is the same on real photographs as it was on
synthetic shapes -- buy, not build, at this scale -- which is now confirmed
on real data instead of only on rendered shapes.

A detour from here: [the build-vs-buy verdict, on real
photos](when-the-api-still-wins/) — the hosted API's accuracy recomputed
from the raw log (0.460, matching the recorded 0.4596) and the three-arm
comparison read: real photos do not change the NOT MET answer, and the
API's edge is answer-type-shaped.

Another detour: [the API's edge is shaped like the answer type](the-answer-type-shaped-edge/) — the log recomputed: yes/no 0.637, other 0.366, number 0.240, so a future build could compete where the API is weakest.
