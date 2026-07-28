---
status: draft
label: Language-model agent
---

# Raw text to a tool-using model

Build one complete language-model system on a single 24GB GPU: clean raw text,
train a tokenizer, pretrain a decoder, adapt its behavior, serve it, place it
inside a controlled agent loop, and evaluate the resulting system.

This is the integration test for the repository. Each stage owns one artifact
and consumes the previous stage's output. The chain is only complete when the
model trained here is served by the engine built here and driven by the harness
built here.

## Why this mission exists

It is easy to understand each layer in isolation and still fail to build a
system. Tokenizer choices change sequence length; sequence length changes
training and serving cost; architecture choices change the KV cache; the
serving API constrains the harness; the harness changes what the evaluation
actually measures.

This mission makes those dependencies visible:

<!-- interactive: LanguageModelPipeline -->

The mission contract is [`mission.yaml`](mission.yaml). Read its
`does_not_prove` section before treating the pipeline as a product claim.

## The stage contract

Every stage has one input, one deliverable, one verification boundary, and one
next consumer. A stage may have working code while remaining `draft`: code
demonstrates an implementation, while a run record demonstrates that the
declared path actually executed.

| Stage | Deliverable | Current evidence |
|---|---|---|
| [`00-corpus`](00-corpus/) | cleaned English shard and a comparison between the readable and production pipelines | verified run |
| [`01-tokenizer`](01-tokenizer/) | byte-level BPE vocabulary, fast export, and round-trip parity | verified run |
| [`02-pretrain`](02-pretrain/) | 88.2M decoder, token data path, optimizer loop, and resumable checkpoint | **verified** — 3.0B tokens in 4.98h, best val loss 3.0689 |
| [`03-sft`](03-sft/) | chat template, assistant-only loss, and before/after behavior | **verified** — 9,500 conversations in 92.5s, best val loss 2.7828 |
| [`04-rl`](04-rl/) | GRPO updates against a verifiable reward | implementation present; run pending |
| [`05-serve`](05-serve/) | KV-cache decoding, paged allocation, and continuous batching | implementation present; run pending |
| [`06-agent`](06-agent/) | bounded tool loop, grounding rule, context policy, and sandbox | implementation present; run pending |
| [`07-eval`](07-eval/) | disclosed harness, static and agentic tasks, variance, and failure cases | implementation present; run pending |

## The stage this mission deliberately skips

Between pretraining and SFT the platform describes a third training stage,
[mid-training](../../platform/adaptation/mid-training/), where a base model
first sees tool calls and long contexts. This mission has no such stage, and the
reason is a constraint rather than an oversight: mid-training installs behavior
by exposure at pretraining scale, and a base this small trained on this much
text has no capacity for the exposure to land in. Running it here would produce
a clean loss curve and teach the reader something false.

The same constraint decides where reinforcement learning can honestly be taught.
Group-relative policy optimization normalizes advantage within a group of
rollouts, so a base that never solves the task returns an advantage of zero for
every sample and therefore no gradient at all. Reinforcement learning sharpens
behavior a model already produces sometimes; it cannot install behavior that is
absent. Stage 04 is built and readable for that reason, and its run record will
state which base it used.

## What composes across the stages

The tokenizer is frozen before pretraining. Changing it later changes token IDs
and invalidates the embedding table. The pretraining checkpoint fixes the model
shape that SFT and RL must load. Adaptation changes weights, not the serving
protocol. The serving engine exposes generation to the harness, while the
harness owns tools, permissions, and stop conditions. Evaluation records both
model behavior and harness configuration because either can cause a failure.

Those ownership boundaries prevent a common debugging mistake: changing the
model when the bug is in the prompt loop, or changing the harness when the
checkpoint and tokenizer do not match.

## Definition of done

Completion requires more than eight scripts that start:

- every stage has an exact command and a run record;
- every published number traces to that record;
- the tokenizer, checkpoint, and serving configuration are identity-compatible;
- the agent calls the locally served model rather than a hosted replacement;
- checkpoint and evaluation artifacts can be reproduced from repository docs;
- total wall-clock and cost are reported;
- the final report names failure cases and the limits of its evidence.

The mission remains `draft` until all conditions are true.

## What this mission proves

When complete, it will prove that the language-model chain composes on the
declared hardware and that an engineer can inspect and replace each layer.
That is a systems claim, not a quality claim.

It will not prove that a small self-trained model beats a hosted frontier model,
that the agent creates business value, or that the same platform generalizes to
non-text decisions. Mission 02 exists to test that last claim with personalized
discovery, where the objective, data, serving path, and failure modes are
different.

## How to use the mission

Follow the stages in order when reproducing the complete path. When learning one
mechanism, enter through the relevant platform lesson and return here to see
which upstream and downstream contracts it affects.

Start with [stage 00](00-corpus/) if you want the full build. Start with
[stage 02](02-pretrain/) if your immediate goal is to understand how data,
architecture, optimization, and checkpoints become one training system.
