---
status: verified
level: applied
base: scratch
verified: 2026-07-28
---

# Architecture ablations: the budget you hold equal

**Question:** RMSNorm beat LayerNorm — under which definition of "beat"?

[Stage 02](../) chose
RMSNorm, RoPE, SwiGLU, and grouped-query attention without comparing any of
them against an alternative. This chapter is where one of those choices gets
tested — and the first thing a test needs is a definition of winning, because
the nine training runs in section 3 support two opposite headlines depending
on which definition you pick.

**Before this:** [the decoder block](../../../foundations/00-attention/) for what
RMSNorm, RoPE, SwiGLU and grouped-query attention each do. This chapter tests
those choices; it does not explain them.

## 1. The comparison is underdetermined until you say what is held equal

"RMSNorm beat LayerNorm" only means something once you say what stayed fixed
while the norm changed. Three definitions are all defensible, all in common
use, and they routinely disagree:

- **Equal parameters** flatters anything that spends more compute per
  parameter than the control — a block that reuses its weights across passes,
  or a mixture-of-experts layer whose stored parameters buy capacity no single
  forward pass pays for.
- **Equal FLOPs** flatters the opposite: anything that adds parameters cheaply
  relative to compute, the same expert layer read from the other side.
- **Equal wall-clock** flatters whatever the kernels are already fast at.
  Routing, gathers, and extra sequential dependencies pay a kernel-immaturity
  tax that has nothing to do with whether the idea is good.

Most published architecture comparisons do not state which of the three they
used. Every run record produced in this chapter must, and `core/ablate.py`
refuses to write a result file without one. Section 3 is what that discipline
looks like when the definitions actually disagree.

## 2. The ladder

Six rungs, each one variable changed against a fixed control. Four are held
equal in total parameters by construction — the definition `core/model.py`'s
helper functions are built to enforce. Attention is not, and the feed-forward
rung refuses to choose; the paragraphs after the table say why:

| Rung | Control -> variant | What stays fixed |
|---|---|---|
| Norm | RMSNorm -> LayerNorm | everything else |
| Position | RoPE -> learned absolute -> none | everything else |
| Activation | SwiGLU -> GELU | parameters, via `d_ff` |
| Attention | full MHA -> GQA at several KV-head counts | everything but the KV cache |
| Depth/width | a fixed layer count -> half -> double | parameters, via `d_model` |
| Feed-forward | dense -> mixture-of-experts | active parameters, *or* total parameters |

Holding a budget equal takes arithmetic, and `core/model.py` does it in code
rather than asserting it in prose: `python model.py` prints every rung's match
and, more usefully, every rung's *miss* — SwiGLU against GELU lands within
0.03%, depth against width is still 5.8% high at the closest available width.
Misses are reported rather than rounded away, because an uneven match is more
instructive than a hidden one.

Two rungs decline to match at all, for opposite reasons. Attention lets the
parameter count fall as KV heads shrink, because that fall *is* GQA's entire
pretraining-time cost, traded for a smaller KV cache at serving time. The
feed-forward rung cannot pick: a mixture-of-experts block has *two* parameter
counts — what it stores and what a token passes through — so `moe_arms()`
returns one arm matched on each. The mechanism behind that rung — routing,
the top-1 dead expert, and the entropy-versus-imbalance gap — is worked out
in [the mixture-of-experts foundation](../../../foundations/07-moe/).

## 3. What the ladder found

All six rungs have run: 17 arms, three seeds each, 51 runs, 12.97 GPU-hours on
one card. Because arms within a rung see identical batches in identical order,
the statistic this design supports is the **per-seed difference** against the
control, not the gap between two independently noisy averages.

| Rung | Change | Per-seed differences | Reading |
|---|---|---|---|
| Position | RoPE to learned | +0.0762, +0.0884, +0.0813 | RoPE wins on every seed |
| Feed-forward | dense to MoE, equal active | -0.0942, -0.0940, -0.0822 | MoE wins on every seed |
| Depth/width | 8 layers to 16 narrow ones | +0.0618, +0.0636, +0.0699 | deep-and-narrow loses |
| Attention | 8 KV heads to 4 | +0.0096, +0.0004, +0.0177 | same direction, small |
| Norm | RMSNorm to LayerNorm | -0.0023, +0.0052, +0.0091 | **sign flips** |
| Activation | SwiGLU to GELU | +0.0001, -0.0115, -0.0031 | **sign flips** |

