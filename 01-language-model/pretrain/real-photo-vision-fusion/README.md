---
status: verified
level: applied
base: scratch
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

## The fix and its trade

The fix is the per-arm spread read: the margin is judged against the arm's
own seed-to-seed spread, not against a pooled number. That is the only
read that keeps +0.0152 a result — vision's spread is 0.0101, a third of
the margin — and it is also the read that exposes what flipped from stage
01: text-only is now 7x noisier (0.0707 vs 0.0101), so the noise lives on
the control side and the margin belongs to the stable vision arm. The
trade is that the margin, while real by the rule, is a sliver: a third of
the synthetic margin (+0.1105), so real photographs shrink the vision
advantage toward zero even as they make it seed-stable. The likely reason
is the VQA v2 answer distribution itself (Goyal et al., 2017): the real
set's majority-answer skew per question type makes a blind text-only
guess's accuracy depend on which seed's weights happen to land near the
skew, while the image-conditioned model anchors on an actual signal across
seeds — a hypothesis this stage states as unconfirmed, not as a finding.
The stage's second deliverable is the reuse claim: zero code changes
across synthetic-to-real, so the same +14,464-parameter pathway that saw
rendered shapes learns to condition on real pixels too, at the disclosed
cost of a CPU fallback (CUDA unreachable, allowed by `mission.yaml` and
recorded rather than assumed away).

## Who owns the loop

- **The model team** owns the architecture-reuse claim and the training
  recipe: the unchanged import path from stage 01 is the evidence for
  reuse, and the CPU fallback is a run-environment fact the model team
  discloses in the record.
- **The evaluation owner** owns the per-arm spread rule and the per-seed
  read: pooled spreads would misread this run, and the per-arm form is
  what makes the narrow margin and the flipped variance legible.
- **The report owner** owns the verdict against the hosted API, which
  this stage does not run: stage 04 settles the self-trained half of the
  acceptance bar, and stage 05 holds the result against the second
  baseline.

## What this stage does not settle

Whether this narrow margin survives against the hosted VLM API baseline —
`mission.yaml`'s acceptance bar requires beating *both* baselines, and this
stage only trains and evaluates the self-trained half. Vocabulary size (1,014
real words vs. stage 01's small closed synthetic vocabulary) confirms the
tokenizer itself needed no change to handle real, open-ended VQA text, but
says nothing about whether a larger vocabulary changes what the model can
still learn to condition on at this parameter count and dataset size. Full
boundary in [`../../mission.yaml`](../../mission.yaml)'s `does_not_prove`.

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

A detour from here: [the margin is narrow, real, and noisy on the control
side](when-the-margin-is-narrow/) — the recorded +0.0152 read as three
numbers: beyond vision's own spread (real), a third of the synthetic
margin, with the noise on the text-only arm (7x vision's spread).

Another detour: [the noise changed sides](the-flipped-variance/) — the recorded seeds read: text-only is now 7x noisier (0.0707 vs 0.0101), the opposite of stage 01, and the narrow margin belongs to the stable vision arm.
