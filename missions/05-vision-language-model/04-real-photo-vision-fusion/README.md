---
status: verified
level: applied
base: 01-vision-fusion
verified: 2026-08-01
label: Real-photo vision fusion
---

# Does the same vision pathway, unchanged, still separate from a text-only guess on real photographs?

**Question:** stage 01 built a real patch-embedding module and fusion path
and found a partial result on synthetic shapes — two of three seeds beat
text-only, but the margin was smaller than vision's own seed spread. Does
that same architecture, with zero code changes, show a real (if different)
signal once the images are real photographs instead of rendered shapes?

**The artifact this stage produces** is three trained seeds each of the
vision pathway and the text-only baseline, retrained on stage 03's 300
real-photo training images, evaluated on its 100-image held-out set.

**Before this:** [stage 03](../03-real-photo-task/), which supplies the
real-photo data this stage trains on, in the exact schema stage 00's
synthetic data used.

## What changes, and what does not

Nothing in `vlm_model.py` or `tokenizer.py` changes. `Config`,
`VisionLanguageTransformer`, and `Tokenizer` are imported directly from
[stage 01](../01-vision-fusion/)'s `core/` — this stage's own `train.py`
imports stage 01's `train.py` functions (`build_examples`, `make_batch`,
`evaluate`, `train_one`) unchanged too, and only points `DATA_DIR` at stage
03's real-photo manifests instead of stage 00's synthetic ones. The only new
code is the entry point and the 30-minute declared-ceiling check
`mission.yaml`'s stages 03-05 extension requires.

The local 4090 lane named in the mission's cost_budget was not reachable
from this run's environment (`torch.cuda.is_available()` returned `False`,
no route to the GPU host) — training fell back to CPU, as `mission.yaml`
allows, and is disclosed here rather than assumed away.

## The result

```
vision     eval exact-match: mean=0.2374 spread=0.0101 per_seed=[0.2374, 0.2424, 0.2323]
text_only  eval exact-match: mean=0.2222 spread=0.0707 per_seed=[0.2121, 0.1919, 0.2626]
wall-clock: 497.3s (8.3 min), CPU, well inside the 30-minute ceiling
```

Margin over text-only is **+0.0152**, larger than vision's own seed-to-seed
spread (0.0101) — a real, narrow margin by this mission's own rule. The
seed-stability pattern flips from stage 01: there, vision was the noisier
pathway (one seed collapsed entirely); here, text-only is far noisier
(spread 0.0707 vs vision's 0.0101). A likely reason, not yet confirmed: VQA
v2's real answer distribution has a strong majority-answer skew per question
type (many questions have an obvious "yes" or a common short answer), so a
blind text-only guess's accuracy depends heavily on which random seed's
weights happen to land near that skew, while the image-conditioned model has
an actual signal to anchor on across seeds.

## What this stage does not settle

Whether this narrow margin survives against the hosted VLM API baseline —
`mission.yaml`'s acceptance bar requires beating *both* baselines, and this
stage only trains and evaluates the self-trained half. Vocabulary size (1,014
real words vs. stage 01's small closed synthetic vocabulary) confirms the
tokenizer itself needed no change to handle real, open-ended VQA text, but
says nothing about whether a larger vocabulary changes what the model can
still learn to condition on at this parameter count and dataset size. Full
boundary in [`../mission.yaml`](../mission.yaml)'s `does_not_prove`.

## Run it

```bash
cd core
uv run --group torch python train.py --seeds 3
```

CPU (no CUDA GPU reachable this run), 3 seeds each of vision and text-only,
about 8.3 minutes total. Full trace:
[`runs/2026-08-01-real-photo-vision-vs-text-only.md`](runs/2026-08-01-real-photo-vision-vs-text-only.md).

**Next:** stage 05 adds the hosted VLM API baseline on this same real-photo
eval set and reports whether the mission's full acceptance bar is met.
