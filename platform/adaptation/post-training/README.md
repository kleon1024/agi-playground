---
status: draft
level: applied
label: Post-training
---

# How does a continuation model become an assistant?

And how does it get there without erasing useful capability or learning to
imitate the wrong part of a conversation?

[Stage 03 of the language-model system](../../../missions/01-language-model-agent/03-sft/)
sends you here with a base checkpoint and a behavior problem. Take back the
supervision contract — what is masked, what is scored, and what the template
guarantees — and run it there against real conversations.

We will follow one prompt through three increasingly strong supervision
contracts:

```text
demonstration -> supervised fine-tuning
preference pair -> preference optimization
teacher trajectory -> distillation
```

Each contract changes which tokens produce loss and what that loss means. All
three assume the base model already has the behavior somewhere in its
distribution; installing a behavior it has never produced is
[mid-training](../mid-training/)'s job, not this chapter's.

**Before this:** [what closes the gap](../README.md). You need a base checkpoint
and the fact that it continues text rather than answering questions.

## What exactly is the model being taught to produce?

Pretraining rewards every correct next token in raw text. An assistant dataset
contains roles and a behavioral boundary: user tokens are context; assistant
tokens are the target.

A chat template serializes the roles:

```text
<user> What is LoRA?
<assistant> A low-rank adaptation method. <end>
```

The model still sees the entire sequence, but labels for user and role-marker
tokens are set to `-100`, the ignored value for cross-entropy. Predict which
tokens should contribute before toggling the control.

<!-- interactive: AssistantLossMask -->

Training on prompt tokens wastes gradient budget reproducing user text and
makes “generate both sides” a valid learned behavior. The closing assistant
token matters too: without it, the model is not supervised on when to stop.

The SFT data contract must therefore include template version, role boundaries,
loss mask, truncation policy, and packed-sequence boundaries.

## How do you know the template is wired correctly?

SFT mostly changes format, response policy, and style; it does not inject all
the factual knowledge the base model lacks. Start with a small, reviewed set
that covers the intended task distribution.

Check these failure modes before increasing examples:

- the answer is truncated but still treated as complete;
- the user prompt leaks into the supervised region;
- packed examples can attend across unrelated conversations;
- duplicate templates dominate the style;
- validation prompts are paraphrases of training records.

The first evidence is not a benchmark average. It is a before-and-after set of
fixed prompts showing that the model enters, answers, and exits the assistant
turn correctly.

## Do you need to move every weight?

LoRA keeps a pretrained weight $W$ frozen and learns a low-rank update:

$$
W' = W + \frac{\alpha}{r}BA
$$

where $A\in\mathbb{R}^{r\times k}$,
$B\in\mathbb{R}^{d\times r}$, and $r$ is much smaller than either original
dimension.

**Worked, on this repository's 88M model at $r=8$.** One query projection is
$768 \times 768 = 589{,}824$ weights. Its LoRA pair is
$8 \times (768 + 768) = 12{,}288$ — **48 times fewer**. Adapt all four
attention projections in all 12 layers and the trainable set is 491,520
parameters, **0.56% of the model**, against 18,874,368 if you moved the
projections directly. With $\alpha = 16$ the update is scaled by
$\alpha/r = 2$, and if you later raise $r$ to 16 that scale becomes 1, which is
the entire reason the term is there: rank changes without the update's
magnitude changing underneath you.

Change rank below. Compare trainable parameters with update capacity rather
than treating rank as a free quality knob.

<!-- interactive: LoRARank -->

Initialize one factor randomly and the other to zero so the initial update is
exactly zero but gradients can still flow.

LoRA is not merely compressed full fine-tuning. It constrains the directions
the model can move. That can regularize a small dataset, but it can also block
a change that genuinely requires a higher-rank update.

QLoRA reduces the frozen base weight footprint with 4-bit quantization while
keeping adapters and critical computation at higher precision. It changes
memory feasibility, not the semantic contract of the training data.

## What does a human comparison actually tell you?

A preference record contains a prompt, a chosen response, a rejected response,
and the rubric used to compare them. A reward model converts that comparison
into a scalar difference:

$$
P(y_w \succ y_l)=\sigma(r_w-r_l)
$$

**Worked:** a reward gap of 0 gives $\sigma(0) = 50\%$ — the model claims no
preference. A gap of 1 gives 73.1%, a gap of 2 gives 88.1%, a gap of 3 gives
95.3%. Now add 100 to both rewards. Every one of those numbers is unchanged,
because $\sigma$ only ever sees the difference. A reward of 4.7 is not a score
out of anything; it is meaningful only next to the reward of whatever it was
compared against.

