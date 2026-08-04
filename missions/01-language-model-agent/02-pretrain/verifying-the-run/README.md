---
status: verified
level: applied
verified: 2026-07-28
base: scratch
label: Verifying the run
---

# How do you know a five-hour run is working?

**Question:** you understand what the model is and what the objective asks of
it — [the previous chapter](../) — and starting the run is one command. It will
take about five hours. What can you check in the first minute that tells you
the next five hours are not wasted?

The artifact this stage produces is a checkpoint plus the history that makes it
believable: a configuration, optimizer moments, tokens seen, and a validation
curve. Everything below is about the small number of checks that separate a run
that is training from a run that is merely running.

<!-- interactive: PretrainingLoop -->

## The check available at step one

The previous chapter established the floor: a model that has learned nothing
must score $\ln(16{,}512) = 9.712$ nats. Predict what it means if step 0 comes
out well *below* that line before you look at the number.

<!-- interactive: InitLossCheck -->

Far below means the model is seeing the answer — a label-shifting bug, a mask
that lets attention read the token it is predicting, a validation file that
overlaps training. Far above means initialization or the loss reduction is
wrong. This run measured **9.8697**, which is the small excess expected from
random weights.

That one number costs one forward pass and rules out most of the ways a
pretraining run can be silently broken. Nothing else in this chapter is
available so early or so cheaply.

## What the budget commits you to

The token budget is the second decision that cannot be fixed later. This run
spent 3.0B tokens on 88,197,888 parameters — roughly 34 tokens per parameter,
against the Chinchilla-optimal ratio of about 20. It is deliberately
over-trained: the compute-optimal ratio minimizes loss for a *training* budget,
while a model you intend to serve is better spent past that point, because
inference cost depends on parameters and not on how long you trained them.

3.0B tokens do not fit in 24GB, so the optimizer step is assembled from pieces.
A micro-batch of 16 sequences of 1,024 tokens is what fits; eight of those
accumulate into one optimizer step of 131,072 tokens.

<!-- interactive: GradientAccumulation -->

Dividing each micro-batch loss by the accumulation count is part of the
algorithm, not bookkeeping. Omit it and the gradient is scaled by eight, which
is identical to multiplying the learning rate by eight — a silent change to the
optimization problem that no log line reports.

## Whether the hardware is doing the work

The loop is correct and the budget is set; the run still takes as long as the
hardware is used well. Model-FLOPs utilization is the fraction of the card's
theoretical throughput that the run actually converts into training.

<!-- interactive: MFUBreakdown -->

The first measurement on this configuration was 85.5k tokens/second at 33.3%
MFU, which projected to roughly 9.8 hours. Enabling `torch.compile` moved it to
165.6k tokens/second and 64.5% — a **1.76x** speedup, and a finished run in
**4.98 hours**. The gap was not arithmetic; it was memory-bound elementwise work
and kernel-launch overhead that fusion removes.

The lesson generalizes past this flag: a wall-clock estimate inherited from a
differently-configured run is a guess wearing a number.

## What five hours bought

![Validation loss from step 0 to 22,500](../runs/loss.svg)

Loss fell from 9.8697 to a best of **3.0689** at step 21,000, a validation
perplexity of 21.5. It then rose to 3.0984 by step 22,500 — the final 6.5% of
the budget went the wrong way, while the learning rate was still decaying toward
its floor.

<!-- interactive: LRSchedule -->

Three explanations fit: the model is beginning to overfit as it approaches one
full epoch over the corpus (0.95 at the end); the cosine floor is too high to
settle; or it is evaluation noise, since each point samples the validation set
rather than consuming it. **This run cannot distinguish them**, because it is one
run. Separating them needs the paired multi-seed comparison in
[the data-ablation harness](../../../../foundations/05-is-the-difference-real/).

Reported at both numbers rather than the better one, and the saved checkpoint is
the final one, not the best-scoring one.

## Fluent, and useless

The most important output of this stage is not the curve. Sampled from the
final checkpoint:

> **The capital of France is** the city of Monaco, which is the largest city in
> the Mediterranean.

> **Photosynthesis is the process by which** the sun shines on the Earth, or in
> the atmosphere, to provide oxygen for a person to breathe.

Grammatical, confident, and wrong. The model learned English morphology,
syntax, register, and the shape of an encyclopedia paragraph. It did not learn
that photosynthesis is performed by plants or that Monaco is not in France, and
at 88M parameters over 3.0B tokens it was never going to.

