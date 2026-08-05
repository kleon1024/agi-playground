---
status: verified
level: foundation
verified: 2026-07-28
base: scratch
label: SFT
---

# How does a text predictor learn to answer?

**Goal:** turn stage 02's base model — a next-token predictor over web
documents, with no notion of "answer the question" — into a model that
recognizes a conversation, answers in it, and stops when its turn is over.

A base model is not shy about conversation, it is simply indifferent to it.
Asked "What causes seasons on Earth?", the highest-probability continuation of
that string in web text is not necessarily an answer — it might be a follow-up
question, a forum reply header, or the start of an unrelated paragraph,
because all of those are things that follow question-shaped text somewhere in
a crawl. SFT does not teach the model new facts about seasons; the facts, if
they are there at all, came from pretraining. It teaches the model the *shape*
of a reply: which tokens are "mine" versus "the user's," and where a turn
ends.

## Why this is not "more pretraining"

Open stage 00's cleaned text next to a no_robots conversation and compare their
shape. Pretraining data is documents: self-contained, no speaker turns, no
expectation of response. SFT data is dialogue: two roles, an expectation that
role B replies to role A, and an expectation that the reply ends. Pretraining
and SFT still optimize the same loss — next-token cross-entropy — over that
different distribution, and you make dialogue-shaped text trainable under a
document-shaped objective by changing *what counts toward the loss*, not the
objective — which is why loss masking, covered next, is this stage's central
mechanism rather than a detail of it.

It follows that SFT cannot fix what pretraining did not put there. If the base
model never encountered a fact, formatting the question as a chat turn will not
produce it. SFT surfaces knowledge and reframes behavior; it does not add
capability the base model lacked — installing a behaviour the base has never
produced at all is a pretraining-scale problem, surveyed in
[mid-training](../../../reference/research/mid-training/).

## The chat template is a learned convention, not a magic string

`<|im_start|>user\nWhat causes seasons on Earth?<|im_end|>\n<|im_start|>assistant\n`
looks like syntax. It is not — it is arbitrary text that becomes meaningful
only because the model is trained to treat it as a turn boundary. Nothing
about the bytes `<|im_start|>` inherently marks anything; a model fine-tuned
with `### Instruction:` / `### Response:` (the older Alpaca convention) learns
that boundary instead, equally well. What matters is that **exactly one**
convention is used, consistently, at train and inference time. Serve a
ChatML-tuned model with Alpaca-formatted prompts and it degrades toward its
untuned base behavior, because the input no longer resembles anything it was
trained to recognize as "a turn."

This repo's tokenizer has no chat-marker ids — it was trained on web documents,
which have no such concept. `core/sft.py` takes `16385` and `16386` from the
127-id gap stage 02 left when it padded the vocabulary to a multiple of 128.
Production tokenizers reserve chat tokens *before* pretraining so the embedding
table never has to grow; padding for alignment happens to leave exactly enough
room to do the same thing one stage late, for free.

## Loss masking, worked

Open `render_and_mask` and watch what it does to `labels[i]`: it copies
`ids[i]` wherever token `i` belongs to an assistant turn's content or its
closing `<|im_end|>`, and writes `-100` everywhere else. That is the whole
mechanism — the loss is computed only on assistant tokens. `-100` is not an
arbitrary sentinel you're asked to take on faith: it is
`torch.nn.functional.cross_entropy`'s default `ignore_index`, so stage 02's
`Transformer.forward` (which calls `cross_entropy(logits, targets)` with no
`ignore_index` argument) already ignores it, with no change to the frozen
model needed for it to become SFT-aware. That is why `-100` is the field's
near-universal choice for masked labels, not a coincidence this lesson
invented.

For one assistant turn — say the tokenizer renders "yes." as three tokens —
the sequence and its labels look like this:

```
ids     <|im_start|>  assistant  \n   yes    .   <|im_end|>   \n
labels      -100         -100  -100   yes    .   <|im_end|>  -100
                └──────── prompt: masked ────────┘└trained┘└masked┘
```

