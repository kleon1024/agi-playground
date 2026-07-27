---
status: draft
---

# Architecture ablations: the budget you hold equal

**Question:** RMSNorm beat LayerNorm — under which definition of "beat"?

[Mission 01's pretraining model](../../../missions/01-language-model-agent/02-pretrain/core/model.py)
frames RMSNorm, RoPE, SwiGLU, and GQA as four independent choices, "each can
be ablated on its own," and then deliberately does not ablate them — that file
stays a fixed, readable reference. This chapter is the one that runs the
ladder. Its own `core/` model is a small, variant-configurable sibling of that
reference, not a parameterized version of it: the mission's `model.py` stays
exactly as clean as it was.

## 1. The comparison is underdetermined until you say what is held equal

"RMSNorm beat LayerNorm" only means something once you say what stayed fixed
while the norm changed. Three definitions are all defensible, all in common
use, and they routinely disagree about which variant wins:

- **Equal parameters.** Flatters anything that spends more compute per
  parameter than the control — a block that reuses the same weights across
  several passes (looped or recurrent-depth), or a mixture-of-experts layer
  whose stored parameters buy specialized capacity no single forward pass
  pays for in full.
- **Equal FLOPs.** Flatters anything that adds parameters cheaply relative to
  compute — a sparsely-routed mixture-of-experts layer again, from the other
  side, or a wide-and-shallow dense model whose extra width is easy to add
  without a proportional compute increase.
- **Equal wall-clock.** Flatters whatever the kernels happen to already be
  fast at. A plain dense block sits on the most mature kernels in the stack;
  a design with routing, gathers, or extra sequential dependencies pays a
  kernel-immaturity tax that has nothing to do with whether the idea itself
  is good.

Most published architecture comparisons do not state which of the three they
used. Every run record produced in this chapter must, and `core/ladder.py`
refuses to write a result file without one.

<!-- interactive: EqualBudget -->

Notice that switching the definition reorders the same four designs without
touching any of them — the ranking is a property of the comparison, not of
the architectures. Every rung in the ladder below is anchored to one
definition by construction, and it stops being a controlled comparison the
moment that anchor is left unstated next to the numbers.

## 2. The ladder

Five rungs, each one variable changed against a fixed control. Four are held
equal in total parameters by construction — the definition `core/model.py`'s
helper functions are built to enforce. The fifth, attention, is not, and the
paragraph after the table says why:

| Rung | Control -> variant | What stays fixed |
|---|---|---|
| Norm | RMSNorm -> LayerNorm | everything else |
| Position | RoPE -> learned absolute -> none | everything else |
| Activation | SwiGLU -> GELU | parameters, via `d_ff` |
| Attention | full MHA -> GQA at several KV-head counts | everything but the KV cache |
| Depth/width | a fixed layer count -> half -> double | parameters, via `d_model` |

Two rungs need actual arithmetic to hold equal, and `core/model.py` shows it
rather than asserting it. A GELU MLP is two matrices (`2 * d_model * d_ff`);
SwiGLU is three (`3 * d_model * d_ff`), so an honest comparison shrinks
SwiGLU's `d_ff` to about 2/3 of GELU's. On this chapter's control config
(`d_model=256`), that is `d_ff=683` against `d_ff=1024` — 3,411,200 real
parameters for SwiGLU against 3,410,176 for GELU, a 0.03% miss, close enough
to call equal. The depth/width rung is harder: trading 4 layers at
`d_model=256` for 8 layers means searching for the width that lands closest to
the same total, and the closest available match (`d_model=160`) still misses
by +197,280 parameters — about 5.8% high. That miss is reported, not rounded
away, for the same reason `platform/training/01-distributed` reports ZeRO's
2.5x saving instead of the clean 4x a reader might expect: an uneven match is
more instructive than a hidden one.

The attention rung does not try to match parameters at all — shrinking the
number of KV heads is the point, and `core/model.py`'s own numbers show the
parameter count falling as a side effect (kv8: 3,411,200; kv4: 3,149,056;
kv2: 3,017,984; kv1: 2,952,448). Reporting that side effect, rather than
compensating it away, is itself the honest thing to do: GQA's entire
pretraining-time cost is that small parameter change, traded for a KV cache
that shrinks by the same ratio at serving time.

## 3. Why this is affordable, and what makes it a real experiment

A five-rung, several-arm ladder is only affordable because every arm here is
a few million parameters trainable on a CPU in seconds. That smallness is not
a limitation to apologize for — it is what makes a *controlled* ladder
possible on one card at all, where a single 70B-parameter run already
consumes the budget a whole ladder would need at this scale.

Smallness does not excuse a single run per arm. A single seed is not a weak
result — it is no result, because run-to-run variance at small scale
routinely exceeds the effect an architecture swap produces. `core/ladder.py`
always runs `--seeds` independent seeds per arm for exactly this reason, and
the number of seeds is part of the method: a result file that reports one
seed's loss without saying so is reporting noise as a finding.

## 4. Evidence boundary: a ranking can invert with scale

Nothing here demonstrates that a rung's winner at this parameter count stays
the winner at a larger one. Mixture-of-experts is the standard example: it is
widely expected, and has been reported, to look mediocre at small scale and
strong at large scale, because the specialization that makes routing pay off
needs enough total capacity and enough training tokens to have somewhere to
go. A ladder run at one size cannot tell the two apart from a rung that
simply performs worse everywhere.

The rule that follows: trust a rung's ranking only where it is stable across
at least two sizes, run at the same budget definition. An unstable ranking —
the winner at 10M parameters loses at 100M — is not a failed experiment. It is
itself the finding, and it is reportable exactly as written, not smoothed into
"results were mixed."

## Run the working path

`core/model.py` is the variant-configurable transformer: run `python
model.py` to print every rung's parameter arithmetic, including the numbers
quoted in section 2, with nothing trained. `core/ladder.py` runs one rung
across `--seeds` seeds as a CPU smoke test — forward and backward passes on
synthetic random tokens, enough to prove every arm constructs and trains a
step, nothing more — and writes a result file that always names its budget
definition. `prod/hf_ladder.py` runs the parameter-matching arithmetic for the
attention and depth/width rungs again through HuggingFace `transformers`'
`LlamaConfig`, where `num_key_value_heads` and `hidden_size` are already
named fields; it also names the gap in the other direction — no shipped
config lets norm, position, and activation vary independently of the model
family, so that rung's production stand-in compares two named architectures
(`LlamaConfig` against `GPT2Config`) rather than flipping one flag.

No ladder has actually run yet. This repository's card is mid-pretraining
(see [Mission 01, pretraining](../../../missions/01-language-model-agent/02-pretrain/)),
so this chapter stays `status: draft`, has no `runs/` directory, and makes no
claim about which variant wins anything. What is here is the method: how to
state a budget definition, how to hold it equal, how many seeds a result
needs, and what evidence a ranking would need before it is trustworthy.

## Check your mental model

1. Why can "equal parameters" and "equal FLOPs" rank the same two
   architectures in opposite orders?
2. Why does matching SwiGLU and GELU by parameter count require shrinking
   `d_ff`, and not just leaving it at the GELU value?
3. Why does the GQA rung report a falling parameter count instead of
   compensating for it?
4. Why is a single seed per arm "no result" rather than a weak one, at this
   parameter scale?
5. What would make a rung's ranking untrustworthy even after it ran cleanly
   on this ladder?

## Next

GQA's payoff is invisible on this chapter's CPU-scale ladder — the parameter
delta is the only thing a training-time comparison can see. Continue to
[serving](../../serving/) for the KV-cache-per-token arithmetic that GQA was
built to change.

Primary references: Zhang & Sennrich, "Root Mean Square Layer Normalization"
(2019); Su et al., "RoFormer" (2021); Shazeer, "GLU Variants Improve
Transformer" (2020); Ainslie et al., "GQA" (2023); Fedus et al., "Switch
Transformers" (2022), for the scale-dependent mixture-of-experts result cited
in section 4.