The absolute reward value has no meaning. The model learns which response a
particular annotation process tends to prefer. Length, format, annotator
population, and prompt distribution can all become shortcuts.

Before using a reward model, measure agreement and slice accuracy across the
failure modes the policy may exploit.

## Can you skip the reward model entirely?

DPO compares how much the trainable policy prefers the chosen response over the
rejected response relative to a frozen reference policy:

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
correctly wired DPO run starts there, exactly, the same way pretraining starts
at $\ln(\text{vocab})$ — and a first step that is not 0.693 means the reference
model, not the objective, is wrong. To halve that loss to 0.347 the policy must
reach $\beta[h(y_w)-h(y_l)] = 0.88$, which at $\beta = 0.1$ means a **8.8-nat**
gap in log-probability between chosen and rejected. Small $\beta$ does not mean
small changes; it means the policy has to move much further to register the
same loss.

Change the loss family below and inspect which assumption each variant removes.

<!-- interactive: DPOLossFamily -->

The useful comparison is not a leaderboard of acronyms:

| Method | Changed assumption | New risk |
|---|---|---|
| DPO | explicit offline preference pairs | reference memory and label noise |
| IPO | fixed target margin | margin selection |
| KTO | pointwise good or bad labels | weaker pairwise information |
| ORPO | no frozen reference model | less explicit drift anchor |
| SimPO | length-normalized, reference-free score | margin sensitivity |

All remain offline objectives. They cannot explore responses absent from the
fixed preference dataset.

## When is a stronger model a better label than a human?

Distillation can supervise final answers, token distributions, rationales, or
tool traces. The important distinction is whose trajectory is scored:

- off-policy distillation trains on teacher-generated trajectories;
- on-policy distillation lets the student generate and asks the teacher to
  score or label the student's states.

On-policy data reduces the mismatch between what the student sees during
training and what it produces at inference. It also costs fresh generation and
teacher evaluation, so the run record must include both.

Do not assume a longer rationale is a better target. Verify answer correctness,
faithfulness where measurable, and whether the target format will exist at
deployment time.

What the teacher exposes decides what you can copy, and that turns out to
constrain the student's tokenizer rather than only its weights.
[Distillation](../distillation/) takes that question on its own terms.

## Can two fine-tunes be added together?

Model merging treats a fine-tune as a task vector:

$$
\tau_i=\theta_i-\theta_{\text{base}}, \qquad
\theta_{\text{merged}}=\theta_{\text{base}}+\sum_i\lambda_i\tau_i
$$

**Worked, on two fine-tunes of the 88M base at $\lambda_1=\lambda_2=0.5$.**
Each $\tau_i$ has one number per weight — 88,197,888 of them — so merging two
adapters means holding three full checkpoints, not two adapters. The arithmetic
then decides everything. If the two task vectors are identical, the merge
reproduces one fine-tune exactly. If they are exact opposites, $0.5\tau + 0.5(-\tau) = 0$
and the merge is the base model, having learned nothing from either. Real task
vectors sit between those poles, per weight, and no scalar $\lambda$ can tell
you where.

This is useful when checkpoints share the same base and their updates do not
strongly conflict. It is not a substitute for evaluation. Merge methods such as
TIES and DARE change how sign conflicts and small updates are handled, but none
make incompatible bases compatible.

Evaluate every source model, the merged model, and regression slices. A merge
that combines two headline capabilities can still lose both on their harder
cases.

## Run the working path

[Mission 01, SFT](../../../missions/01-language-model-agent/03-sft/) owns the
first vertical slice: serialize conversations, mask the prompt, fine-tune the
base checkpoint, and compare fixed prompts before and after.

That run can establish behavioral change on the chosen prompts. It cannot
establish broad instruction-following quality, safety, or preference alignment.

## Check your mental model

1. Why are prompt tokens visible but excluded from SFT loss?
2. What does LoRA rank constrain?
3. What can a reward-model score claim, and what can it not claim?
4. Why is DPO still limited by an offline dataset?
5. What compatibility assumption makes task-vector merging plausible?

## Next

The output is an assistant policy shaped by demonstrations or fixed
preferences. Continue to [distillation](../distillation/) when a stronger model
can supply the targets, or to
[reinforcement learning](../reinforcement-learning/) when the policy must
generate new attempts, receive a reward, and update from its own behavior.

Primary references: LIMA, LoRA, QLoRA, DPO, SimPO, GKD, and Task Arithmetic.

[The post-training landscape](LANDSCAPE.md) pairs the from-scratch trainer here
with the libraries that ship these algorithms, and says where their defaults
disagree with what this chapter argues.