Everything up to and including `assistant\n` is context the harness supplies
at inference time — the model is never asked to produce it, so training on
it wastes compute and, worse, teaches the model that generating a plausible
`<|im_start|>user\n...` is also a valid thing to do (the exact failure mode
of skipping this step: the fine-tune quietly re-teaches the model to write
both sides of the conversation). The closing `<|im_end|>` **is** trained on
deliberately — it is the token that tells the model when to stop, and a model
that never sees it as a target never learns to stop cleanly, running on until
it hits the length limit instead.

`core/sft.py`'s `render_and_mask` builds exactly this, turn by turn, for every
row of the dataset; read it before reading anything else in this lesson.

Toggle prompt supervision below and compare what the optimizer is being asked
to reproduce. The token sequence stays fixed; only the loss boundary changes.

<!-- interactive: AssistantLossMask -->

## It answers now. What did that cost?

The mechanism is cheap: a template and a mask. Three costs are not visible in
the loss curve. Packing finishes this stage in ninety seconds by putting
unrelated conversations in one sequence, which has a consequence. The learning
rate has to fall roughly thirtyfold, for a reason that is not numerical
stability. And one class of complaint about a fine-tuned model cannot be fixed
with better data at all.

[What did that cost?](what-it-costs/) takes those in turn, including the
attention leak this lesson's `core/` accepts on purpose and what its blast
radius actually is.

## What it actually did

Three epochs over 9,500 hand-written conversations took **92.5 seconds** on a
24GB card and moved validation loss from 3.1829 to a best of **2.7828**. The
behavioural change is visible without a benchmark. The base model, given a
question, continued it; this model answers it:

> **What are 5 things I can do when it's raining in London?**
> Celebrate the day with these 5 things you can do when it's raining in London.
> Have fun with your friends, be active, and find out more!
>
> 1. Find some local shops or bookstores. [...]

It produces a heading and starts a list because it was asked for five things,
and it stops — neither of which the base model would do. It is also still
wrong about everything:

> **What are some good desserts that use chocolate?**
> Candy, chocolate, and chocolate, are the two popular desserts for children.

A sentence with the shape of an answer and no content. That pairing is the
result to carry forward: **SFT changed the form of the output and nothing about
what the model knows**, which is what 9.8M tokens of instruction data can and
cannot do to a model that saw 3.00B tokens of pretraining.

Two costs of the 1,024-token context arrive here rather than in stage 02.
Packing leaves **19.6% of trained positions as padding**, and **217
conversations — 2.3% of the dataset — were discarded outright** for exceeding a
single block. Neither was measured for impact; both are recorded because they
are real.

One number invites a false reading. Step 0 measures 3.1829 while pretraining
ended at 3.0984, which looks like a regression and is not: different held-out
distribution, loss counted only on assistant tokens, through a template the
model has never seen. The only honest baseline for an SFT curve is its own
step 0.

Command, hardware, software versions, the full curve, all six generations, and
the two setup defects worth knowing about are in
[`runs/2026-07-28-sft-no-robots.md`](runs/2026-07-28-sft-no-robots.md).

**Is that result a size effect?** The run shows form-yes, content-no at 88M,
but one point cannot tell you whether that is what SFT does at every scale or
what 88M specifically can and cannot hold. [What model size changes](what-model-size-changes/)
runs the same recipe at 5M — from a pretrained base and from random init —
and reads the resulting axis against dated results at 65B-plus. Both arms
produce word fragments, which is the low end of the story the main run's
fluent-but-wrong output belongs to.

## Reproducing

```bash
# fine-tune stage 02's checkpoint on HuggingFaceH4/no_robots
python core/sft.py train \
    --tokenizer ../01-tokenizer/tokenizer_hf.json \
    --init-checkpoint ../02-pretrain/ckpt/ckpt.pt \
    --out ckpt

# compare identical prompts before and after — point --checkpoint at either
python core/sft.py sample --tokenizer ../01-tokenizer/tokenizer_hf.json \
    --checkpoint ../02-pretrain/ckpt/ckpt.pt \
    --prompt "What causes seasons on Earth?"          # the "before"
python core/sft.py sample --tokenizer ../01-tokenizer/tokenizer_hf.json \
    --checkpoint ckpt/ckpt.pt \
    --prompt "What causes seasons on Earth?"          # the "after"

# the same recipe through TRL's SFTTrainer, on a small public stand-in model
python prod/trl_sft.py --model HuggingFaceTB/SmolLM2-135M --out ckpt-trl
```

