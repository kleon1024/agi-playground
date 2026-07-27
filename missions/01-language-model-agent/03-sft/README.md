---
status: draft
base: scratch
---

# Stage 03 — Supervised fine-tuning

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

Pretraining and SFT optimize the same loss — next-token cross-entropy — over
data with a completely different distribution. Pretraining data is documents:
self-contained, no speaker turns, no expectation of response. SFT data is
dialogue: two roles, an expectation that role B replies to role A, and an
expectation that the reply ends. Training on dialogue-shaped text with a
document-shaped objective works only because we change *what counts toward
the loss*, not the objective itself — which is the whole reason loss masking,
covered next, is the central mechanism of this stage rather than a detail of
it.

It follows that SFT cannot fix what pretraining didn't put there. If the base
model never encountered a fact, formatting the question as a chat turn will
not produce it — SFT reliably surfaces knowledge and reframes behavior, it
does not add capability the base model didn't already have latent in it. See
the post-training chapter's
[supervision contract](../../../platform/adaptation/post-training/README.md#1-define-the-assistant-turn)
for the boundary between visible context and learned output.

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

This repo's tokenizer (stage 01) has no dedicated single-id tokens for chat
markers — it was trained purely on web documents, which have no such
concept. `core/sft.py` reuses two ids from the 127-id gap stage 02's `Config`
already reserved when it padded the vocabulary to a multiple of 128
(`16385` and `16386`, right after the document separator at `16384`) as
`<|im_start|>`/`<|im_end|>`. Production tokenizers instead reserve chat
special tokens *before* pretraining starts, specifically so the embedding
table never needs to grow later — this repo's padding-for-alignment habit
from stage 02 happens to leave exactly enough room to do the same trick
here, one stage later than usual, for free.

## Loss masking, worked

The loss is computed only on assistant tokens. Concretely: `labels[i]` equals
`ids[i]` wherever token `i` belongs to an assistant turn's content or its
closing `<|im_end|>`, and `-100` everywhere else. `-100` is not an arbitrary
sentinel — it is `torch.nn.functional.cross_entropy`'s default
`ignore_index`, so stage 02's `Transformer.forward` (which calls
`cross_entropy(logits, targets)` with no `ignore_index` argument) already
ignores it. No change to the frozen model is needed for it to become
SFT-aware; that is the reason `-100` is the field's near-universal choice for
masked labels, not a coincidence this lesson invented.

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

## Packing, and the limit of reusing a frozen model

A curated instruct set is short and length-variable — no_robots (below)
averages a few hundred tokens per example against a 1024-token block. Padding
every example out to the block size individually spends most of a batch's
forward pass on tokens that carry no signal. Packing instead concatenates
several short examples back-to-back into one sequence, closing a block only
once the next example no longer fits it, so a large majority of positions in
every block hold a real token from some conversation.

Packing has one correctness subtlety production trainers handle and this
lesson's `core/` cannot: once two unrelated conversations share a sequence,
a plain causal mask lets late tokens in conversation B attend to all of
conversation A, which is unrelated context. TRL and torchtune fix this with a
block-diagonal attention mask — each packed example gets causal attention
*only within itself*. `core/sft.py` reuses stage 02's `Attention.forward`
unmodified, which always calls `scaled_dot_product_attention(...,
is_causal=True)` over the whole sequence, so building a custom mask would
mean editing a file this stage is scoped not to touch. The lesson disclosed,
not hidden: packing here gets a small, documented attention leak; loss masking
is unaffected because it depends only on `labels`, never on attention, so the
model is never taught to predict the wrong token — it just occasionally
spends a little attention capacity on an irrelevant neighboring conversation.
`prod/trl_sft.py` runs the same recipe through `SFTConfig(packing=True)`,
which does not have this limitation, and its header comment says exactly why.

## Catastrophic forgetting, and why the learning rate drops ~30x

