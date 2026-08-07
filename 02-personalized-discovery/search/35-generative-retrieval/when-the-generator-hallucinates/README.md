---
status: verified
level: applied
base: scratch
label: When the generator hallucinates
verified: 2026-08-07
---

# The generator hallucinates an ID that does not exist

**Question:** [stage 35's generative retrieval](../) emits document IDs.
This chapter reads the executed corpus check and asks what happens when
the decode invents one.

**Before this:** [stage 35 — generative retrieval](../) and its executed
beam decode.

## The check, executed

The run ([record](runs/2026-08-07-generator-hallucinates-read.md))
verifies each generated ID against the corpus:

| generated | in corpus |
|---|---|
| doc_02 | True |
| doc_99 | False |
| doc_03 | True |

Valid results: doc_02, doc_03.

## The reading

doc_99 is emitted but does not exist, so the beam slot is wasted and the
result is dropped at the corpus check. A retrieval model that
manufactures IDs needs the check — the index is the arbiter of what the
generator may return. The hallucination is not an index failure; the
index is doing its job. It is a decode failure, and the only defense is
verification, which costs the very latency the approach was meant to
save.

## Evidence boundary

The executed check over three declared generated IDs (illustrative,
deterministic, assumed decode output). It demonstrates the mechanism;
real generative retrieval needs the trained model and a measured
hallucination rate over the actual corpus.

## Check your mental model

Answer each before opening it.

**1. Why can the generator emit an ID the corpus does not contain?**

<details>
<summary>Answer</summary>

Because the decode samples from a vocabulary of possible tokens, and
the ID is a sequence of those tokens. Nothing constrains the output to
be a real document — the model learned the ID distribution, not a
database lookup. doc_99 is a well-formed ID that happens to name
nothing, which is the same class of failure as a language model
confidently stating a false fact.

</details>

**2. What does the corpus check cost, and why is it still worth it?**

<details>
<summary>Answer</summary>

It costs the latency advantage — every generated ID has to be verified
against the corpus, reintroducing a lookup the approach removed. It is
still worth it because an unverified decode can return nonexistent
documents as if they were answers, which would break the next stage's
ranking. The check trades some of the speed win for correctness, and
the hallucination rate decides how much is left.

</details>

## Next

Back to [stage 35](../). The
[ID-space detour](../when-the-id-space-grows/) shows the scaling side:
how accuracy decays as the corpus the model must spell grows.
