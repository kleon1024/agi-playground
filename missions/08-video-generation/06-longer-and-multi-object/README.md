---
status: verified
level: applied
base: scratch
verified: 2026-08-05
label: Both axes at once
---

# Two hard things at once: do they add up, or does one of them dominate?

Stage 04 doubled the clip to 16 frames and kept one object. Stage 05 added a
second occluding object and kept 8 frames. Both cleared the frame-repeat
baseline, and both ended by saying the combination was untested.

That leaves a question neither could answer. If longer clips cost a little and
two objects cost a lot, a reader still cannot tell whether running both at once
costs roughly the sum, or something worse. This stage runs the fourth corner —
**16 frames and 2 objects** — so all four cells of the grid exist and the
difference between any two of them isolates one change.

**Before this:** [longer sequences](../04-longer-sequences/) and
[multi-object scenes](../05-multi-object/), for the two single-axis results this
one is measured against. Same codec, same sequence model, same baseline.

## The grid, filled in

Every cell is 3 seeds, 800 training clips, 150 held-out clips, 800 codec steps,
400 LM steps, and half the clip given as a prompt. Reconstruction MSE is
measured on the frames the model had to produce.

| Frames | Objects | Stage | MSE (3 seeds) | Frame-repeat baseline | Exact-match |
|---|---|---|---|---|---|
| 8 | 1 | [02](../02-generation-model/) | 0.0804–0.0882 | 0.1281 | 6.67–22.00% |
| 16 | 1 | [04](../04-longer-sequences/) | 0.0818–0.0892 | 0.1185 | 8.67–33.33% |
| 8 | 2 | [05](../05-multi-object/) | 0.1429–0.1533 | 0.2193 | 0.67–28.67% |
| **16** | **2** | **this stage** | **0.1375–0.1456** | **0.1998** | **0.00–0.67%** |

Read the MSE column down. Doubling the frames barely moves it (0.0804–0.0882 to
0.0818–0.0892). Adding the second object nearly doubles it (0.0804–0.0882 to
0.1429–0.1533). Doing both lands at 0.1375–0.1456 — **inside the range the
second object alone already cost**, not on top of it.

In pixel space the two axes do not add. Object count is the whole cost, and
frame count is close to free once the codec is per-frame.

## Where they do compound

The exact-match column tells the opposite story. It is the fraction of held-out
clips where every predicted token matches the codec's own encoding of the true
future, and it goes to the floor: **0.00%, 0.67%, 0.67%** across the three
seeds. One clip in 150, twice, and none at all on the third.

Part of that is a harder target by construction. At 16 frames the model predicts
8 tokens and all 8 must match; at 8 frames it predicts 4. But stage 04 also
predicted 8 tokens, at one object, and reached 33.33% on its best seed — so the
longer target is not what emptied this column. Two objects sharing one 64-entry
per-frame token, over a target twice as long, is.