Stage 02 pretrained from a random initialization, so a large learning rate
early on is safe — there is nothing yet to disturb. SFT starts from a model
that already computes something useful, and the fine-tuning objective can
easily out-compete that: a peak LR anywhere near pretraining's (`6e-4` here)
applied to a converged model does not adjust it, it re-randomizes large
swaths of it before the objective has a chance to specialize gently.
`core/sft.py` defaults to `2e-5` — roughly 30x lower — for exactly this
reason, and runs a short warmup (30 steps, versus pretraining's 500) because
there are far fewer total steps to warm up across in the first place. This is
also why SFT trains for a handful of *epochs* over a small dataset rather than
a fraction of one epoch over a token budget: with roughly 10,000 examples
instead of billions of tokens, "run once" would barely move the model, and
"run for many epochs at a pretraining-scale LR" is precisely how you get
catastrophic forgetting — visible as fluent, grammatical text that has lost
whatever the base model previously knew.

## What SFT cannot fix

Restated plainly, because it is easy to lose sight of once a model starts
producing fluent chat-shaped output:

- **No new knowledge.** If it wasn't in the pretraining corpus, formatting the
  question as a chat turn does not put it there.
- **No ground truth.** SFT imitates the *style* of the training examples, not
  their correctness. A confidently-worded wrong answer in the training set
  teaches the model to be confidently wrong.
- **No preference signal.** SFT has one response per prompt to imitate; it has
  no way to express "this reply is better than that one." That comparison is
  what `05-rl` — RM training and the DPO family — is for.
- **Fixed at training time.** It does not compress well by ability alone: a
  small model given LIMA-quality data still has a small model's capacity.
  Zhou et al. (2023)'s ~1,000-example result (the "Superficial Alignment
  Hypothesis": pretraining already contains almost all the knowledge, SFT
  mostly teaches format and style) is an argument for curation over volume,
  not evidence that curation substitutes for scale.

## Reproducing

No GPU has run this stage yet — the commands below are the reproduction
recipe, not a report of a completed run. `runs/` will hold the actual
numbers, the exact dataset snapshot, and before/after samples once stage 02
has landed a checkpoint to fine-tune.

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

## Exercises

1. **Break the mask on purpose.** Comment out the loss-masking branch in
   `render_and_mask` so every token is trained on, run a few hundred steps,
   and sample from the result. Watch the model start generating plausible
   `<|im_start|>user\n...` turns of its own — the exact failure this stage
   exists to prevent.
2. **Measure the packing win directly.** Before calling `pack()`, compute what
   padding every example individually to `block_size` would cost in wasted
   positions, and compare it to `pack()`'s actual fill rate on the same data.
   The gap is a property of your data's length distribution, not a constant —
   confirm that for yourself rather than trusting a quoted number.
3. **Find the forgetting cliff.** Train the same run at `--lr 6e-4` (stage
   02's pretraining peak) for a few hundred steps and compare sample
   completions against the `2e-5` default on prompts unrelated to the
   fine-tuning data. Fluency usually survives; specific recall often doesn't.
4. **Swap the chat template.** Re-render the same dataset with an
   Alpaca-style (`### Instruction:` / `### Response:`) template instead of
   ChatML markers, fine-tune, then serve completions using the *other*
   template's boundary string. Confirm the model degrades toward base-model
   behavior — this is the "one consistent convention" claim, demonstrated
   rather than asserted.
5. **Read what no_robots actually contains.** Categories vary widely (open
   Q&A, rewrite, summarize, classify, coding, ...). Break the eval loss down
   by category and see whether the model improves uniformly or concentrates
   on whichever categories dominate the training count.

## Next

[Stage 04 — RL](../04-rl/): GRPO on a verifiable task, starting from this
stage's chat-tuned checkpoint. Everything here that stopped at imitating a
fixed dataset is the on-ramp — RL replaces "imitate this response" with
"prefer whichever response of several actually verifies as correct."