Three tiers, and the last one is what the overnight run bought. Position
encoding and expert routing are unmissable: every seed agrees, by margins more
than ten times anything the hardware could manufacture. Attention and depth are
directionally consistent but too small to size honestly. **And the two choices
the literature argues about hardest cannot be ranked here at all — RMSNorm and
SwiGLU each lose to their alternative on one seed of three.**

Notice which way the activation rung fell. Its three-seed mean puts GELU ahead
of SwiGLU by 0.0048, the opposite of the usual published ordering. Reporting
that as "GELU wins" would be exactly the failure this chapter exists to
prevent. The answer the data supports is *not measurable at this scale* —
a result, not a failed experiment. Per-arm numbers:
[`runs/2026-07-29-five-rungs.md`](runs/2026-07-29-five-rungs.md).

## 4. One rung where the definition decided the answer

The feed-forward rung is the one where section 1 stops being cautionary. Its
nine runs support two opposite headlines: holding **active** parameters equal,
mixture-of-experts wins on every seed by 0.0901 nats; holding **total**
parameters equal, the difference is 0.0001 with the sign flipping between
seeds. Under the third definition there is no winner at all, because the arm
that would settle it was never run.

[The rung that flipped](the-rung-that-flipped/) has the three arms, the
interactive that switches the definition, and the 1.85x routing overhead that
makes an equal-wall-clock comparison a blank rather than a tie.

## 5. What earns the right to say any of this

Three seeds per arm is the method, not a detail — and the ladder proved why by
accident. The control configuration appears in all six rungs: `rmsnorm`,
`rope`, `swiglu`, `kv8`, `L8-d512`, and `dense` are one model, run with the
same seeds on the same batches in the same order. Six replications that should
be identical:

> 3.8597, 3.8593, 3.8604, 3.8611, 3.8602, 3.8608

**A range of 0.0018 with nothing changed.** That residue is GPU
nondeterminism — non-deterministic backward reductions, autotuned kernel
choice, bf16 accumulation order. It is an assumption-free floor bought for
nothing: any claim resting on less than about 0.002 is resting on the
allocator, not the architecture.

That floor turns the whole ladder into one question with a dial on it: how
large a difference are you willing to act on? Set it and see which arms survive.

<!-- interactive: AblationLadder -->

Against that floor a single seed is not a weak result but no result, which is
why `core/ablate.py` runs `--seeds` seeds and writes every one out.

## 6. Evidence boundary: one metric, one distribution, one size

Every number above is validation cross-entropy on a held-out slice of **the
same FineWeb-Edu shards the arms trained on**. That makes it a measure of
in-distribution fit. It says which architecture predicts educational web text
better; it says nothing about which one writes, reasons, or answers better. No
arm was scored on text from another distribution, and none was scored on a
downstream task — a model this small is not expected to separate from chance on
the standard suites, so those scores would be noise wearing a benchmark's name,
though that expectation is itself untested here. Perplexity makes the size of
the largest effect legible: 47.5 down to 43.4. Whether that is worth doubling
the stored parameters is not a question loss can answer.

Nor does anything here show that a rung's winner at 33M stays the winner at 7B.
That caution cuts both ways: the equal-active MoE arm leading at this size is a
smaller claim than "MoE works", and RMSNorm and SwiGLU failing to separate is
emphatically **not** evidence they do not help at scale — only that 200M tokens
and three seeds cannot see it.

Trust a ranking only where it is stable across at least two sizes at the same
budget definition. An unstable ranking is not a failed experiment; it is the
finding.

## Run the working path

Three files, in the order you would use them. `core/model.py` prints every
rung's parameter arithmetic with nothing trained. `core/ladder.py` is a CPU
smoke test on synthetic tokens — enough to prove every arm constructs and takes
a step, nothing more. `core/ablate.py` is the one that can rank anything: real
tokens, a fixed budget, seeds, and a result file that cannot be written without
a budget definition.

```bash
cd 01-language-model/02-pretrain/architecture-ablations/core
python model.py                                    # parameter arithmetic, nothing trained
python ladder.py --rung moe --seeds 3 --steps 20   # CPU smoke test, minutes
python ablate.py --rung moe --data <token-dir> --seeds 3 --tokens 2e8 \
    --budget "both: equal-active and equal-total arms, declared per arm" \
    --out moe-ablation.json                        # the real thing, GPU-hours
```

`prod/hf_ladder.py` redoes the attention and depth/width arithmetic through
HuggingFace `LlamaConfig`, where `num_key_value_heads` and `hidden_size` are
already named fields — and names the gap in the other direction: no shipped
config varies norm, position, and activation independently of the model family.

