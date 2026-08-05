---
status: verified
level: foundation
verified: 2026-07-28
base: scratch
label: Pretraining
---

# What are you actually training?

**Question:** you have 3.16B tokens from [stage 00](../00-corpus/) and a
16,512-token vocabulary from [stage 01](../01-tokenizer/). What is the thing
you are about to spend five hours changing, and what is it being changed
toward?

**Say the purpose out loud first, because the result invites the wrong
conclusion.** The model this stage produces writes fluent English and is wrong
about nearly everything. It will not beat a hosted model at any task. That is
the expected outcome at 88M parameters, and it is not the point. The point is
that every mechanism downstream — loss masking in [SFT](../03-sft/), the KV
cache in [serving](../05-serve/), the capacity argument that decides where
[reinforcement learning](../04-rl/)
can honestly be taught — becomes something you can run and falsify instead of
something you read about. A model small enough to train in an afternoon is the
only one where that is true.

This chapter is the mechanism: what the data is, what the network does to it,
and what "wrong" means numerically. The next one,
[verifying the run](verifying-the-run/), is how you know a five-hour job is
working while it runs.

## The data is 3.01B tokens of one specific thing

Not "text". Four shards of FineWeb-Edu's `sample/10BT` — **2,916,000
documents, 3.01B tokens, 8.1GB** — which is Common Crawl already filtered by an
educational-quality classifier. Stage 00 built the equivalent pipeline by hand
and measured what its filters keep: of 20,000 raw HTML responses, 91% yield
extractable text, 36.7% survive English detection, 31.7% survive Gopher quality
rules, 24.3% survive C4's line filter, and 23.0% survive deduplication.

That last number is the one to hold on to. **Roughly four fifths of the raw
crawl is discarded before training sees any of it**, and the model that comes
out of this chapter is a model of what survived — encyclopedic, expository,
mostly grammatical prose. It has never seen a conversation, a tool call, or a
code review, which is exactly why stages 03 onward exist.

[`core/prepare_data.py`](core/prepare_data.py) turns those documents into two
flat files of `uint16` token IDs. Three decisions there are load-bearing:

- **Validation is written before training.** They are separate memory-mapped
  files, so a training window cannot reach into held-out data — not by
  convention, but because the bytes are not in the same file.
- **A reserved separator sits between documents.** Without it the model learns
  that the last sentence of one page predicts the first sentence of an
  unrelated one.
- **`uint16`, not `int32`.** A 16,512-token vocabulary fits in 16 bits, which
  halves storage and memory traffic at no cost. This is why stage 01's
  vocabulary size was a serving decision as well as a linguistic one.

## Is 3.0B tokens the right amount for 88M parameters?

The corpus is fixed and the model shape is not yet. The two are decided
together, because a dense decoder's training cost is set almost entirely by
their product:

$$
C \approx 6ND
$$

where $N$ is parameters and $D$ is training tokens. **Worked, on this run:**
$N = 88{,}197{,}888$ and $D = 3.0 \times 10^{9}$ give
$C \approx 6 \times 88.2\text{M} \times 3.0\text{B} = 1.59 \times 10^{18}$
FLOPs — 34 tokens per parameter, against the roughly 20 that Chinchilla's
compute-optimal result suggests. Being past that ratio is deliberate: the
optimal ratio minimizes loss for a *training* budget, while a model you intend
to serve is better spent past it, because inference cost tracks parameters and
not how long they were trained.

Run the estimate backwards and it becomes a schedule. The card here advertises
165 TFLOP/s in bf16, so a run converting every advertised FLOP into gradient
would finish in $1.59 \times 10^{18} / 1.65 \times 10^{14} = 9{,}622$ seconds
— 2.7 hours. The real run took **4.98 hours**, and nothing was wrong with it.
That ratio is what utilization means, and it is the subject of
[the throughput ladder](throughput/).

Move the budget below and keep three questions apart: what fits the training
compute, what uses the data you have, and what is affordable to serve forever
after.

<!-- interactive: ChinchillaBudget -->

The number to carry forward is the budget you can actually execute, not the
largest model that fits in memory for one forward pass.

## From token IDs to a guess about the next token

A token ID is an integer with no meaning. The first thing the network does is
look it up in a table of 16,512 rows of 768 numbers, and from that point on the
token *is* those 768 numbers — a position on a residual stream that every
layer reads from and writes back into.

Follow one token down that stream. Each half of a block reads a normalised
*copy* of the stream, computes, and adds its result back; the stream itself is
never overwritten. That is the property to watch, because it leaves an
unobstructed path from the loss back to layer 1, and it is why depth can be
added without redesigning anything else.

<!-- interactive: ModelArchitecture -->

Attention is the only place in the block where positions see each other;
SwiGLU transforms each position on its own and holds more than twice the
parameters. After twelve such blocks and a final norm, the same embedding table
is used in reverse — tied weights — to turn 768 numbers back into a score for
every one of the 16,512 tokens. That vector of scores is the model's entire
output. Everything else is arithmetic on it.

