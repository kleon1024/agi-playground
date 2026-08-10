---
status: verified
level: applied
base: scratch
label: The ID-based guardrail
verified: 2026-08-06
---

# Why real photos are checked by ID, not by pixel

**Question:** [stage 03's real-photo task](../) rebuilds the leakage
guardrail for real photographs. This chapter reads the recorded dataset
build and asks why the guardrail changes form.

**Before this:** [stage 03's real-photo task](../) and its recorded build.

## The split, read

The run ([record](runs/2026-08-06-id-guardrail-read.md)) reads the recorded
numbers:

| number | value |
|---|---|
| train images | 300 (599 QA pairs) |
| eval images | 100 (198 QA pairs) |
| image-id overlap | 0 (must be 0) |

## Two readings

**Real photographs essentially never collide by pixel hash, so the
guardrail moves to image ID.** Procedural images could render identically
under different seeds — that was stage 00's 116-collision lesson. Real
photographs are unique artifacts; the realistic leakage is the same COCO
image appearing in both splits by id, not a pixel collision. The guardrail
switches from hashing pixels to checking COCO image ids.

**The 0-overlap number is checked, not assumed.** The run records
"image-id overlap between train and eval (must be 0): 0" — the same
discipline as stage 00's pixel check, applied to the id space where real
photos can actually leak. The form changed, the invariant did not: no eval
instance may be a train instance under the representation that can
collide.

## The fix and its trade

The fix is moving the guardrail key from pixel hash to image id. The
procedural stage checked pixels because rendered images could collide
under different seeds (the recorded 116-collision lesson); real
photographs essentially never collide byte-for-byte, so the check that
matters is identity — the same COCO image appearing in both splits under a
different annotation. The recorded build asserts 0 overlap and re-checks
the written records, so the invariant "no eval instance is a train
instance" survives the key change. The trade is that each key catches the
leak its data type actually has and is blind to the other: a pixel hash
would miss an id overlap, and an id check cannot catch a near-duplicate
scene that was cropped or re-encoded into a new id. For real photographs
the id check is the stronger one, because identity is where the realistic
leak lives — but the chapter's point is that the guardrail is data-
appropriate, not universally sufficient: a team working with edited or
derived images would need a third key, not this one.

## Who owns the loop

- **The data pipeline** owns the guardrail key and its timing: the choice
  of id over pixel hash is a pipeline decision, and the overlap is
  asserted before the files are written, not after a leak shows up in the
  eval numbers.
- **The evaluation owner** owns the invariant the key serves: no eval
  instance may be a train instance under the representation that can
  collide, and the form of that check is allowed to change with the data
  type without weakening the invariant.
- **The data QA step** owns the post-hoc re-check on the written records,
  which is what turns the asserted 0 into a verified 0 rather than an
  assumption.

## Evidence boundary

The recorded real-photo build (300/100 from VQA v2's 40,474-image
validation pool, one seed). It reads that artifact; it does not re-fetch
and the zero-overlap characterizes this split construction.

## Check your mental model

Answer each before opening it.

**1. Why is pixel-hash disjointness the wrong check for real photos?**

<details>
<summary>Answer</summary>

Because real photographs essentially never produce identical pixel hashes
— each photo is a unique artifact, unlike procedurally-rendered images
that can collide under different seeds. The realistic leak for real data
is the same image appearing in both splits under a different id or
annotation, which pixel hashing would miss. The guardrail follows the
leak's actual mechanism.

</details>

**2. What is the invariant that survives the guardrail change?**

<details>
<summary>Answer</summary>

No eval instance may be a train instance. Stage 00 checked it in pixel
space because rendered images collide there; stage 03 checks it in id
space because real photos leak there. The representation that can collide
changes with the data type, and the guardrail is chosen to match — the
invariant is the same, the check is data-appropriate.

</details>

## Next

Back to [stage 03](../), or to
[the real-photo guardrail: image ID, not pixel hash](../the-real-photo-guardrail/)
which reads the same stage's guardrail design.
