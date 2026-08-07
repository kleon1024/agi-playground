---
status: verified
level: applied
base: scratch
label: When the ID space grows
verified: 2026-08-07
---

# The ID space grows and decode accuracy falls

**Question:** [stage 35's generative retrieval](../) emits document IDs.
This chapter reads the executed scaling sweep and asks what the ID
vocabulary costs.

**Before this:** [stage 35 — generative retrieval](../) and its executed
beam decode.

## The scaling curve, executed

The run ([record](runs/2026-08-07-id-space-grows-read.md)) sweeps corpus
size:

| corpus size | beam accuracy |
|---|---:|
| 100 docs | 0.98 |
| 1,000 docs | 0.93 |
| 10,000 docs | 0.84 |
| 100,000 docs | 0.71 |

## The reading

The generator must emit exact IDs, and the odds of a decode error grow
with the vocabulary — accuracy falls from 0.98 at 100 docs to 0.71 at
100,000. Generative retrieval's recall is a decode property, not an
index property: the beam can only be as accurate as the model's ability
to spell the right ID, and that ability decays as the set of IDs grows.
The scaling curve is the frontier constraint — the approach that removes
the index brings a decode bottleneck in its place.

## Evidence boundary

The executed sweep over a declared accuracy model (illustrative,
deterministic, assumed decode-error rates). It demonstrates the shape;
real generative retrieval needs the trained model and measured recall
over the actual corpus at production size.

## Check your mental model

Answer each before opening it.

**1. Why does a bigger corpus hurt a generator more than an index?**

<details>
<summary>Answer</summary>

Because an index searches, while a generator must recall the exact
string. A bigger corpus barely changes a scan's answer — the index
looks up whatever is there. A generator has to emit the right ID from a
larger set, so the probability of a decode error rises with the
vocabulary, exactly as the executed curve shows: 0.98 at 100 docs, 0.71
at 100,000.

</details>

**2. What does "recall is a decode property" mean operationally?**

<details>
<summary>Answer</summary>

That recall is set by the generator's decoding, not by anything the
index could fix. You cannot add a bigger index or a faster scan to
recover recall — you can only improve the decode, shrink the ID space,
or accept the accuracy loss. The frontier design has to price the ID
space itself, which is a constraint the index-based funnel never faced.

</details>

## Next

Back to [stage 35](../). The
[hallucination detour](../when-the-generator-hallucinates/) shows the
second decode failure: the generator emitting an ID that does not exist
at all.
