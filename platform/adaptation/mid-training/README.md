---
status: draft
base: none
label: Mid-training
---

# Mid-training

**Question:** your base model has never made a tool call. Where does that
behavior come from — and why isn't the answer supervised fine-tuning?

The three contracts read as one pipeline:

```text
pretraining        -> mid-training               -> post-training
next-token loss       still next-token loss,         demonstration / preference
over web text         over synthesized agentic       loss over assistant turns
                       trajectories, longer context
```

All three stages train the same next-token objective on different documents.
Mid-training is the stage that decides whether the model has already seen a
think, call a tool, read the result, continue episode before
[post-training](../post-training/) ever asks it to behave like an assistant.

## 1. The scale mismatch

Post-training's SFT step runs on a small, reviewed demonstration set — sized
in the millions of tokens, because SFT's job is teaching format and
turn-taking, not new capability. Agentic behavior — deciding to call a tool
mid-response, reading unpredictable output, continuing the reasoning after
it — is a different kind of update. The one documented attempt to install it,
Agentic Continual Pre-training (Agentic CPT), used two stages:

$$
T_{\text{ACPT}} = \underbrace{200\text{B}}_{\text{32K context}} +
\underbrace{100\text{B}}_{\text{128K context}} = 300\text{B tokens}
$$

before any SFT or RL runs on top of it (*Scaling Agents via Continual
Pre-training*, arXiv:2509.13310, 2025). Three hundred billion tokens is not a
fine-tuning budget by any convention; it is a pretraining-scale intervention,
whatever stage of the pipeline it happens to occupy. That is the variable
worth watching as it moves between programmes:

<!-- interactive: TrainingStages -->

## 2. The optimization-conflict argument

If installing an agentic prior costs pretraining-scale tokens, why not fold it
into post-training and just train longer there? The Agentic CPT paper's own
argument is that this asks one optimization to do two incompatible jobs at
once: acquire a new behavioral pattern (when to call a tool, how to read what
comes back) and stay aligned to human preference, from the same small,
carefully curated post-training signal. Pushing both objectives through SFT
and RL sets them against each other — the gradient that best teaches tool use
is rarely the gradient that best preserves helpfulness and safety behavior
already tuned in. Installing the behavioral prior earlier, at pretraining
scale under the plain next-token objective, separates the two problems:
post-training then only has to align a model that already knows how to act,
instead of teaching it to act and to align in the same pass.

## 3. Long-context extension rides along

The two-stage split in section 1 is not arbitrary — 32K tokens, then 128K.
Real agentic trajectories are long: one episode of thinking, calling a tool,
reading its output, and continuing several times over routinely runs
64K-128K tokens before it reaches an answer. Training the model to extend its
usable context and training it to hold an agentic episode together want the
same input — long documents built from real dependency chains, at the same
token scale — so the two jobs merge into one stage rather than staying two.
GLM-5 (2026) makes the same choice explicit, running mid-training in three
context bands after its general pretraining:

$$
T_{\text{GLM-5 mid-train}} = \underbrace{1\text{T}}_{32K} +
\underbrace{500\text{B}}_{128K} + \underbrace{50\text{B}}_{200K}
\approx 1.55\text{T tokens}
$$

against roughly 28.5T tokens of general-and-code pretraining — mid-training
here is about 5% of the pretraining budget, not a rounding error bolted onto
it (Kili Technology, "Data Story: GLM Model Family," 2026). Long-context
extension and agentic-prior installation are not two adjacent stages that
happen to sit next to each other; in both programmes they are one stage.

## 4. Where the data comes from

Neither token count in sections 1 and 3 comes from recorded human-supervised
agent transcripts — real trajectories at that volume do not exist. The
tokens are synthesized, and the two published routes differ in what they
synthesize from:

- **First-order Action Synthesis (FAS)** builds think, act, observe tuples
  directly from a knowledge source, without ever calling a live tool. The
  observation is generated to stay consistent with the source, not returned
  by a running API.
