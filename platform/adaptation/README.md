---
level: applied
---

# What closes the gap between predicting text and answering a person?

A pretrained base model predicts the next token in a document. Nothing about
that objective makes it answer a question, call a tool, refuse a request, or
prefer one correct answer over another correct answer. Adaptation is every
technique that closes that gap, and it is four chapters rather than one because
the techniques operate at different scales, on different data, for different
reasons.

Missions enter here at the point where a base model exists and its behavior is
wrong — [stage 03 of the language-model system](../../missions/01-language-model-agent/03-sft/)
is the usual arrival. Which chapter you need depends on what is missing, so
read the question column and take the one that matches, not the whole sequence.
Read in order only if you are building the full pipeline; each chapter then
consumes what the previous one leaves behind.

| Chapter | The question it answers |
|---|---|
| [Mid-training](mid-training/) | Your base has never seen a tool call. Where does that go, and why is the answer not SFT? |
| [Post-training](post-training/) | How do you turn a text predictor into something that follows instructions and has preferences? |
| [Distillation](distillation/) | You can afford to generate from a good model but not to train one. What exactly can you copy? |
| [Reinforcement learning](reinforcement-learning/) | How do you improve a model when there is no correct answer to imitate, only a signal about whether it succeeded? |

**Before this:** [training](../training/), which produces the base model every
chapter below starts from. Nothing here creates capability; all of it reshapes
what pretraining already installed.

## Why mid-training is a separate chapter

The pipeline is commonly described as two stages, pretraining then
post-training, and that description is wrong in a way that matters. Agentic
and tool-use behaviour is installed at pretraining scale — hundreds of billions
of tokens — in a stage that sits between the two, before any supervised
fine-tuning happens. Supervised fine-tuning operates at millions of tokens. The
two are not substitutes, and treating them as one stage leads to the
expectation that a few thousand tool-call examples can install a capability
that was never there.

## What decides which chapter applies

The constraint that runs through all four is capacity. Reinforcement learning
sharpens behaviour a model already produces sometimes; it cannot install
behaviour that is absent, because group-relative advantage is zero when every
rollout in a group fails identically. Mid-training installs behaviour by
exposure, but only if the model is large enough for the exposure to land in.
Distillation copies behaviour from a model that already has it, and is bounded
by whether teacher and student share a tokenizer.

This is why every lesson in the repository declares a `base:` in its
frontmatter — `scratch`, `none`, or `external:<model-id>`. The same technique
applied to an 88M model trained here and to a published 0.6B checkpoint
produces different results for reasons that are invisible in a loss curve. See
[the lesson and run contract](../../standards/lesson-and-run-contract.md).
