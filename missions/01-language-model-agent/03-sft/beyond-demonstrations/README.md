---
status: draft
level: applied
base: none
label: Beyond demonstrations
---

# You have comparisons, not demonstrations. What changes?

[The previous chapter](../) fine-tuned every weight of an 88M model on 9,500
written conversations, because that is what the data was: a person had already
produced the answer, and the model's job was to imitate it. Two things break
that arrangement in practice. Sometimes nobody wrote the answer — all you have
is a pair of candidate replies and a judgement about which is better. And
sometimes moving 88M weights is fine while moving 8B of them is not.

This chapter is the four adaptation methods that answer those two constraints:
one that changes *how much* of the model moves, and three that change *what the
supervision is*. None of them is run here — this repository's checkpoint is
small enough that full fine-tuning is cheap and no preference data was
collected for it — so every number below is worked arithmetic on this model's
real shapes, not a measurement. That boundary is restated at the end.

**Before this:** [how does a text predictor learn to answer?](../), through the
loss mask. Every method here changes what produces gradient; you need to know
what produced it in the demonstration case first.

## Do you need to move every weight?

LoRA keeps a pretrained weight $W$ frozen and learns a low-rank update beside
it:

$$
W' = W + \frac{\alpha}{r}BA
$$

where $A\in\mathbb{R}^{r\times k}$, $B\in\mathbb{R}^{d\times r}$, and $r$ is
much smaller than either original dimension.

**Worked, on this repository's 88M model at $r=8$.** One query projection is
$768 \times 768 = 589{,}824$ weights. Its LoRA pair is
$8 \times (768 + 768) = 12{,}288$ — **48 times fewer**. Adapt all four attention
projections in all 12 layers and the trainable set is 491,520 parameters,
**0.56% of the model**, against 18,874,368 if you moved the projections
directly. With $\alpha = 16$ the update is scaled by $\alpha/r = 2$, and if you
later raise $r$ to 16 that scale becomes 1 — which is the entire reason the term
is there. Rank changes without the update's magnitude changing underneath you.

Change rank below. Compare trainable parameters against update capacity rather
than treating rank as a free quality knob.

<!-- interactive: LoRARank -->

Initialize one factor randomly and the other to zero, so the initial update is
exactly zero while gradients still flow.

The thing to carry forward is that **LoRA is not compressed full fine-tuning; it
is constrained fine-tuning.** Rank bounds the directions the update may move in.
That constraint can regularize a small dataset, and it can also block a change
that genuinely needs a higher-rank update — which is a different failure from
"not enough data", and it does not look different in a loss curve. QLoRA reduces
the frozen base's footprint further with 4-bit quantization while keeping
adapters and the critical computation at higher precision; it changes what fits
on a card, not the semantics of the training data.

## What does a human comparison actually tell you?

A preference record holds a prompt, a chosen response, a rejected response, and
the rubric used to compare them. A reward model turns that comparison into a
scalar difference:

$$
P(y_w \succ y_l)=\sigma(r_w-r_l)
$$

**Worked.** A reward gap of 0 gives $\sigma(0) = 50\%$ — the model claims no
preference. A gap of 1 gives 73.1%, a gap of 2 gives 88.1%, a gap of 3 gives
95.3%. Now add 100 to both rewards. Every one of those numbers is unchanged,
because $\sigma$ only ever sees the difference.

So a reward of 4.7 is not a score out of anything. It is meaningful only beside
the reward of whatever it was compared against, and what the model has actually
learned is which response *a particular annotation process* tends to prefer.
Length, formatting, the annotator population, and the prompt distribution can
all become shortcuts that score well and mean nothing. Before trusting a reward
model, measure annotator agreement and accuracy sliced by the failure modes the
policy might exploit — a model that is 95% accurate overall and 50% accurate on
long answers has taught the policy to be verbose.

## Can you skip the reward model entirely?

DPO compares how much the trainable policy prefers the chosen response over the
rejected one, relative to a frozen reference policy:

$$
h(y)=\log\pi_\theta(y|x)-\log\pi_{\text{ref}}(y|x)
$$

$$
L_{\text{DPO}}
=
-\log\sigma\left(\beta[h(y_w)-h(y_l)]\right)
$$

**Worked, at $\beta = 0.1$.** At step zero the policy *is* the reference, so
$h(y_w) = h(y_l) = 0$ and the loss is $-\log\sigma(0) = \log 2 = 0.693$. Every
correctly wired DPO run starts exactly there, the same way pretraining starts at
$\ln(\text{vocab})$ — and a first step that is not 0.693 means the reference
model is wrong, not the objective. To halve that loss to 0.347 the policy must
reach $\beta[h(y_w)-h(y_l)] = 0.88$, which at $\beta = 0.1$ means an **8.8-nat**
gap in log-probability between chosen and rejected. Small $\beta$ does not mean
small changes; it means the policy has to move much further to register the same
loss.

Change the loss family below and read which assumption each variant drops.

<!-- interactive: DPOLossFamily -->

The useful comparison is not a leaderboard of acronyms — it is which assumption
each one removes, and what that removal costs:

