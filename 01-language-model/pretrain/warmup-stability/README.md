---
status: verified
level: applied
base: scratch
verified: 2026-08-02
label: Warmup stability
---

# Does a learning-rate warmup close the seed-2 collapse?

**Question:** [stage 01](../01-vision-fusion/)'s vision pathway beat the
text-only baseline on 2 of 3 seeds by a wide margin, but the third seed
collapsed below every text-only seed -- a single failure large enough that
the stage's own report could not call the result a clean win. Stage 01's
diagnosis pointed at one cause: the failed seed's train loss sat close to
text-only's own losses, while the other two vision seeds fit substantially
better, under a fixed, un-scheduled learning rate used for all six of that
stage's runs. Stage 01 named a warmup or schedule as untested future work,
not a finding. This stage tests it.

**The artifact this stage produces** is the same 3-seed vision-pathway run
stage 01 ran, with exactly one mechanism changed: a linear LR warmup over
the first 10% of optimizer steps, then held constant at stage 01's original
rate for the rest of training.

**Before this:** [stage 01](../01-vision-fusion/) measured the collapse this
stage tries to fix and named the untested hypothesis.

## What is reused, and what is new

`VisionLanguageTransformer`, `Config`, `Tokenizer`, the dataset loader, the
batch builder, and the evaluation loop are all imported directly from
[stage 01](../01-vision-fusion/)'s `core/` -- nothing there was
reimplemented. Epochs (30), batch size (64), optimizer (AdamW), base learning
rate (3e-3), and all 3 seeds (0, 1, 2) are identical to stage 01's run, so
the two results are directly comparable.

The only new code is in `core/train_warmup.py`: a linear warmup schedule
applied to the optimizer's learning rate for the first
`warmup_frac = 0.10` of total steps (0 -> 3e-3 across steps 0-185 of 1,860
total, at this stage's step count), held constant at 3e-3 after that --
the standard, simplest fix, and the one stage 01's own diagnosis pointed at.
Text-only was not re-run: the collapse and the hypothesis under test are
specific to the vision pathway.

## The result: warmup closes the collapse

```
                       seed 0    seed 1    seed 2    mean     spread
stage 01 (no warmup)   0.5128    0.5153    0.2844    0.4375   0.2309
this stage (warmup)    0.4707    0.5242    0.4962    0.4970   0.0536
```

Seed 2 moves from 0.2844 -- below every text-only seed -- to 0.4962, in line
with the other two warmup seeds. Spread across seeds drops from 0.2309 to
0.0536, more than a 4x tightening. All three warmup seeds now individually
beat text-only's mean (0.3270) by a margin several times text-only's own
0.0459 spread -- not just the mean moving while one seed stays bad, all
three moved into a tight, clearly-winning band.

<!-- interactive: WarmupSeedStability -->

Final train loss tells a more complicated story: seed 2's warmup train loss
(0.3406) is now the *lowest* of the three runs, exactly reversed from stage
01, where seed 2's *high* train loss (0.6853) was the signal it never left a
poorly-fit region. That reversal is consistent with the collapse being an
optimization-trajectory problem the warmup fixed, not evidence that warmup
changed what "fit" means for this task. Full per-seed numbers, environment,
and reasoning are in
[the run record](runs/2026-08-02-warmup-vs-stage01.md).

**Verdict:** the warmup hypothesis is confirmed on this run -- a single
changed mechanism (10%-of-steps linear LR warmup), same architecture, same
data, same seeds, closed the seed-2 collapse and tightened spread by more
than 4x. This does not retroactively make stage 01's own reported result
wrong; it answers the specific open question stage 01 named as future work.

## The fix and its trade

The fix is a linear LR warmup over the first 10% of optimizer steps (0 ->
3e-3 across steps 0-185 of 1,860), applied as the single changed mechanism
to stage 01's exact recipe. The measured effect: seed 2 moves from 0.2844 —
below every text-only seed — to 0.4962; eval spread drops from 0.2309 to
0.0536 (more than 4x); the mean rises 0.4375 to 0.4970; and all three
warmup seeds individually beat text-only's mean by several times text-only's
own 0.0459 spread. The mechanism the numbers support is an
optimization-trajectory one: a fixed high LR at step 0 lets one seed's
early updates push it into a degenerate region before any useful feature
exists, and a warmup keeps the first 185 steps small enough for the pathway
to survive initialization — the standard empirical fix for exactly this
collapse class, documented when raising batch size or LR (Goyal et al.,
2017) and present in transformer training from the original schedule
(Vaswani et al., 2017). The trade is priced per attempt: one fraction (10%)
was tried, not swept, so the result claims this fraction closed this
specific collapse, not that 10% is optimal; text-only was not re-run, so
nothing is claimed about its spread under warmup; and the final train-loss
spread stayed 0.2302, which is the proof of the mechanism — warmup fixed
the path divergence, not the seed variance itself.

## Who owns the loop

- **The model team** owns the training recipe, the hypothesis, and the
  single-mechanism discipline: the warmup was the one thing changed, which
  is what makes the before/after comparison attributable; the team also
  owns the decision to test one fraction rather than silently sweep for
  the best number.
- **The evaluation owner** owns the per-seed before/after read and the
  spread convention: the 4x tightening and the all-three-seeds-in-band
  claim come from the recorded JSON, not from a headline.
- **The report owner** owns the verdict's scope: stage 01's reported
  result stands as recorded (this stage answers its named open question),
  and the mission's build-vs-buy NOT MET is untouched by a stability fix
  on the self-trained arm.

## What this stage does not establish

One warmup fraction (10% of steps) was tried, not swept -- this result does
not claim 10% is optimal, only that it closed this specific collapse; a
different fraction might work better, worse, or not at all. Text-only was
not re-run with warmup, so this stage says nothing about whether warmup
would tighten or loosen text-only's own already-small 0.0459 spread. Only 3
seeds were tried on each side, the same count stage 01 used -- a pattern
across 3 seeds is not an exhaustive stability guarantee; a 4th or 5th seed
could in principle reopen a gap these 3 do not show. Stage 01's own scope
boundary is unchanged: the eval set is still stage 00's synthetic,
disjoint-checked set, and stage 02's hosted-API baseline comparison is
untouched by this result.

## Run it

```bash
cd 01-language-model/vision/06-warmup-stability/core
uv run --group torch python train_warmup.py --seeds 3 --epochs 30 --batch-size 64
```

CPU only, ~1060s (17.7 min) for 3 seeds. Full run record:
[`runs/2026-08-02-warmup-vs-stage01.md`](runs/2026-08-02-warmup-vs-stage01.md),
raw numbers in
[`runs/warmup-results.json`](runs/warmup-results.json).

**Next:** stage 02 adds the hosted-VLM-API baseline stage 01 deferred; this
stage's tightened, seed-stable vision result is the pathway stage 02
compares against.

A detour from here: [what the warmup changed, and what it did
not](when-warmup-closed-the-collapse/) — the eval spread fell 0.2309 to
0.0536 while train-loss spread stayed 0.2302: the collapse was an
optimization-path divergence, not an irreducible seed difference.

Another detour: [the seed-2 outlier, closed by a training-dynamics fix](the-collapse-that-warmup-closed/) — the recorded before/after read: spread 0.2309 -> 0.0536 and mean 0.4375 -> 0.4970, with model, data, and seeds unchanged.
