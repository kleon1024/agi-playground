---
status: verified
level: applied
base: scratch
verified: 2026-08-03
label: Speculative decoding
---

# Is a cheap draft's guess ever worth the expensive model's check?

**Question:** a smaller draft model proposes several tokens; the target model verifies them in
one pass and accepts the longest matching prefix. Whether that is faster than decoding normally
depends on three quantities — draft cost, target verification cost, and acceptance length — and a
fast draft with poor acceptance can be *slower* than plain decoding, because the target still pays
a full verification pass over every proposal regardless of how many survive it. This chapter
measures that crossover directly: the same draft architecture, trained to two different qualities,
against the same target.

Move the three quantities and watch where the crossover lands before reading the measured one.

<!-- interactive: SpeculativeDecoding -->

Acceptance is the quantity that has to be measured per request slice rather than assumed: domain,
temperature, and prompt style all change how often the draft is right, so a single acceptance
number averaged over a mixed workload can hide a slice where speculation is a straight loss.

**Before this:** [quantization](../quantization/), for this stage's running discipline of measuring
a technique's cost against a real forward pass rather than trusting its argument in the abstract.

You will finish able to explain why speculative decoding's correctness does not depend on the
draft's quality at all, only its speed does — and read a measured example of that speed crossing
from a win to a loss as one variable, training steps, changes.

## No checkpoint, no CUDA — so this chapter trains its own