This is the correct result, and it is the reason a falling loss curve is not a
claim about a working model. Fluency is cheap; grounding is not. Converted back
through [the objective](../#what-wrong-means), a loss of 3.0689 is 4.65%
probability on the right token — real learning, and nowhere near knowing what
the sentence means.

## What this run does not establish

That any of the architecture choices are good ones. There is one arm, one seed,
and no comparison — so nothing here says RMSNorm beat LayerNorm, or that
grouped-query attention cost nothing. Those are separate experiments with a
stated budget definition, in
[architecture ablations](../architecture-ablations/).

Full command, hardware, software versions, generations, and the two monitoring
mistakes worth avoiding are in
[`runs/2026-07-28-pretrain-3b.md`](../runs/2026-07-28-pretrain-3b.md).

## Reproduce it

```bash
cd missions/01-language-model-agent/02-pretrain/core
python train.py --data data/tokens --out ckpt --tokens 3.0e9 --compile
```

## Check your mental model

1. What does a step-0 loss of 5 imply, given a 16,512-token vocabulary?

<details>
<summary>Answer</summary>

A correctly initialized model with no learning yet must score $\ln(16{,}512)
= 9.712$ nats, because that's the loss of spreading probability uniformly
across every possible next token. A step-0 loss of 5 sits far *below* that
line, and the chapter is explicit about what "far below" means: the model is
seeing the answer it's supposed to predict — a label-shifting bug, a mask
that lets attention read the token being predicted, or a validation file that
overlaps training. It is not a lucky initialization; it's a sign the run is
broken before training has done anything at all.

</details>

2. Why does omitting the division by the accumulation count change the learning
   rate rather than just the logged loss?

<details>
<summary>Answer</summary>

Because the division is part of the optimization algorithm, not cosmetic
bookkeeping on a printed number. Skipping it leaves the accumulated gradient
scaled up by the accumulation count (eight, in this run), and a gradient
scaled by eight produces exactly the same parameter update as multiplying the
learning rate by eight would — the optimizer can't tell the difference
between "gradient is eight times bigger" and "step size is eight times
bigger." That's a silent change to the actual optimization problem being
solved, and critically, no log line reports it: the loss value you'd see
printed looks the same either way, which is what makes this bug dangerous
rather than merely cosmetic.

</details>

3. This run used 34 tokens per parameter against a compute-optimal 20. Why is
   over-training the right call for a model you intend to serve?

<details>
<summary>Answer</summary>

Chinchilla's ratio is optimal for minimizing loss *given a fixed training
compute budget* — it says nothing about what happens after training ends.
Once you intend to serve the model, inference cost depends on parameter
count and gets paid on every single request for the life of the model,
while training tokens are a one-time, already-sunk cost. So it's better to
spend extra tokens pushing a smaller parameter count further past the
compute-optimal point than to buy a bigger model that would cost more on
every future request — the same logic the chapter uses elsewhere for why the
KV-cache tradeoff is worth paying once at training time.

</details>

4. Validation loss rose over the last 1,500 steps. Name the three explanations
   and say what evidence would separate them.

<details>
<summary>Answer</summary>

The three: (1) the model beginning to overfit as it approaches one full
epoch over the corpus (0.95 at the end); (2) the cosine learning-rate floor
being too high to let the model settle; (3) evaluation noise, since each
validation point samples the validation set rather than consuming it in
full. The chapter states directly that "this run cannot distinguish them,
because it is one run" — separating them needs the paired multi-seed
comparison in the data-ablation harness: repeated seeds would reveal whether
the uptick reproduces (ruling out noise), a run with a lower LR floor would
test explanation 2, and tracking loss against epoch count on a corpus of
different sizes would test explanation 1.

</details>

5. The model writes fluent English and states that Monaco is the capital of
   France. Which of those two facts is surprising at this scale?

<details>
<summary>Answer</summary>

Neither, according to the chapter — both are exactly the expected result at
88M parameters over 3.0B tokens, which is the whole point of the section
title "Fluent, and useless." Fluency (morphology, syntax, register, the
shape of an encyclopedia paragraph) is cheap and comes from surface-level
next-token statistics the model genuinely learned. Getting facts wrong is
equally expected — "grounding is not" cheap, and a model this small over
this little data "was never going to" hold accurate world knowledge. The
surprising failure mode this chapter warns against isn't either fact alone;
it's mistaking the first (fluency, visible in a falling loss curve) for
evidence of the second (a working, knowledgeable model).

</details>

## Next

[Stage 03](../../03-sft/) changes the learning target. Instead of predicting
every corpus token, it teaches this base model to follow a conversation
template, masking the loss outside the assistant's response — and the measured
result there is the cleanest demonstration of what this chapter's model does
and does not contain.
