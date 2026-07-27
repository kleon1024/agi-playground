---
status: draft
---

# Post-training

**Question:** how do we turn a continuation model into an assistant without
erasing useful capability or teaching it to imitate the wrong part of a
conversation?

We will follow one prompt through three increasingly strong supervision
contracts:

```text
demonstration -> supervised fine-tuning
preference pair -> preference optimization
teacher trajectory -> distillation
```

Each contract changes which tokens produce loss and what that loss means.

## 1. Define the assistant turn

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

## 2. Prove the data path before scaling it

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

## 3. Restrict the update when full fine-tuning is unnecessary

LoRA keeps a pretrained weight $W$ frozen and learns a low-rank update:

$$
W' = W + \frac{\alpha}{r}BA
$$

where $A\in\mathbb{R}^{r\times k}$,
$B\in\mathbb{R}^{d\times r}$, and $r$ is much smaller than either original
dimension.

Change rank below. Compare trainable parameters with update capacity rather
than treating rank as a free quality knob.

<!-- interactive: LoRARank -->

Initialize one factor randomly and the other to zero so the initial update is
exactly zero but gradients can still flow. Scaling by `alpha / r` keeps update
magnitude comparable while rank changes.

LoRA is not merely compressed full fine-tuning. It constrains the directions
the model can move. That can regularize a small dataset, but it can also block
a change that genuinely requires a higher-rank update.

QLoRA reduces the frozen base weight footprint with 4-bit quantization while
keeping adapters and critical computation at higher precision. It changes
memory feasibility, not the semantic contract of the training data.

## 4. Represent preference as evidence, not truth

A preference record contains a prompt, a chosen response, a rejected response,
and the rubric used to compare them. A reward model converts that comparison
into a scalar difference:

$$
P(y_w \succ y_l)=\sigma(r_w-r_l)
$$

The absolute reward value has no meaning. The model learns which response a
particular annotation process tends to prefer. Length, format, annotator
population, and prompt distribution can all become shortcuts.

Before using a reward model, measure agreement and slice accuracy across the
failure modes the policy may exploit.

## 5. Understand DPO as one explicit objective

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

## 6. Use distillation when the teacher supplies a richer target

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

## 7. Merge only when the compatibility assumption holds

Model merging treats a fine-tune as a task vector:

$$
\tau_i=\theta_i-\theta_{\text{base}}, \qquad
\theta_{\text{merged}}=\theta_{\text{base}}+\sum_i\lambda_i\tau_i
$$

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
preferences. Continue to
[reinforcement learning](../reinforcement-learning/) when the policy must
generate new attempts, receive a reward, and update from its own behavior.

Primary references: LIMA, LoRA, QLoRA, DPO, SimPO, GKD, and Task Arithmetic.