[Graph execution](../graph-execution/) and [quantization](../quantization/) both measure an
already-trained 88,197,888-parameter checkpoint on a real GPU. Neither exists in this environment:
`torch.cuda.is_available()` returns `False` here, and no `.pt` checkpoint is on disk to load. The
question under test — does a cheap model's guesses save an expensive model's forward passes — does
not require either model to be good at anything in particular, only that both are trained on the
same distribution. So `core/speculative.py` trains two tiny transformers from scratch on the local
CPU lane, reusing [the mission's `Transformer`/`Config`](../../02-pretrain/core/model.py)
class and [`05-serve`'s `generate_naive`](../core/engine.py)
baseline, on the same tinyshakespeare corpus [the first training loop](../../../foundations/01-first-training-loop/)
uses:

```
target: 4 layers, d_model=256  ->  2,903,552 params (2.9M)
draft:  2 layers, d_model=96   ->    227,904 params (0.2M)
```

`draft-good` and `draft-poor` share this exact architecture. The only difference between them is
600 training steps versus 40 — isolating draft *quality* as the one variable this chapter changes,
holding draft *size* and the target fixed.

## The mechanism: one verification pass covers k proposed tokens

Each round, the draft proposes `k` tokens the ordinary way — one token at a time, feeding its own
growing sequence back in. Those `k` guesses get appended to the real context and the whole
candidate sequence goes through the target **once**. Because a transformer's forward pass computes
a prediction at every position in one shot, that single pass already contains the target's own
greedy answer for "what comes after position `i`" at every one of the `k` proposed positions —
verifying all of them costs the same one forward pass as verifying one.

```
draft proposes:            d1  d2  d3  d4
target verifies (1 pass):  t1  t2  t3  t4      <- target's own argmax at each position
walk left to right:        accept while ti == di, stop at first mismatch
```

Accept every proposed token up to the first place the target disagrees; take the target's own
token there instead. If every proposal is accepted, the same forward pass already priced in one
free bonus token past the last one — the target has to compute that logit anyway, since it computes
logits at every position in the sequence it was handed.

## Why the output is guaranteed identical to plain greedy decoding

This is the deterministic special case of the two founding papers below, both of which verify with
*probabilistic rejection sampling* so that the accepted distribution stays exact under
temperature-greater-than-zero sampling — a token can be accepted with some probability even when it
does not match the target's single most-likely choice. Greedy decoding only ever wants the argmax,
so that machinery collapses to one equality check per position: accept a proposal **iff** it equals
the token the target's own forward pass would have produced there anyway, computed over the exact
same real prefix a plain greedy decode would have reached at that step. That is not an
approximation of "the same answer" — it is the same answer, checked by construction, and the
chapter's own run asserts it directly rather than trusting the argument:

```
exact match, draft-good: True
exact match, draft-poor: True
```

Both regimes produce token sequences byte-for-byte identical to `generate_naive` (plain
target-only greedy decoding) over 200 tokens. Draft quality changes speed. It never changes
correctness.

## The measured crossover: the same architecture, a win and a loss

```
      config   wall_s  vs_baseline  accept_rate  accepted/round  rounds
    baseline    1.623         1.00           --              --     200
  draft-good    1.028         1.58        0.379            1.51      80
  draft-poor    1.735         0.94        0.159            0.63     123
```

`draft-good` accepts 37.9% of its proposals — 1.51 tokens per verification round, on average — and
that is enough to beat plain decoding by 1.58x on real CPU wall-clock. `draft-poor`, the identical
architecture with 40 training steps instead of 600, accepts only 15.9% of its proposals and is
measurably *slower* than the baseline it was meant to speed up: 0.94x. The extra draft forward
passes plus the wider target verification batch, paid every round regardless of how many tokens
that round nets, cost more than the occasional accepted token saves. This is exactly the boundary
[the serving overview](../README.md) named without a number attached — here it has one, and the
crossover sits between 15.9% and 37.9% acceptance on this model and hardware, not at some universal
threshold.

## What this does not establish

- **The full stochastic speculative decoding algorithm.** Only the deterministic/greedy variant is
  implemented and measured here. Leviathan, Kalman & Matias (2023) and Chen et al. (2023) verify
  with rejection sampling to keep the *distribution* exact under temperature-greater-than-zero
  sampling — a materially harder mechanism this chapter does not build or measure.
- **Anything about GPU speedup.** No CUDA GPU is available in this environment; every number above
  is local CPU wall-clock. The two production systems this platform already measured on a real
  24GB card ([graph execution](../graph-execution/), [quantization](../quantization/)) both
  found the decode step launch-bound rather than bandwidth-bound at batch 1 — whether that changes
  the draft-vs-verify tradeoff on a GPU is not tested here.
- **A universal acceptance threshold.** The 15.9%-to-37.9% crossover is specific to this draft
  size, this target size, this `k=4`, and this corpus. A different pairing of model sizes, or a
  different chunk length, would move where the crossover sits, which is why acceptance has to be
  measured per workload rather than assumed.
- **Multi-request serving.** This is one sequence, one draft, one target, no batching or
  scheduling — the [continuous batching](../why-concurrency-pays/) mechanism this stage already
  measures is a separate concern this chapter does not combine with speculation.

## Reproduce it

```bash
cd 01-language-model/05-serve/speculative-decoding/core
python speculative.py
```

Commands, hardware, and every number above:
[`runs/2026-08-03-speculative-decoding-bench.md`](runs/2026-08-03-speculative-decoding-bench.md).

## Check your mental model

**1. Draft quality changed 600 steps to 40, and speedup flipped from 1.58x to 0.94x. What did NOT
   change between those two runs, and why does that matter for trusting the result?**

<details>
<summary>Answer</summary>

The target model, the target's training, the prompt, `k`, and the correctness guarantee all held
fixed — only the draft's training steps changed. That isolation is what makes the crossover
attributable to draft quality specifically, rather than to some other confound (a different
target, a different prompt that happens to be easier or harder to predict, a different chunk
size). Both runs are also proven byte-identical to plain greedy decoding, so the speed difference
is a pure execution-cost effect, not a quality tradeoff in the output.

</details>

**2. Why does verifying `k` draft tokens cost the target only one forward pass, not `k` of them?**

<details>
<summary>Answer</summary>

A transformer's forward pass is not "predict the next token" — it computes a prediction at *every*
position of whatever sequence it is given, in one batched pass, because of the causal attention
mask (each position only attends to positions before it, so all positions can be computed
simultaneously). Handing the target the real prefix plus all `k` proposed tokens at once means the
logits at position `prefix_len - 1 + i` already contain the target's own greedy answer for what
should follow position `prefix_len - 1 + i`, for every `i` from 0 to `k-1` — one pass reads off all
`k` checks at once, rather than needing one autoregressive step per check.

</details>

**3. `draft-poor` still produced output byte-identical to plain greedy decoding, despite a 15.9%
   acceptance rate. Why doesn't a bad draft ever produce a wrong answer, only a slow one?**

<details>
<summary>Answer</summary>

Because every accepted token is defined as "the token the target's own greedy argmax would have
picked at that position anyway" — acceptance is a check against the target's own output, not a
guess that might be wrong. When the draft's proposal fails that check, the target's own token is
substituted immediately, at the first mismatch. The draft can only ever be wrong about *how many*
tokens it saves the target from computing one at a time; it has no path to injecting a token the
target itself did not endorse.

</details>

**4. At `k=4`, `draft-poor` averaged 0.63 accepted tokens per round. What does an average below 1
   mean about how often that round's single most valuable event — a first-token rejection — is
   happening?**

<details>
<summary>Answer</summary>

An average of 0.63 accepted-per-round, with `k=4`, means the common case is rejecting the draft's
very first proposed token — the walk in `speculative_decode` stops at the first mismatch, so most
rounds contribute only the one corrective token past whatever was accepted before the break,
often zero. Every one of those rounds still paid for `k` draft forward passes and one wider target
verification pass, for a net gain of roughly one token — worse than the plain decode's one token
per one target forward pass, which is exactly why this regime measures slower than the baseline.

</details>

## Next

This platform's three sub-lessons now cover the three questions [the overview](../README.md)
raises without measuring: is the card idle between tokens
([graph execution](../graph-execution/)), does a smaller model decode faster
([quantization](../quantization/)), and is a cheap draft's guess worth the check (this
chapter). Continue to [evaluation](../../07-eval/) to decide whether a served
system, including any of these decode-time techniques, is actually better on a task that matters.

Primary references: Leviathan, Kalman & Matias, *Fast Inference from Transformers via Speculative
Decoding* (Google, 2023); Chen et al., *Accelerating Large Language Model Decoding with Speculative
Sampling* (DeepMind, 2023).
