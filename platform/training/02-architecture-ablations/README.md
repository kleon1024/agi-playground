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
rather than asserting it in prose — `python model.py` prints every rung's
match and, more importantly, every rung's *miss*. SwiGLU against GELU comes
within 0.03%; depth against width does not come out that clean, and the
closest available width is still 5.8% high. Those misses are reported rather
than rounded away, for the same reason
[`01-distributed`](../01-distributed/) reports ZeRO's 2.5x saving instead of
the clean 4x a reader expects: an uneven match is more instructive than a
hidden one.

Two rungs decline to match at all, for opposite reasons. The attention rung
lets the parameter count fall as KV heads shrink, because that fall *is* GQA's
entire pretraining-time cost, traded for a KV cache that shrinks by the same
ratio at serving time. And the feed-forward rung cannot pick: a
mixture-of-experts block has *two* parameter counts — what it stores and what
any one token passes through — so `moe_arms()` returns one arm matched on each
and refuses to choose between them.

## 3. What the rung measured, and why one number was not enough

Of the six rungs, this is the one that has run on real tokens: three arms,
three seeds each, 200M FineWeb-Edu tokens per run, sharing a per-seed batch
sequence so a difference between arms cannot be a difference in what they
were shown. Every expert setup is 8 routed experts with top-2 routing plus one
shared expert; only the per-expert width changes.

| Arm | Total parameters | Active per token | Mean val loss | Seed spread |
|---|---:|---:|---:|---:|
| `dense` | 33,661,440 | 33,652,736 | 3.8608 | 0.0033 |
| `moe-equal-active` | 67,314,176 | 33,685,504 | **3.7707** | 0.0122 |
| `moe-equal-total` | 33,694,208 | 22,478,848 | 3.8607 | 0.0034 |

Read the two MoE rows against dense one at a time, and they support opposite
headlines. Holding **active** parameters equal, MoE wins by 0.0901 nats —
7.4x the widest seed spread, comfortably clear of noise. Holding **total**
parameters equal, the gap is 0.0001 against spreads of 0.0033, which does not
say the two are equal; it says this ladder cannot tell them apart. What that
arm did buy is on the other axis: the same loss while passing each token
through 33.2% fewer parameters.

Switch between the definitions below and watch a single set of nine runs
change its verdict.

<!-- interactive: EqualBudget -->

The third definition is the one to sit with, because it has no winner at all.
Both MoE arms ran at roughly half of dense throughput — `moe-equal-total`
performs *less* arithmetic per token and still took 1.85x as long, which is
routing overhead measured rather than argued. So in the 1,645.9 seconds
`moe-equal-active` needed, the dense arm would have seen 391M tokens instead
of 200M. Whether it would still have lost is not established, because that arm
was not run, and the 0.0901 nats above are not evidence about it. A budget
definition you did not buy is not a tie — it is a blank.

## 4. Why this is affordable, and what makes it a real experiment

The whole rung cost 3.42 GPU-hours, only possible because every arm is tens of
millions of parameters rather than tens of billions. That smallness is not a
limitation to apologize for — it is what buys a *controlled* comparison on one
card, where a single 70B run would consume the entire budget.

Smallness does not excuse a single run per arm. A single seed is not a weak
result — it is no result, because run-to-run variance at small scale routinely
exceeds the effect an architecture swap produces. The rung above is the
argument in miniature: had `moe-equal-active` been run once and landed on
3.7778 while dense landed on 3.8596, the reported effect would have been 0.082
instead of 0.0901, and nothing in the output would have revealed that ±0.006 of
it was the seed. `core/ablate.py` always runs `--seeds` independent seeds per
arm and writes every one of them out, because a result file that reports one
seed's loss without saying so is reporting noise as a finding.

## 5. Evidence boundary: a ranking can invert with scale

Nothing here demonstrates that a rung's winner at this parameter count stays
the winner at a larger one. Mixture-of-experts is the standard caution: it is
widely expected to look mediocre at small scale and strong at large scale,
because the specialization that makes routing pay off needs enough capacity
and enough tokens to have somewhere to go. Section 3 found the equal-active
arm already ahead at 33M parameters, which is a smaller and more specific
claim than "MoE works" — it says nothing about whether 0.0901 nats grows,
shrinks, or reverses at 7B.

The rule that follows: trust a rung's ranking only where it is stable across
at least two sizes, run at the same budget definition. An unstable ranking —
the winner at 10M parameters loses at 100M — is not a failed experiment. It is
itself the finding, and it is reportable exactly as written, not smoothed into
"results were mixed."

## Run the working path

Three files, in the order you would use them. `core/model.py` is the
variant-configurable transformer: run `python model.py` to print every rung's
parameter arithmetic, including the numbers quoted in section 2, with nothing
trained. `core/ladder.py` runs one rung across `--seeds` seeds as a CPU smoke
test — forward and backward passes on synthetic random tokens, enough to prove
every arm constructs and trains a step, nothing more. `core/ablate.py` is the
one that can rank anything: real tokens, a fixed budget, seeds, and a result
file that cannot be written without a budget definition.

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
config varies norm, position, and activation independently of the model
family, so that rung's production stand-in has to compare two architectures
rather than flip one flag.

**Only the feed-forward rung has been trained.** Its command, hardware,
wall-clock, and per-seed losses are in
[`runs/2026-07-28-moe-rung.md`](runs/2026-07-28-moe-rung.md). The other five
rungs have their arms constructed and smoke-tested and nothing more, so this
chapter makes no claim about norms, positions, activations, KV-head counts, or
depth against width. Those tables in section 2 are a plan, not a finding.

## Check your mental model

1. Why can "equal parameters" and "equal FLOPs" rank the same two
   architectures in opposite orders?
2. Section 3's two MoE arms support opposite headlines from the same nine
   runs. Which sentence would be true of both, and which of each alone?
3. `moe-equal-total` matched dense's loss using 33.2% fewer active parameters
   and still took 1.85x as long. Which budget does that make it better under,
   and which worse?
4. Why does matching SwiGLU and GELU by parameter count require shrinking
   `d_ff`, and not just leaving it at the GELU value?
5. Why is a single seed per arm "no result" rather than a weak one, at this
   parameter scale?
6. What would make the 0.0901-nat result untrustworthy even though it ran
   cleanly across three seeds?

## Next

What this chapter hands back to
[stage 02 of the language-model system](../../../missions/01-language-model-agent/02-pretrain/)
is not a winning architecture. It is the habit of stating the budget before
stating the ranking — without which "we chose RMSNorm" is a preference rather
than a result.

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
in section 5.