- **High-order Action Synthesis (HAS)** starts from an existing trajectory and
  expands it into a decision process — a wrong first attempt, an observation
  that shows the mismatch, and a corrected step — rather than a single clean
  imitation of the right answer.

Synthesis without live tool execution is not free of quality control just
because no API call actually ran. The Agentic CPT report puts a number on that:
passing FAS output through an LLM-based quality check raised the share of
synthesized items judged correct from 50% to 82%. Read that as a statement
about the generated data, not about a trained model's accuracy — half of what
first-order synthesis produced did not survive review.

`core/mid_training_data.py` builds a small FAS trajectory from a five-fact toy
knowledge base and then a HAS expansion of it, so the difference between one
clean shot and a decision process with feedback is something you can read
token by token instead of taking on faith.

## 5. Loss masking on observations

Both synthesis routes produce a transcript containing three kinds of text:
what the model decided (think), what it did (act), and what came back
(observe). Training loss on all three teaches the model to generate
convincing tool output — a model that has learned to predict its own
observations has learned to fabricate them at inference time, when no real
result exists yet to condition on.

The standard mitigation in agentic SFT is the same idea
[post-training](../post-training/) already established for user turns: mask
the loss on observation tokens. The model still sees them in context —
conditioning on a real or synthesized tool result is exactly the skill being
trained — but no gradient asks it to reproduce them. Only the think and act
spans stay in the loss. Neither source cited in this chapter documents its
own masking implementation, so this is stated as prevailing practice in
agentic SFT, not as a detail either paper confirms.

`core/mid_training_data.py` renders exactly this: token ids and a same-length
label array with `-100` (`CrossEntropyLoss`'s ignored index) over every
observation span, and `prod/chat_template_masking.py` reproduces the same mask
through a real tokenizer's chat template instead of the toy one, so the
mechanism is visibly the one instruction-tuning already used.

## 6. Evidence boundary

This chapter cites two dated, external reports and demonstrates the mechanism
they describe at a scale a single machine can execute. It does not
demonstrate: a 300B-token training run — no lane in this repository reaches
that budget, see [`infra/`](../../../infra/); a measured comparison of
"install the prior first" against "train it all during post-training," which
is the source paper's argument and is not re-derived here; or that FAS/HAS
filtering generalizes beyond the two programmes that reported it. `core/` and
`prod/` synthesize trajectories and mask observations correctly at toy
scale — they do not show that either technique still behaves the same way at
hundreds of billions of tokens.

## Run the working path

`core/mid_training_data.py` builds a first-order trajectory from a toy
knowledge base, expands it into a high-order one with an explicit correction
step, and renders both with observation tokens masked out of the loss.
`prod/chat_template_masking.py` renders the same trajectories through a real
tokenizer's chat template, which is closer to how a production pipeline would
actually compute the mask. Neither script trains a model — there is no
`runs/` directory yet, and this chapter stays `status: draft` until one
exists.

## Check your mental model

1. Why does installing an agentic prior cost pretraining-scale tokens rather
   than SFT-scale tokens?
2. What does the Agentic CPT paper argue goes wrong if that prior is installed
   during post-training instead?
3. Why does context-length extension end up sharing a stage with
   agentic-prior installation rather than happening on its own?
4. What is the difference between what First-order and High-order Action
   Synthesis each start from?
5. What failure does masking the loss on observation tokens prevent, and what
   does the model still see despite the mask?

## Next

The output of mid-training is a base model that has already seen tool calls,
long dependency chains, and corrected mistakes under the plain next-token
objective. Continue to [post-training](../post-training/) to see what changes
when that same model is trained on a demonstration or a preference pair
instead.

Primary references: Scaling Agents via Continual Pre-training
(arXiv:2509.13310, 2025); GLM-5 data story (Kili Technology, 2026).