| Method | Assumption dropped | New risk |
|---|---|---|
| DPO | needs a reward model | reference memory, label noise |
| IPO | fixed target margin | choosing the margin |
| KTO | needs paired data | weaker signal per label |
| ORPO | needs a frozen reference | no explicit drift anchor |
| SimPO | reference-free, length-normalized | margin sensitivity |

All of them stay **offline**. None can explore a response that is absent from
the fixed preference dataset, which is exactly the boundary
[stage 04](../../04-rl/) crosses when it lets the policy generate its own
attempts and be scored on them.

## Can two fine-tunes be added together?

Model merging treats a fine-tune as a task vector:

$$
\tau_i=\theta_i-\theta_{\text{base}}, \qquad
\theta_{\text{merged}}=\theta_{\text{base}}+\sum_i\lambda_i\tau_i
$$

**Worked, on two fine-tunes of the 88M base at $\lambda_1=\lambda_2=0.5$.** Each
$\tau_i$ carries one number per weight — 88,197,888 of them — so merging two
fine-tunes means holding three full checkpoints, not two small adapters. The
arithmetic then decides everything. If the two task vectors are identical, the
merge reproduces one fine-tune exactly. If they are exact opposites,
$0.5\tau + 0.5(-\tau) = 0$ and the merge is the base model, having learned
nothing from either. Real task vectors sit between those poles *per weight*, and
no scalar $\lambda$ can tell you where.

Merging is plausible only when the checkpoints share a base and their updates do
not strongly conflict — subtract a different base and the vectors point through
unrelated coordinate systems. TIES and DARE change how sign conflicts and small
updates are handled; none of them make incompatible bases compatible. Evaluate
every source model, the merged model, and the regression slices, because a merge
of two headline capabilities can lose both on their harder cases.

## What this chapter does not establish

Nothing here has been run. There is no LoRA fine-tune, no reward model, no
preference dataset, and no merged checkpoint in this repository, so every figure
above is arithmetic on this model's declared shapes rather than a measurement —
which means it can tell you what a method *costs* and not what it *buys*.
[Stage 03's own run](../#what-it-actually-did) is the only adaptation
measurement mission 01 has, and it is full fine-tuning on demonstrations.

Primary references: LoRA (Hu et al., 2021), QLoRA (Dettmers et al., 2023), DPO
(Rafailov et al., 2023), SimPO (Meng et al., 2024), and Task Arithmetic (Ilharco
et al., 2022).

## Check your mental model

1. What does LoRA rank constrain, beyond the parameter count?

<details>
<summary>Answer</summary>

The directions the update is allowed to move in. $A$ and $B$ together define a
rank-$r$ update, so $r$ bounds the space of weight changes the adapter can
express at all — not just how many numbers you are training. A low rank can
regularize a small dataset and can equally block a change that genuinely
requires a higher-rank update, which is why LoRA is constrained fine-tuning
rather than compressed fine-tuning. The failure looks like "the method didn't
work" and is actually "the update I needed wasn't in the subspace".

</details>

2. What can a reward-model score claim, and what can it not?

<details>
<summary>Answer</summary>

It can claim a relative preference between two specific responses to the same
prompt: $P(y_w \succ y_l) = \sigma(r_w - r_l)$ depends only on the difference.
It cannot claim an absolute quality score — adding 100 to both rewards leaves
every predicted preference unchanged, because $\sigma$ only ever sees the
difference. A reward of 4.7 in isolation means nothing; it is meaningful only
next to whatever it was compared against.

</details>

3. Why is DPO still limited by an offline dataset, and which of its variants
   escapes that?

<details>
<summary>Answer</summary>

None of them escape it. DPO only ever compares a chosen and a rejected response
that already exist in a fixed dataset; it never generates a new candidate of its
own. If a genuinely better response was never sampled into that dataset, DPO has
no mechanism for discovering it — it can only reweight preference among the
options it was given. IPO, KTO, ORPO, and SimPO each drop a *different*
assumption (the reward model, paired labels, the frozen reference, the reference
entirely) and all of them stay offline for the same reason. Generating new
attempts and scoring them is what stage 04 is.

</details>

4. What compatibility assumption makes task-vector merging plausible at all?

<details>
<summary>Answer</summary>

That the checkpoints share the same base model. The merge arithmetic
$\theta_{\text{merged}} = \theta_{\text{base}} + \sum_i \lambda_i \tau_i$ only
makes sense because every $\tau_i = \theta_i - \theta_{\text{base}}$ is computed
in that one shared weight space — subtract a different base and the vectors point
through unrelated coordinate systems, and no scalar $\lambda$ reconciles that. A
shared base is necessary and not sufficient: real task vectors still conflict per
weight, which is why merging never substitutes for evaluating the merged model.

</details>

## Next

[Distillation](../distillation/) when a stronger model can supply the targets
your annotators cannot — and it is the one method on this page that
mission 01 actually ran. Then [stage 04 — RL](../../04-rl/), where the policy
stops imitating a fixed dataset and starts generating attempts to be scored.