[Stage 04's length-scaling widget](../04-longer-sequences/#the-result)
is where to drive that variable directly; this stage adds the second object on
top of the longest setting it offers.

## The variance that vanished

Stage 05 reported an unexplained finding: exact-match ranged 0.67% to 28.67%
across seeds while MSE stayed tight (0.1429 to 0.1533). Stage 04 saw the same
thing — 8.67% to 33.33%, a 24.6-point spread, on tightly clustered MSE.

Here the spread is 0.67 points. The metric did not become more reliable; it hit
its floor, and a metric pinned at zero cannot vary. That reframes the earlier
observation: exact-match was not noisy *because* the task was hard, it was noisy
because it sat in the middle of its range, where a handful of clips crossing a
strict all-or-nothing threshold moves the percentage a long way. Push the task
until the rate is near zero and the variance goes with it.

MSE keeps reporting throughout, because it degrades smoothly rather than
thresholding. That is the difference between the two metrics, made visible by
running the task past the point where one of them still works.

## What the oracle says about who is at fault

Each run also encodes the true future frames with the trained codec and decodes
them straight back — the `oracle_tokens` MSE, the best any sequence model could
do with this codec. At 0.1245, 0.1179, and 0.1455 against the model's 0.1391,
0.1375, and 0.1456, the gap between the model and its own ceiling is small, and
on seed 2 it is 0.0001.

The sequence model is not the binding constraint. It is very nearly extracting
everything the tokenizer left in the token stream, and the token stream is what
is missing information about two overlapping shapes. This is the same
conclusion stages 04 and 05 each reached separately, now measured where both
difficulties are present at once.

## What ran

```bash
cd missions/08-video-generation/06-longer-and-multi-object/core
uv run --group torch python train_longer_and_multi_object.py --seed 0
uv run --group torch python train_longer_and_multi_object.py --seed 1
uv run --group torch python train_longer_and_multi_object.py --seed 2
```

Apple silicon laptop, CPU only, run 2026-08-05, seeds sequential. Total
wall-clock 401.5s, 494.3s, and 408.3s against the declared 1800s ceiling —
22–27% used, so `CEILING_EXCEEDED` was never close. \$0 marginal cost. The
occlusion is real and measured rather than assumed: 82.6% of training clips have
at least one frame with overlapping pixels, mean overlap 0.96% of the frame.
Full numbers in
[`runs/2026-08-05-longer-and-multi-object.md`](runs/2026-08-05-longer-and-multi-object.md).

## The bug this stage had to not have

Five modules hold five independent copies of the frame count, because
`from generate_video_dataset import N_FRAMES` copies the *value* at import time
rather than creating a live view of the exporting module's global. Setting the
source to 16 after any of them has been imported changes nothing for that
module.

The failure mode is not a crash. `load_clips` reshapes a flat pixel array using
its own copy of the frame count, so a disagreement would silently reinterpret
16-frame clips as 8-frame tensors and train on corrupted data that looks
perfectly well-formed. The script patches the source before the first import
that copies from it, patches stage 05's own copy as well, and then asserts all
five agree — recorded in the run record as `frame_count_bindings`, all five
reading 16.

## What this stage does not establish

Nothing about 3 or more objects, or about clips longer than 16 frames — the grid
has four corners, not a surface. The occlusion here is naturally occurring and
modest (0.96% of pixels on average, 7.1% at the worst clip), not a heavy-occlusion
stress test. Nothing about real video, camera motion, or any footage this
mission's own code did not procedurally generate. And the exact-match floor is a
statement about this codec at 64 codebook entries and one token per frame; a
wider codebook or more tokens per frame is a different experiment, untried here.

The MSE non-additivity is measured on three seeds at one setting per corner. It
is a comparison between four measured points, not a scaling law.

## Check your mental model

1. MSE at 16 frames and 2 objects is no worse than at 8 frames and 2 objects.
   Why does that not mean longer clips are free?

<details>
<summary>Answer</summary>

Because MSE is averaged over the frames the model produced, and at 16 frames it
produced 8 of them rather than 4. An average that holds steady over twice as
many predicted frames is a *per-frame* result, not a per-clip one — the model is
doing the same quality of work on each frame, twice as many times. What is free
is the per-frame cost, and only because the codec is per-frame: it encodes each
frame independently, so a longer clip is more work of the same kind rather than
harder work. The sequence model's attention cost does grow with length, and at
16 frames that is 17 tokens rather than 9 — still small enough not to show up in
this stage's wall-clock, which is dominated by codec training.

</details>

2. Exact-match fell to near zero and its seed-to-seed spread fell with it. Why
   is the second fact not evidence that the measurement got more reliable?

<details>
<summary>Answer</summary>

Because a metric bounded below at zero cannot vary once it is sitting on that
bound. The spread collapsed for the same reason the value did — there is no room
underneath. Reliability would mean the metric still distinguishes between
systems and happens to do so consistently; this metric has stopped
distinguishing anything, since a model that is slightly better and a model that
is much worse both score approximately 0%. The tight spread is a symptom of
saturation, and reading it as precision would be exactly backwards.

</details>

3. The model's MSE is within 0.0001 of the oracle MSE on seed 2. What would you
   change to improve this system, and what would be a waste of effort?

<details>
<summary>Answer</summary>

Change the tokenizer. The oracle is the MSE you would get from a *perfect*
sequence model — one that predicts the codec's own encoding of the true future
exactly — so the gap between model and oracle is all the room a better sequence
model has to work with. On seed 2 that room is 0.0001. Training the LM longer,
widening it, or improving its sampling can recover at most that, and would be a
waste. Everything else, all 0.1455 of it, is information the codec threw away
when it compressed two overlapping shapes into one 64-entry token per frame.
More codebook entries, more tokens per frame, or a codec that sees more than one
frame at a time are the changes with headroom behind them.

</details>

## Next

This closes both follow-on axes `mission.yaml` named, alone and together. The
open question the grid now points at is the tokenizer's capacity, which every
corner of it independently identified as the binding constraint — and which no
stage in this mission has yet varied. Return to
[the mission report](../03-report/) for what the whole chain does and does not
license you to claim.