`--tokenizer` in both scripts expects the HF-format export from stage 01's
[`prod/hf_tokenizer.py`](../01-tokenizer/prod/hf_tokenizer.py) (`export`
subcommand), not the pure-Python `tokenizer.json` — SFT needs `tokenizers`'
Rust encoder for speed on a real dataset, the same substitution stage 02's
`prepare_data.py` already made and verified.

## Check the wiring before you add examples

The first evidence that this worked is not a benchmark average. It is a
before-and-after set of fixed prompts showing the model enters, answers, and
exits the assistant turn correctly — which is what the samples above are. Four
failure modes are worth checking on a new dataset before deciding you need more
of it, because each one produces a plausible loss curve:

- an answer is truncated at the block limit but still trained on as if complete;
- the user prompt leaks into the supervised region (exercise 1 induces this);
- duplicate templates dominate, so the model learns one house style rather than
  the task;
- validation prompts are paraphrases of training records, so the held-out loss
  is measuring memorization.

## Three things to do with a checkpoint that are not this

This stage moved every weight, using demonstrations somebody wrote. Three other
adaptation methods start from different constraints, and mission 01 ran exactly
one of them.

**[Beyond demonstrations](beyond-demonstrations/)** — *what if nobody wrote the
answer, or the model is too big to fine-tune whole?* LoRA and QLoRA, reward
models, the DPO family, and task-vector merging, worked against this model's real
shapes. No run: this checkpoint is small enough that full fine-tuning is cheap.

**[Distillation](distillation/)** — *what can you copy from a better model?* The
one that was run here, and the answer turned out to constrain the student's
tokenizer rather than only its weights.

**[Stage 04 — RL](../04-rl/)** — *what if the model has to generate the answer
and be scored on it?* Everything above stays offline; none of it can prefer a
response that is absent from the dataset.

## Exercises

1. **Break the mask on purpose.** Comment out the loss-masking branch in
   `render_and_mask` so every token is trained on, run a few hundred steps,
   and sample from the result. Watch the model start generating plausible
   `<|im_start|>user\n...` turns of its own — the exact failure this stage
   exists to prevent.
2. **Find the forgetting cliff.** Train the same run at `--lr 6e-4` (stage
   02's pretraining peak) for a few hundred steps and compare sample
   completions against the `2e-5` default on prompts unrelated to the
   fine-tuning data. Fluency usually survives; specific recall often doesn't.
3. **Swap the chat template.** Re-render the same dataset with an
   Alpaca-style (`### Instruction:` / `### Response:`) template instead of
   ChatML markers, fine-tune, then serve completions using the *other*
   template's boundary string. Confirm the model degrades toward base-model
   behavior — this is the "one consistent convention" claim, demonstrated
   rather than asserted.
4. **Read what no_robots actually contains.** Categories vary widely (open
   Q&A, rewrite, summarize, classify, coding, ...). Break the eval loss down
   by category and see whether the model improves uniformly or concentrates
   on whichever categories dominate the training count.

## Next

[What did that cost?](what-it-costs/) covers packing's attention leak, the
thirtyfold learning-rate drop, and the four limits better data does not move.
[The post-training landscape](LANDSCAPE.md) pairs the from-scratch trainer here
with the libraries that ship these algorithms, and says where their defaults
disagree with what this stage argues.
Then [stage 04 — RL](../04-rl/): GRPO on a verifiable task, starting from this
stage's chat-tuned checkpoint. Everything here that stopped at imitating a
fixed dataset is the on-ramp — RL replaces "imitate this response" with
"prefer whichever response of several actually verifies as correct."
