---
status: draft
---

# 03 — Pretraining

**Question:** given a fixed corpus and compute budget, which choices make a
next-token model learn reliably instead of wasting tokens, memory, or optimizer
steps?

You arrive with two artifacts:

- a decoder block whose mechanics are understood;
- a clean, versioned text corpus.

You leave with a checkpoint, tokenizer, training trace, and evaluation slice
that another person can reproduce. Follow one artifact through the chapter:

```text
text -> tokens -> batches -> logits -> next-token loss
     -> gradients -> optimizer update -> checkpoint
```

## 1. Turn text into a stable interface

A tokenizer is part of the model contract. Change it and token IDs, sequence
lengths, embedding shapes, and training examples all change.

Byte-pair encoding begins with bytes and repeatedly merges the most frequent
adjacent pair. Starting from bytes guarantees every UTF-8 string is
representable. The trade-off is fertility: how many tokens a source string
becomes.

A small vocabulary produces longer sequences and increases attention cost. A
large vocabulary expands the input embedding and output projection while giving
rare tokens fewer examples. Measure fertility by language and domain; a single
global average hides the users who pay the highest token cost.

The tokenizer stage must publish:

1. training corpus version;
2. normalization and pre-tokenization rules;
3. vocabulary and merge rules;
4. held-out round-trip tests;
5. fertility by relevant language or domain.

See [Mission 01, tokenizer](../../missions/01-language-model-agent/01-tokenizer/)
for the readable implementation and the trained artifact.

## 2. Size the model against the token budget

Model dimensions should not be chosen independently:

```text
vocabulary size -> embedding parameters
model width      -> projection and FFN parameters
depth            -> repeated compute and activation memory
context length   -> attention compute and activation memory
KV head count    -> future serving memory
```

The LLaMA-style block used here combines RMSNorm, RoPE, grouped-query attention,
and SwiGLU because each addresses a different scaling failure. Combining them
does not remove the need to count parameters and estimate tokens per parameter.

For a dense decoder, a training-token estimate is:

$$
C \approx 6ND
$$

where $N$ is parameters and $D$ is training tokens. This is a budgeting
approximation, not a quality guarantee. Chinchilla's compute-optimal result
suggests roughly 20 training tokens per parameter under its measured regime,
but deployed models are often trained on far more data to reduce inference cost
at a fixed quality target.

Change the budget below and separate three questions: what fits the training
compute, what uses the available data, and what is affordable to serve.

<!-- interactive: ChinchillaBudget -->

The number to carry forward is the budget you can actually execute, not the
largest model that fits in memory for one forward pass.

## 3. Build the smallest complete training step

For a token batch `x` and its one-position-shifted labels `y`:

```python
logits = model(x)
loss = cross_entropy(logits.view(-1, vocab_size), y.view(-1))
loss.backward()
optimizer.step()
optimizer.zero_grad()
```

That loop is complete but not yet robust. Before adding distributed systems,
prove four invariants locally:

- labels are shifted exactly once;
- causal masking prevents future access;
- a small batch can be overfit;
- resuming a checkpoint reproduces the next step within the expected numerical
  tolerance.

If the model cannot overfit a tiny sample, scale will only make the bug more
expensive.

## 4. Use precision without losing the update

Forward and backward passes can use lower precision, while optimizer state and
the authoritative weight update remain higher precision. BF16 keeps FP32's
exponent range and therefore avoids FP16's overflow-driven loss-scaling
machinery, but it has fewer mantissa bits.

Change the format below. Compare representable range with local precision; do
not reduce “16-bit” to a single property.

<!-- interactive: PrecisionFormats -->

The consequence is a mixed-precision contract:

```text
bf16 activations and matrix multiplies
fp32 accumulation and optimizer state
explicit checks for non-finite loss and gradients
```

Lower precision saves memory and bandwidth. It does not make numerical
validation optional.

## 5. Accumulate the batch you intend to train

The desired effective batch may not fit in memory. Gradient accumulation runs
several micro-batches before one optimizer step.

If there are `k` micro-batches, divide each micro-batch loss by `k` before
backward. Otherwise the accumulated gradient is `k` times larger and the
effective learning rate changes silently.

<!-- interactive: GradientAccumulation -->

The optimizer step, not the micro-batch, is the unit used for learning-rate
schedules, checkpoint cadence, and tokens-per-update accounting.

## 6. Control the size of early and late updates

Adam's moment estimates begin at zero. Warmup keeps early, poorly estimated
updates small. Cosine decay reduces step size as the model approaches the end
of the allocated token budget.

<!-- interactive: LRSchedule -->

The schedule is part of the run record. “Same model and data” is not a
controlled comparison if peak learning rate, warmup tokens, minimum learning
rate, or weight decay changed.

Track at least:

- train loss and held-out loss by consumed token count;
- gradient norm and clipping rate;
- learning rate;
- throughput and memory;
- skipped or non-finite steps;
- checkpoint and data cursor.

Wall-clock alone cannot distinguish faster learning from merely processing
tokens faster.

## 7. Diagnose the loss curve as a system

Use the pair of training and validation loss:

| Observation | First hypothesis |
|---|---|
| both flat | label shift, masking, optimizer, or learning rate is wrong |
| train falls, validation flat | overfitting or train-validation mismatch |
| both fall, then spike | instability, bad batch, overflow, or resume defect |
| periodic jumps | data shards, schedule boundaries, or checkpoint restore |
| smooth loss, poor samples | tokenizer, data distribution, or evaluation mismatch |

Do not jump directly from a bad sample to a larger model. Identify which
subsystem owns the evidence.

## 8. Extend only after the base run is reproducible

Longer context changes memory, data, and position use. RoPE scaling methods can
make longer positions representable, but they do not create long-range training
examples. Continued domain pretraining changes the data distribution and risks
catastrophic forgetting.

For continued pretraining:

- begin near the base run's final learning rate, not its original peak;
- mix general replay data when general capability must be preserved;
- evaluate domain gain and general regression together;
- version the new mixture separately from the base corpus.

The comparison is two-objective: gain the target domain without silently
erasing the baseline.

## Run the vertical slice

[Mission 01, pretraining](../../missions/01-language-model-agent/02-pretrain/)
connects the tokenizer, decoder, optimizer, and checkpoints. The
[first training loop](../../foundations/01-first-training-loop/) is the
CPU-scale prerequisite when the full run is not yet available.

A valid run record includes exact command, configuration, data version,
hardware, wall-clock, cost, token count, checkpoints, and metrics. A plausible
loss curve written from memory is not evidence.

## Check your mental model

1. Why does tokenizer fertility affect both cost and model quality?
2. Which batch size controls an optimizer update under accumulation?
3. Why does BF16 still need higher-precision optimizer state?
4. What does Chinchilla optimize, and what deployment cost does it omit?
5. Which evidence separates overfitting from a broken training loop?

## Next

The output is a base model that predicts continuations. It does not yet know
that a user message should receive an assistant answer. Continue to
[post-training](../adaptation/post-training/) to define that behavioral
contract.

Primary references: Sennrich et al. (BPE), Kaplan et al. and Hoffmann et al.
(scaling laws), Touvron et al. (LLaMA), Gururangan et al. (continued
pretraining), and YaRN for context extension.
