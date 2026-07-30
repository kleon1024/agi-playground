---
status: draft
level: foundation
label: Language-model system
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

**What this mission proves is a systems claim, not a quality claim**, and it is
worth saying before you spend the compute rather than after. The model at the
end of this chain writes fluent English and is wrong about nearly everything; a
hosted frontier model beats it on essentially every task. What the chain
establishes is that the layers are real and compose — and that every mechanism
in them is something you can run, break, and measure on hardware you own.

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
| [`02-pretrain`](02-pretrain/) | 88.2M decoder, token data path, the training objective, and a resumable checkpoint | **verified** — 3.0B tokens in 4.98h, best val loss 3.0689 |
| [`03-sft`](03-sft/) | chat template, assistant-only loss, and before/after behavior | **verified** — 9,500 conversations in 92.5s, best val loss 2.7828 |
| [`04-rl`](04-rl/) | GRPO updates against a verifiable reward | implementation present; run pending |
| [`05-serve`](05-serve/) | KV-cache decoding, paged allocation, and continuous batching | **verified** — the KV cache buys 1.21x at 32 tokens and *loses* by 512, and concurrency buys nothing until the kernel is fused |
| [`06-agent`](06-agent/) | bounded tool loop, grounding rule, context policy, and sandbox | **verified** — 0/6 against a served SFT checkpoint; the harness never once saw a parseable `Action:` |
| [`07-eval`](07-eval/) | disclosed harness, static and agentic tasks, variance, and failure cases | **verified** — perplexity 21.677, loglik 0.625/8, agent report 0/6 |

## Where the mission leaves the path, and what comes back

This mission is the path. Foundations, capabilities, and platform are libraries
it reaches into, and it reaches into them at a specific stage for a specific
decision — never as reading you do first. Each detour below returns something
the next stage consumes, which is the test for whether the detour was worth
taking.

| At this stage | You need to decide | So read | And bring back |
|---|---|---|---|
| before 02 | what a decoder block is doing at all | [the decoder block](../../foundations/00-attention/) | the forward path, and this model's 88,197,888 parameters reconstructed from its own formulas |
| 00 | which documents to keep, and whether the filter is defensible | [platform / data](../../platform/data/) | a versioned dataset with rejection reasons |
| 02 | whether an architecture choice is worth its cost | [architecture ablations](../../platform/training/02-architecture-ablations/) | six choices measured, two of which flip sign between seeds |
| 02 | why a run will take ten hours, and whether it should | [the throughput ladder](../../platform/training/03-throughput/) | tokens per second, MFU, and what to change |
| after 02 | whether to keep the checkpoint or retrain a new shape | [upcycling](../../platform/training/05-upcycling/) | a converted checkpoint that starts at the parent's loss |
| 03 | whether teacher data beats human data | [distillation](../../platform/adaptation/distillation/) | a target format and its tokenizer constraint |
| 04 | whether this base can be improved by RL at all | [reinforcement learning](../../platform/adaptation/reinforcement-learning/) | the condition under which the gradient is non-zero |
| 05 | what the model is doing between tokens | [platform / serving](../../platform/serving/) | the cost model for a request |
| 06 | how a tool loop stays bounded | [act and coordinate](../../capabilities/act-coordinate/) | a permission and stop-condition contract |
| 07 | what a number from a harness is worth | [evaluation and observability](../../platform/evaluation-observability/) | variance, and the disclosure a result needs |

Two chapters are deliberately not on this list.
[Mid-training](../../platform/adaptation/mid-training/) is skipped for the
reason below. [Latent reasoning](../../platform/training/04-latent-reasoning/)
is an open question rather than a decision this mission makes, and it is
labelled draft until a run says otherwise.

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

Follow the stages in order. When a stage poses a decision you cannot make yet,
take the detour the table above names, then come back with the artifact it
returns — that is the only reading order this repository has.

Start with [stage 00](00-corpus/) if you want the full build. Start with
[stage 02](02-pretrain/) if your immediate goal is to understand how data,
architecture, optimization, and checkpoints become one training system.

Do not read the platform section front to back. It is arranged by lifecycle
stage so it can be indexed, not so it can be studied in order, and reading it
that way produces an inventory of mechanisms with no decision attached to any
of them.