Commands, hardware, wall-clock, and every per-seed loss are in
[`runs/2026-07-28-moe-rung.md`](runs/2026-07-28-moe-rung.md) for the
feed-forward rung and
[`runs/2026-07-29-five-rungs.md`](runs/2026-07-29-five-rungs.md) for the other
five.

## Check your mental model

Answer each before opening it.

**1. Why can "equal parameters" and "equal FLOPs" rank the same two
architectures in opposite orders?**

<details>
<summary>Answer</summary>

Because the two definitions flatter opposite kinds of design. Equal parameters
flatters anything that spends more compute per stored parameter than the
control — a mixture-of-experts layer whose stored weights buy capacity no
single forward pass fully uses looks great under this definition, since it's
being compared to a dense model with the same parameter count but far less
capacity. Equal FLOPs flatters the reverse: anything that adds parameters
cheaply relative to compute, which is the same MoE layer read from the other
side — under equal FLOPs, the dense control gets to be much larger to match
the MoE arm's compute, closing or reversing the gap. The feed-forward rung in
this chapter is the concrete demonstration: MoE wins by 0.0901 nats under
equal-active, but the difference collapses to 0.0001 with the sign flipping
between seeds under equal-total.

</details>

**2. The norm rung's per-seed differences are -0.0023, +0.0052, +0.0091. Why is
the average of those three not a result?**

<details>
<summary>Answer</summary>

Because the sign flips across the three seeds — one seed favors RMSNorm,
two favor LayerNorm — which means the "true" direction of the effect isn't
knowable from this data at all, and averaging three numbers that disagree on
sign produces a number that doesn't represent any of the three seeds'
individual behavior. This chapter's own measured floor makes the point sharp:
six runs of one identical configuration spanned 0.0018 purely from GPU
nondeterminism, and every one of the norm rung's per-seed differences
(-0.0023, +0.0052, +0.0091) is inside or barely outside that same noise band.
A mean computed from numbers this close to the noise floor is reporting the
allocator, not the architecture.

</details>

**3. Six runs of one identical configuration spanned 0.0018. What does that let
you ignore, and what does it not excuse?**

<details>
<summary>Answer</summary>

It lets you ignore any per-seed difference smaller than about 0.002 as a
meaningful architectural signal — that range (0.0018) is what GPU
nondeterminism alone produces with literally nothing changed (same model,
same seeds, same batches, same order), so a smaller gap is indistinguishable
from noise. It does not excuse skipping seeds or running just one: a single
seed still can't be trusted even when it clears the noise floor, since you
have no way to know from one number alone whether you got a typical seed or
an outlier. The floor tells you how small an effect can possibly mean
something; it doesn't replace the three-seed discipline that established the
floor in the first place.

</details>

**4. The activation rung put GELU ahead of SwiGLU. Why is that not a finding, and
what is?**

<details>
<summary>Answer</summary>

It's not a finding that "GELU beats SwiGLU" because the three per-seed
differences (+0.0001, -0.0115, -0.0031) flip sign across seeds, exactly like
the norm rung — the mean of 0.0048 in GELU's favor is an average of
disagreeing signs, sitting close to the same ~0.002 noise floor the identical-
configuration control established. Reporting "GELU wins" would mistake noise
for signal, which is precisely the failure this whole chapter is built to
prevent. The actual finding is the meta-result: at this model size (33M) and
this token budget (200M), the difference between SwiGLU and GELU is not
measurable at all — a real, reportable conclusion about the limits of this
experiment's resolution, not a verdict on which activation is better.

</details>

## Next

What this chapter hands back to
[stage 02 of the language-model system](../)
is not a winning architecture. It is a floor. Stage 02 chose RMSNorm and SwiGLU
without comparing them to anything, and this ladder could not separate either
one from its alternative. That does not make those choices wrong — it makes
them **unjustified by this evidence**, which is a more useful thing to know
than a ranking would have been. Position encoding and the feed-forward shape,
by contrast, are choices stage 02 was right to take seriously.

Two loose ends lead elsewhere. GQA's payoff is invisible on a training-time
ladder — the parameter delta is all such a comparison sees, and the KV-cache
arithmetic it was built to change is in [serving](../../05-serve/). And if this
leaves you wanting a different feed-forward after the checkpoint already
exists, [upcycling](../upcycling/) gets one without retraining.

Primary references: Zhang & Sennrich, "Root Mean Square Layer Normalization"
(2019); Su et al., "RoFormer" (2021); Shazeer, "GLU Variants Improve
Transformer" (2020); Ainslie et al., "GQA" (2023); Fedus et al., "Switch
Transformers" (2022), for the scale-dependent mixture-of-experts result cited
in section 6.
