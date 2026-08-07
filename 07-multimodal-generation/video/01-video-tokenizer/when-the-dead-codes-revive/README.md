---
status: verified
level: applied
base: scratch
label: When the dead codes revive
verified: 2026-08-06
---

# Three collapses, one revive mechanism, 63/64 codes

**Question:** [stage 01's video tokenizer](../) recorded three failed
training attempts before the working codec. This chapter reads the final
run and the collapse history and asks what kept the codebook alive.

**Before this:** [stage 01's video tokenizer](../) and its recorded run.

## The final health, read

The run ([record](runs/2026-08-06-revive-read.md)) reads the recorded
JSON:

| number | value |
|---|---|
| eval MSE | 0.07875 (vs background 0.09437 / mean-frame 0.08580) |
| codes used | 63/64 |
| entropy ratio | 0.912 |
| dead codes revived | 158 (every 20 steps) |

## Two readings

**Three collapses preceded this, each with its own diagnostic.** The first
attempts plateaued at the flat-background baseline with 1/64 codes —
textbook VQ codebook collapse, where the nearest-neighbor argmin locks
onto one index. The decoder saturation bug was the second. The run keeps
all three because they are the actual lesson: a codec training pipeline
fails in recognizable patterns, and each needs a specific fix.

**The revive mechanism is what kept the codebook at 63/64.** The final
run's 158 revived codes are the maintenance loop working — dead entries
reinitialized every 20 steps, keeping utilization high while the encoder
and decoder stabilize. Without the revive, the codebook would have
collapsed again; with it, the tokenizer reaches near-full entropy (0.912)
and beats both baselines.

## Evidence boundary

The recorded video-codec run (one seed, 800 steps, one revive schedule).
It reads that artifact; it does not re-train and the collapse history is
the stage's own recorded attempts.

## Check your mental model

Answer each before opening it.

**1. Why does the codebook collapse to 1/64 codes?**

<details>
<summary>Answer</summary>

Because of initialization scale mismatch. The codebook entries start in a
tiny ball around the origin (uniform(-1/64, 1/64)), while a randomly-
initialized encoder's outputs land far outside at a larger scale — so
every entry is nearly equidistant from any output and the nearest-neighbor
argmin locks onto one index. Raising the LR fixed mission 07's silence
minimum but not this; the collapse has its own mechanism and its own fix.

</details>

**2. What does 158 revived codes tell you about the mechanism?**

<details>
<summary>Answer</summary>

That the revive is load-bearing, not decorative. 158 dead codes were
detected and reinitialized across the run — without the mechanism, those
entries would have stayed unused and the codebook would have operated at
reduced capacity. The revive count is the evidence that the maintenance
loop did real work, and the 63/64 final utilization is its result.

</details>

## Next

Back to [stage 01](../), or to
[what is the discrete thing a video model conditions on](../what-a-video-token-is/)
which reads the same stage's token contract.
