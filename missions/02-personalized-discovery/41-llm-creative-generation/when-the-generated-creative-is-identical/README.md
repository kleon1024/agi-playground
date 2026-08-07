---
status: verified
level: applied
base: scratch
label: When the generated creative is identical
verified: 2026-08-07
---

# The generated creative collapses to near-identical variants

**Question:** [stage 41's LLM creative generation](../) produces
variants for selection. This chapter reads the executed collapse check
and asks what happens when generation repeats itself.

**Before this:** [stage 41 — LLM creative generation](../) and its
executed generate-then-select model.

## The collapse, executed

The run ([record](runs/2026-08-07-generated-creative-is-identical-read.md))
normalizes three generated variants:

| variant | after normalization |
|---|---|
| Run faster, pay less | run faster pay less |
| Run faster. Pay less. | run faster pay less |
| run faster pay less | run faster pay less |

Distinct after normalization: 2.

## The reading

Three variants collapse to two distinct messages — the second is a
punctuation edit and the third a capitalization copy — so selection is
choosing between a copy and a punctuation edit. The scoring model has
nothing real to pick, and the creative space has shrunk to the mode the
generator prefers. LLM generation needs a diversity control
(temperature, repetition penalty) or the collapse silently turns the
generate-then-select pipeline into generate-then-copy.

## Evidence boundary

The executed normalization over three declared variants (illustrative,
deterministic, assumed generation). It demonstrates the failure mode;
real creative generation needs the model, the diversity controls, and a
measured distinctness over a large batch.

## Check your mental model

Answer each before opening it.

**1. Why does normalization matter for counting collapse?**

<details>
<summary>Answer</summary>

Because raw strings hide it. "Run faster, pay less" and "Run faster.
Pay less." look different in a list but are the same message once
punctuation and case are removed. Normalizing exposes the collapse that
a raw-text distinctness count would miss — the executed run shows three
strings shrinking to two distinct messages, one of which is only a
punctuation edit.

</details>

**2. What does the diversity control actually protect?**

<details>
<summary>Answer</summary>

The selection step's information. Scoring can only pick between
variants that differ; if generation collapses, the score chooses among
copies and the delivered creative is whatever the mode happened to be.
Temperature and repetition penalty push the generator off its preferred
mode, keeping the batch diverse enough that selection has a real choice
— the collapse detour's point is that without them, the pipeline's
downstream scoring is decorative.

</details>

## Next

Back to [stage 41](../). The
[surface-score detour](../when-the-score-is-on-surface/) shows the
second failure in the same pipeline: the score that picks the wrong
variant even when generation is diverse.