Move the key/value head count and watch two numbers move in opposite
directions. Dropping from 12 KV heads to 4 costs 9,437,184 parameters of
attention capacity and divides the KV cache by three, from 36,864 to 12,288
bytes per token. That trade is paid once at training time and collected on
every request for the life of the model, which is why
[serving](../05-serve/) cares about it more than training does. A detour from
here: [why is the KV cache the architecture's tax?](attention-variants/) walks
the same trade across the whole line — MHA, GQA, MQA, MLA — and draws each
variant's sharing pattern.

Another detour: [the gate that beats ReLU](the-gate-that-beats-relu/) —
SwiGLU's multiplicative mechanism measured against ReLU and GELU: no dead
zone, zero-mean output, and what the gate's form buys downstream.

## What "wrong" means

Scores are not probabilities. Softmax turns the 16,512 scores into a
distribution, and the objective asks one thing of it: put probability on the
token that actually comes next.

$$
\mathcal{L} = -\frac{1}{N}\sum_{i=1}^{N} \log p_\theta(x_{i+1} \mid x_{\le i})
$$

Three things in that expression carry the whole training loop. The target at
position $i$ is the input at position $i+1$ — **the sequence shifted left by
one** — so one forward pass supplies a target at every position simultaneously,
which is what makes pretraining efficient enough to be possible at all. The
$\log$ makes confident mistakes expensive without bound. And the mean over
$N$ positions is what turns 131,072 tokens of disagreement into the single
scalar the optimizer can differentiate.

Predict, before you move anything: if the loss is 3.0984, how often is the
model right?

<!-- interactive: NextTokenObjective -->

The conversion is the part worth remembering. A loss of 3.0689 nats means the
model puts about **4.65%** of its probability on the token that actually comes
next — one in 21.5. That is an enormous improvement over one in 16,512, and it
is nowhere near understanding the sentence.

## Why the starting loss is not zero and not arbitrary

A model that knows nothing can do no better than spread probability evenly.
Its loss is therefore the log of the vocabulary size:
$\ln(16{,}512) = 9.712$ nats. Every correctly initialised run must start
there — which makes the first number the training loop prints a complete test
of whether the labels, the mask, and the data splits are wired correctly.

This run measured **9.8697**, sitting 0.158 above the uniform line, the small
excess expected when weights are random rather than exactly uniform in effect.
Far *below* the line would mean the model is seeing the answer.

That single number costs one forward pass, and it is where the next chapter
starts.

## What this chapter does not establish

- **That any architecture choice here is a good one.** RMSNorm, RoPE, SwiGLU,
  and grouped-query attention are stated, not compared. One run with one seed
  cannot rank them.
  [Architecture ablations](architecture-ablations/)
  runs the comparison at a smaller size and finds RoPE decisively ahead of the
  alternatives, GQA's cost real and monotone — and RMSNorm and SwiGLU
  indistinguishable from theirs, each losing on one seed of three. Two of these
  four choices are so far unjustified by evidence, which is worth knowing.
- **That you could derive this update by hand.** Every gradient here comes
  from `loss.backward()`, which this chapter calls and never opens.
  [Backpropagation](../../../foundations/03-backpropagation/) builds the
  autodiff engine underneath it and checks it against hand-derived calculus.
- **That the model knows anything.** A falling loss measures next-token
  agreement with held-out web text, not truth. The next chapter shows what
  3.0689 looks like when you read it.
- **That this data mixture is right.** No alternative mixture was trained.
  [The ablation harness](../../../foundations/05-is-the-difference-real/) exists
  because answering that needs paired runs across seeds, not one run.
- **That this architecture is the only way to spend this checkpoint's
  weights.** [Upcycling](upcycling/) takes this
  exact dense checkpoint and asks whether converting it to a mixture-of-experts
  architecture buys back more capacity than it costs.

## Five more things you could change, and what each returns

Each of these takes one decision this chapter states without testing, and runs
it far enough to answer. None is a prerequisite; enter from the question.

**[Architecture ablations](architecture-ablations/)** — *did that design choice
actually help?* Six choices measured at a smaller size, on three seeds. RoPE
wins decisively, grouped-query attention's cost is real and monotone, and two
of this model's four choices turn out indistinguishable from the alternatives
they replaced.

**[The throughput ladder](throughput/)** — *is the run using the card it is
already on?* 14.69x between the slowest and fastest configuration of an
identical model, and which change bought which part of it.

**[Upcycling](upcycling/)** — *can a trained checkpoint become a different
architecture?* This exact dense checkpoint converted to a mixture of experts,
starting at its parent's loss, with [the follow-up](upcycling/does-it-pay-off/)
asking whether the added capacity earned back its cost.

**[When the curve goes wrong](when-the-curve-goes-wrong/)** — *the loss turned
upward and you do not know why.* A rule for deciding which subsystem owns the
evidence, plus the precision contract that decides whether an update lands at
all.

**[Latent reasoning](latent-reasoning/)** — *what if the model could think
without choosing words?* An open question kept honest: a stated hypothesis and
a comparison that has not yet earned a verdict.

For the case where the model no longer fits one card, the mechanism is
[distributed training](../../../foundations/04-distributed-training/), which is
product-independent and lives in foundations.

## Reproduce it

```bash
cd missions/01-language-model-agent/02-pretrain/core
python model.py                                    # parameter and KV-cache budget, no training
python prepare_data.py <parquet-dir> <tokenizer.json> --out-dir data/tokens
```

[`prod/train_prod.py`](prod/train_prod.py) runs the same configuration through
HuggingFace `Trainer` and `LlamaForCausalLM`. The two agree at exactly
88,197,888 parameters, because the four choices in
[`core/model.py`](core/model.py) are Llama's architecture written out longhand.

## Check your mental model

1. Roughly four fifths of the raw crawl is discarded before training. Name two
   filters that do that work and what each one is protecting against.

<details>
<summary>Answer</summary>

Any two of: English-language detection (guards against training on the wrong
language entirely — only 36.7% of extracted text survives it), Gopher quality
rules (guards against low-quality, boilerplate, or malformed text — 31.7%
survive), C4's line filter (guards against navigation menus, boilerplate
lines, and other non-prose junk — 24.3% survive), or deduplication (guards
against the model over-weighting duplicated content and wasting budget
re-learning the same text — 23.0% survive). Each filter protects against a
different way "raw HTML" fails to be the "encyclopedic, expository, mostly
grammatical prose" the chapter says the surviving 23% actually is.

