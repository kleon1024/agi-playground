---
status: verified
level: applied
base: scratch
label: When the seed is the answer
verified: 2026-08-06
---

# The seed is the answer key

**Question:** [stage 00](../) builds clips whose seed fully determines the
correct frames. This chapter reads the committed fixture manifest and asks
what the contract actually is — the fields that make a completion checkable
mechanically instead of judged by eye.

**Before this:** [stage 00's synthetic video dataset](../).

## The contract, read

The run ([record](runs/2026-08-06-seed-contract.md)) reads the committed
manifest:

| clip | seed | prompt | motion | frames |
|---|---|---|---|---|
| vid-0 | 0 | a yellow square moving down_right | square, yellow, speed 2, x0 11, y0 10 | 8 |
| vid-1 | 1 | a red circle moving left | circle, red, speed 2, x0 25, y0 18 | 8 |
| vid-2 | 2 | a red circle moving down_left | circle, red, speed 2, x0 19, y0 14 | 8 |

## Two readings

**The seed is the answer key.** Every clip's correct frames are a function
of the seed: the prompt names the object and motion, the motion dict pins
the exact start position and speed, and rendering is deterministic. That is
what makes a later stage's completion scoreable — "did the model produce
the right frames" is a computed comparison against a real answer, not a
human judgment call. The same seed always renders the same frames.

**The contract is what makes the mission honest before any model exists.**
Stage 00's job is not to build an impressive dataset; it is to build one
where the answer is known and the leakage is checkable. The manifest's
explicit fields — prompt, motion, clip hash — are the audit trail: any
later stage can verify a clip was generated from its declared seed, which
is the same discipline mission 05's leakage guardrail established for
images, applied to time.

## The fix and its trade

The failure is that natural language is underspecified: "a red circle
moving left" does not say where the circle starts, how big it is, or how
fast it moves, so the prompt alone cannot be the answer key a completion
is checked against. The fix is the seed-plus-motion-dict contract — the
manifest stores seed, prompt, and the motion parameters (x0, y0, half,
speed) that pin the remaining degrees of freedom, with rendering
deterministic so the same seed always renders the same frames. The trade
is expressiveness for checkability: the dataset gives up natural-language
flexibility to buy a mechanically comparable ground truth, and if rendering
were not deterministic the answer key would not exist — a completion would
be compared against whatever rendering happened to run that time, and the
mission's central question would become unanswerable.

## Who owns this loop

- **The dataset owner** owns the manifest contract: the committed fixture
  fields (seed, prompt, motion, clip hash) are the audit trail any later
  stage verifies against, and a schema change is a contract change for the
  whole mission.
- **The evaluation owner** owns the mechanical check: "did the model
  produce the right frames" is a computed comparison against the seed's
  rendering, which is what lets a verdict rest on numbers instead of
  human judgment.
- **The model team** owns the consumption: the checkable target is the
  answer key the generation stages score against, and the determinism is
  the property their completion metric depends on.

## Evidence boundary

The committed six-clip fixture manifest (2026-07-31); it reads that artifact
and does not re-render. It demonstrates the contract on the fixtures; the
full 800/150 train/eval split is the stage's recorded run, not re-measured
here.

## Check your mental model

Answer each before opening it.

**1. Why does the prompt alone not fully determine the correct frames?**

<details>
<summary>Answer</summary>

Because natural language is underspecified. "A red circle moving left" does
not say where the circle starts, how big it is, or exactly how fast it
moves. The motion dict — x0, y0, half, speed — is what pins the remaining
degrees of freedom, and the seed is what makes the whole thing reproducible.
The manifest stores all three so a completion can be checked against the
one specific rendering the seed implies.

</details>

**2. What would break if rendering were not deterministic?**

<details>
<summary>Answer</summary>

The answer key would not exist. If the same seed could render different
frames, a later stage's prediction could not be compared against a real
answer — the comparison would be against whatever rendering happened to run
that time, and the mission's "did it produce the right frames" question
would become unanswerable. Determinism is the property that makes the whole
scoreable design work.

</details>

## Next

Back to [stage 00](../), or forward to
[stage 01 — the video tokenizer](../../01-video-tokenizer/) which turns these
frames into the discrete tokens a sequence model conditions on.
