---
status: verified
base: scratch
verified: 2026-07-28
---

# Architecture ablations: the budget you hold equal

**Question:** RMSNorm beat LayerNorm — under which definition of "beat"?

[Stage 02](../../../missions/01-language-model-agent/02-pretrain/) chose
RMSNorm, RoPE, SwiGLU, and grouped-query attention without comparing any of
them against an alternative. This chapter is where one of those choices gets
tested — and the first thing a test needs is a definition of winning, because
the nine training runs in section 3 support two opposite headlines depending
on which definition you pick.

## 1. The comparison is underdetermined until you say what is held equal

"RMSNorm beat LayerNorm" only means something once you say what stayed fixed
while the norm changed. Three definitions are all defensible, all in common
use, and they routinely disagree:

- **Equal parameters** flatters anything that spends more compute per
  parameter than the control — a block that reuses its weights across several
  passes, or a mixture-of-experts layer whose stored parameters buy capacity
  no single forward pass pays for in full.
- **Equal FLOPs** flatters anything that adds parameters cheaply relative to
  compute — the same mixture-of-experts layer from the other side, or a
  wide-and-shallow dense model.
- **Equal wall-clock** flatters whatever the kernels are already fast at. A
  dense block sits on the most mature kernels in the stack; routing, gathers,
  and extra sequential dependencies pay a kernel-immaturity tax that has
  nothing to do with whether the idea is good.

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
returns one arm matched on each.

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
prevent. The answer the data supports is *not measurable at this scale*, and
that is a result, not a failed experiment. Per-arm numbers are in
[`runs/2026-07-29-five-rungs.md`](runs/2026-07-29-five-rungs.md).

## 4. The rung where the definition decided the answer

The feed-forward rung is worth its own look, because it is the one where
section 1 stops being cautionary and starts changing the headline. Three arms,
8 routed experts with top-2 routing plus one shared expert; only the per-expert
width moves.

| Arm | Total parameters | Active per token | Mean val loss |
|---|---:|---:|---:|
| `dense` | 33,661,440 | 33,652,736 | 3.8608 |
| `moe-equal-active` | 67,314,176 | 33,685,504 | **3.7707** |
| `moe-equal-total` | 33,694,208 | 22,478,848 | 3.8607 |

Holding **active** parameters equal, MoE wins on every seed by 0.0901 nats.
Holding **total** parameters equal, the difference is 0.0001 and its sign flips
between seeds — not "MoE ties dense" but "this ladder cannot tell them apart",
while the MoE arm reached that same loss through 33.2% fewer parameters per
token. Switch the definition below and watch one set of nine runs change its
verdict.

<!-- interactive: EqualBudget -->

The third definition has no winner at all. Both MoE arms ran at roughly half of
dense throughput — `moe-equal-total` performs *less* arithmetic per token and
still took 1.85x as long, which is routing overhead measured rather than
argued. In the 1,645.9 seconds `moe-equal-active` needed, dense would have seen
391M tokens instead of 200M. That arm was not run, so the 0.0901 is not
evidence about it. A budget you did not buy is a blank, not a tie.

## 5. What earns the right to say any of this

Three seeds per arm is the method, not a detail — and the ladder proved why by
accident. The control configuration appears in all six rungs: `rmsnorm`,
`rope`, `swiglu`, `kv8`, `L8-d512`, and `dense` are the same model, run with
the same seeds on the same batches in the same order. Six replications that
should be identical:

> 3.8597, 3.8593, 3.8604, 3.8611, 3.8602, 3.8608

**A range of 0.0018 with nothing whatsoever changed.** That residue is GPU
nondeterminism — non-deterministic reductions in the backward pass, autotuned
kernel choice, bf16 accumulation order. It is an assumption-free floor, bought
for nothing, and it says that any claim here resting on less than about 0.002
is resting on the allocator rather than on the architecture.

Against that floor, a single seed per arm is not a weak result but no result.
`core/ablate.py` runs `--seeds` seeds and writes every one out, because a file
reporting one loss without saying so is reporting noise as a finding.

## 6. Evidence boundary: a ranking can invert with scale

Nothing here shows that a rung's winner at 33M parameters stays the winner at
7B. That caution cuts both ways now. The equal-active MoE arm is already ahead
at this size, which is a smaller and more specific claim than "MoE works" — and
RMSNorm and SwiGLU failing to separate here is emphatically **not** evidence
that they do not help at scale, only that 200M tokens and three seeds cannot
see it.

The rule that follows: trust a ranking only where it is stable across at least
two sizes at the same budget definition. An unstable ranking is not a failed
experiment; it is the finding, reportable as written rather than smoothed into
"results were mixed."

## Run the working path

Three files, in the order you would use them. `core/model.py` prints every
rung's parameter arithmetic with nothing trained. `core/ladder.py` is a CPU
smoke test on synthetic tokens — enough to prove every arm constructs and takes
a step, nothing more. `core/ablate.py` is the one that can rank anything: real
tokens, a fixed budget, seeds, and a result file that cannot be written without
a budget definition.

```bash
cd platform/training/02-architecture-ablations/core
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

1. Why can "equal parameters" and "equal FLOPs" rank the same two
   architectures in opposite orders?
2. The norm rung's per-seed differences are -0.0023, +0.0052, +0.0091. Why is
   the average of those three not a result?
3. Section 4's two MoE arms support opposite headlines from the same nine runs.
   Which sentence is true of both, and which of each alone?
4. `moe-equal-total` matched dense's loss using 33.2% fewer active parameters
   and still took 1.85x as long. Which budget does that make it better under,
   and which worse?
5. Six runs of one identical configuration spanned 0.0018. What does that let
   you ignore, and what does it not excuse?
6. The activation rung put GELU ahead of SwiGLU. Why is that not a finding, and
   what is?

## Next

What this chapter hands back to
[stage 02 of the language-model system](../../../missions/01-language-model-agent/02-pretrain/)
is not a winning architecture. It is a floor. Stage 02 chose RMSNorm and SwiGLU
without comparing them to anything, and this ladder could not separate either
one from its alternative. That does not make those choices wrong — it makes
them **unjustified by this evidence**, which is a more useful thing to know
than a ranking would have been. Position encoding and the feed-forward shape,
by contrast, are choices stage 02 was right to take seriously.

Two loose ends lead elsewhere. GQA's payoff is invisible on a training-time
ladder, because the parameter delta is all such a comparison can see; the
KV-cache-per-token arithmetic it was actually built to change is in
[serving](../../serving/). And if the ladder makes you want a different
feed-forward after the checkpoint already exists,
[upcycling](../05-upcycling/) is how to get one without retraining.

Primary references: Zhang & Sennrich, "Root Mean Square Layer Normalization"
(2019); Su et al., "RoFormer" (2021); Shazeer, "GLU Variants Improve
Transformer" (2020); Ainslie et al., "GQA" (2023); Fedus et al., "Switch
Transformers" (2022), for the scale-dependent mixture-of-experts result cited
in section 6.