</details>

2. Why does the loss use the sequence shifted left by one rather than a
   separate label file?

<details>
<summary>Answer</summary>

Because the target at position $i$ is just the input at position $i+1$ — the
next-token objective is defined entirely in terms of data the model already
has, shifted by one position. That's what lets one forward pass supply a
target at *every* position simultaneously (131,072 tokens' worth in one
optimizer step), rather than needing a separately authored or stored label
for each position. A separate label file would duplicate information already
present in the sequence itself and buy nothing the shift doesn't already
give for free — this is exactly what the chapter calls "what makes
pretraining efficient enough to be possible at all."

</details>

3. A validation loss of 3.0689 corresponds to what probability on the correct
   token? Why is perplexity a friendlier way to say the same thing?

<details>
<summary>Answer</summary>

Roughly 4.65% — one in 21.5, per the chapter's own conversion. Perplexity
(here, 21.5) is friendlier because it's stated in units a reader can picture
directly: "the model's uncertainty is like choosing uniformly among about 21.5
options," rather than a raw nats value like 3.0689 that only means something
once you've done $e^{-\mathcal{L}}$ in your head. Both numbers carry exactly
the same information; perplexity just undoes the log so the scale reads as a
count of plausible next tokens instead of an abstract loss unit.

</details>

4. Why must a correctly initialised model start at `ln(vocab_size)`, and what
   does a step-0 loss of 5 imply?

<details>
<summary>Answer</summary>

A model that knows nothing yet can do no better than spread probability
evenly across all 16,512 possible next tokens, and the loss of a uniform
distribution over $V$ options is exactly $\ln(V)$ — here $\ln(16{,}512) =
9.712$. Every correctly initialized run must start at (or very near) that
line, which is why the chapter calls step 0 "a complete test of whether the
labels, the mask, and the data splits are wired correctly." A step-0 loss of
5 is far *below* that line, which the chapter says means the model is
already seeing the answer — a label-shifting bug, an attention mask that lets
a position read the token it's supposed to predict, or a validation set that
overlaps training, not a lucky head start.

</details>

5. The KV cache shrinks with the key/value head count and the parameter count
   barely moves. Why is that trade decided at training time rather than at
   serving time?

<details>
<summary>Answer</summary>

Because the key/value head count is baked into the architecture that gets
trained — grouped-query attention's head count is fixed once the weights are
learned around it, not something a serving deployment can retune afterward
without retraining. The chapter's own numbers make the asymmetry concrete:
dropping from 12 to 4 KV heads costs 9,437,184 parameters of attention
capacity once, at training time, but the KV-cache-per-token savings (36,864
to 12,288 bytes) are "collected on every request for the life of the model" —
a one-time training cost that pays a serving-time dividend on every single
inference call, which is exactly why serving cares about this choice more
than training does even though training is where the choice gets locked in.

</details>

## Next

**Continue the mission at [stage 03 — SFT](../03-sft/)**, which takes this
checkpoint and teaches it to answer rather than continue.

Before you launch the run, though, one companion chapter is worth the ten
minutes: [verifying the run](verifying-the-run/) takes this exact configuration
and asks the operational question — five hours is a long time to be wrong, so
what can you check in the first minute, and what does the finished curve
actually license you to say?

[The training landscape](LANDSCAPE.md) pairs each from-scratch implementation
here with the production trainers and tokenizer libraries that replace it, and
says which difference is load-bearing at this scale and which is not.
