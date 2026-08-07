---
status: verified
verified: 2026-08-05
level: applied
base: none
label: Mid-training
---

# Where does a base model learn to call a tool?

Your base model has never made one. So where does that behavior come from —
and why isn't the answer supervised fine-tuning?

No mission in this repository runs this stage, and
[the language-model system says why](../..):
an 88M base has no capacity for exposure at this scale to land in. You are here
to understand a stage you will read about in other people's model cards, and to
recognise when a project has skipped it and is asking SFT to do its job.

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
[SFT](../../03-sft/) ever asks it to behave like an assistant.
The boundary between the first two columns is a budget line, not a hard wall:
programmes also mix a small agentic slice into general pretraining itself,
concentrated in the annealing phase, at a single-digit share of tokens —
section 7 puts numbers and sources on that.

**Before this:** [pretraining](../), for the base checkpoint this stage would start from.
This chapter is about the stage between pretraining and post-training, so both
of its neighbours have to be in view.

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

A third route skips synthesis-from-a-knowledge-source entirely: distill
trajectories from a stronger model's real rollouts against agent tasks, then
fine-tune a smaller model on the captured behavior. AgentTuning (Zeng et al.,
"AgentTuning: Enabling Generalized Agent Abilities for LLMs," Findings of ACL
2024, arXiv:2310.12823) curates trajectories this way and fine-tunes a smaller
model on them; FireAct (Chen et al., "FireAct: Toward Language Agent
Fine-tuning," 2023, arXiv:2310.05915) reports the same core move, distilling a
strong prompted model's agent trajectories into a training mix. Both are real,
dated precedent for "distill from a strong model's agent rollouts" as an
established data-sourcing route — orthogonal to FAS/HAS, which synthesize
from a knowledge source rather than from another model's behavior.

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

## 5. What the trajectories actually look like

Both synthesis routes in section 4 produce think/act/observe transcripts, but
a corpus team receives agentic data in three shapes, and only one of them is
synthesized by hand. `core/format_agentic_text.py` renders all three the way a
pipeline would emit them; the full output and the metrics are in
[the run record](runs/2026-08-05-agentic-formats.md).

**Natural corpus text.** Jupyter notebook cell transcripts already sit in the
web crawl. The `# In[n]:` / `# Out[n]:` markers carry an action, an error, an
inspection, and a retry without any scaffolding:

```text
# In[3]:
df = pd.read_csv("sales.csv")
df.groupby("region")["revenue"].sum()

# Out[3]:
KeyError: 'revenue'

# In[4]:
df.columns
# Out[4]:
Index(['region', 'rev_usd', 'date'], dtype='object')

# In[5]:
df.groupby("region")["rev_usd"].sum()
# Out[5]:
region
APAC    1284000
EMEA     957000
```

This is the quasi-agentic family: the action -> error -> inspect -> fix arc is
real, but the model absorbs it as ambient text by volume, not as a deliberate
curriculum. Nothing separates code from its output, so the pattern is learned
statistically rather than from an explicit tool contract.

**Synthetic tool-use trajectories.** A declared tool schema, a user request, a
structured call, a result, and a final answer:

```text
<|user|>
Can you find flights from Singapore to Tokyo on Friday, and check the Tokyo weather that day?
<|tool_call|>
{"name": "search_flights", "arguments": {"origin": "SIN", "dest": "NRT", "date": "2026-08-07"}}
<|tool_result|>
{"flights": [{"flight": "SQ638", "dep": "09:30", "arr": "17:15", "price_usd": 412}, ...]}
<|tool_call|>
{"name": "get_weather", "arguments": {"city": "Tokyo", "date": "2026-08-07"}}
<|tool_result|>
{"forecast": "rain", "temp_c": [24, 29]}
<|assistant|>
Two flights on Friday: SQ638 departs 09:30 ($412) and JL712 departs 14:20 ($388). Tokyo has rain, 24-29 C.
```

Nothing goes wrong here. This is the clean-success shape: it teaches the loop
— call a tool, read what comes back, answer from it — and that is all it
teaches.

**SWE-style trajectories.** The same loop over shell and file tools, with the
failure left in: a test fails, the agent reads the offending code, edits it,
and re-runs:

```text
<|tool_call|>
{"name": "bash", "arguments": {"command": "python -m pytest test_parser.py -x"}}
<|tool_result|>
FAILED test_parser.py::test_empty_input - AttributeError: 'NoneType' object has no attribute 'strip'
<|tool_call|>
{"name": "read_file", "arguments": {"path": "parser.py", "lines": "40-55"}}
<|tool_result|>
42  def parse(text):
43      text = text.strip()
...
<|assistant|>
parse() does not handle a None input. Fix it.
<|tool_call|>
{"name": "str_replace", "arguments": {"path": "parser.py", "old": "def parse(text):\n    text = text.strip()", "new": "def parse(text):\n    if text is None:\n        return []\n    text = text.strip()"}}
<|tool_result|>
Edit applied.
<|tool_call|>
{"name": "bash", "arguments": {"command": "python -m pytest test_parser.py -x"}}
<|tool_result|>
1 passed in 0.12s
```

This is the highest-value family: it contains the recovery step the other two
lack. The run record's metrics make the difference legible — the clean
tool-use trajectory has no recovery; the SWE trajectory does, and it survives
the truncation and noise that section 7 describes.

## 6. A neutral format, not the eventual chat template

`core/mid_training_data.py` marks each step with a plain `<role:kind>` tag —
`<assistant:think>`, `<assistant:act>`, `<assistant:observe>` — not the
`<|im_start|>role\n...<|im_end|>` structure post-training's SFT stage renders:
[the SFT stage's `render_and_mask`](../../03-sft/core/sft.py)
reserves three special token ids (`IM_START`, `IM_END`, `PAD_ID`) for exactly
that ChatML-style template. The gap is not an oversight. Mid-training runs
long before post-training decides which chat template the shipped assistant
will actually use, so a model taught to structure trajectories around one
convention's special tokens has that structure to unlearn if SFT settles on a
different one. A neutral, portable shape — think, act, observe in plain
text, the same Thought/Action/Observation loop ReAct describes (Yao et al.,
"ReAct: Synergizing Reasoning and Acting in Language Models," ICLR 2023,
arXiv:2210.03629) — survives that later decision unmodified, because it never
committed to a template SFT might discard.

The trajectories in section 5 were recorded with `<|assistant|>`,
`<|tool_call|>`, and `<|tool_result|>` special tokens, and a corpus team has
two defensible options: convert them to neutral separators, or keep the
original format — never mix conventions. `core/format_agentic_text.py` renders
both (`--separators chat` vs `--separators neutral`), and the run record shows
the result: the neutral rendering is 22 characters shorter and identical in
token count, because the conversion changes the format contract, not the
content. The one thing that breaks a model is a vocabulary collision —
reserving special-token ids for a convention post-training later discards
(SFT's `render_and_mask` spends ids `16385`-`16387` on ChatML markers; a
pretraining mix that already committed those ids to `<|tool_call|>` would hand
the fine-tune an identity conflict to resolve).

What actually breaks when that structure is skipped or introduced too early
is worked out with a real failed run in
[the language-model system's agent chapter](../../06-agent/),
under "What does agentic training data actually need to teach?" — read that
section for the evidence rather than re-deriving it here.

## 7. Length, noise, and the mix

Two pipeline decisions and one corpus-level decision sit between "we have
trajectories" and "the model has seen them."

**Truncation is a budget, not a choice.** Real tool output is longer than any
fixed budget, so a pipeline caps every result — the run record renders a
60-character cap and the read_file result ends mid-sentence, and the
trajectory still resolves, which is exactly what a production token budget
does to a long log. The learner can change the cap and watch the rendered
trajectory change (`--max-result-chars`).

**Noise is what teaches recovery.** A corpus of clean-success trajectories
teaches the loop but never teaches what to do when a tool returns something
unexpected, because the model never sees an unexpected result. Real pipelines
inject the three failures a live tool actually returns — real errors,
timeouts, and empty results — and the format script's `--noise` flag
replaces the first tool result with one of them while keeping the fix-and-
recover arc (error -> inspect -> correct -> success). Noise on every result
instead of the first collapses the trajectory into all-failures and teaches
nothing; placement is part of the design.

**The mix is small and it is annealed.** Reported practice across programmes
is a single-digit-percent share of the corpus, concentrated in the annealing
phase rather than spread evenly over training — the closest dated published
anchor in this chapter is GLM-5's mid-training at roughly 5% of its
pretraining budget (section 3). Neither number is a measured optimum from this
repository; both are reported practice, stated as such. The corpus-level view
— what the mixture weights are, and how a deliberate agentic component
differs from the weak notebook traces the web funnel happens to keep — is
[the corpus stage's mixture chapter](../../00-corpus/what-a-release-needs/).
The downstream cost of getting the mix wrong is measured, not hypothetical:
the language-model system's agent run scored 0/6 against a checkpoint that
never saw an agentic-formatted example
([stage 06](../../06-agent/)).

## 8. Loss masking on observations

Both synthesis routes produce a transcript containing three kinds of text:
what the model decided (think), what it did (act), and what came back
(observe). Training loss on all three teaches the model to generate
convincing tool output — a model that has learned to predict its own
observations has learned to fabricate them at inference time, when no real
result exists yet to condition on.

The standard mitigation in agentic SFT is the same idea
[SFT](../../03-sft/) already established for user turns: mask
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

## Who owns the loop

Mid-training is a data-health stage with a three-way handoff:

- **The data-pipeline team** owns the trajectory sourcing (FAS, HAS, or
  distillation from a stronger model's rollouts), the quality filter on
  synthesized trajectories (Agentic CPT's LLM-based check: 50% to 82% of
  synthesized items judged correct), the format decision — neutral
  separators, no special-token vocabulary collision with post-training —
  and the mix share and anneal placement. It owns the number, not the
  target.
- **The evaluation team** owns the slice read: agentic and general evals
  measured separately after any mix change, the guardrail thresholds, and
  the case-finding step an aggregate cannot do. It owns the evidence that
  the mix moved the model in the intended direction without silently
  paying for it elsewhere.
- **The model team** owns the contract: which eval is primary, where the
  guardrail binds, and the masking decision — which spans pay loss and
  which are context-only. When the ownership is implicit, the stage is
  skipped or its settings are whatever the last config edit left them, and
  SFT is quietly asked to install a capability it was never given the
  budget to install.

## The fix and its trade

The fix is to treat mid-training as a stage with a declared contract
instead of a pipeline detail: a named mix share placed in the annealing
phase, a neutral trajectory format, masked observation tokens, and a
pre-declared primary eval with guardrails on the others — the decision
executed in [when the annealed slice moves the evals](when-the-annealed-slice-moves-the-evals/).
Each choice in that contract trades something named: the neutral format
trades special-token efficiency for template portability across whatever
SFT later decides; masking trades a little learning signal for the
anti-fabrication guarantee that the model never learns to generate its own
tool output; noise trades clean trajectories for harder ones so recovery
is learned at all; and the mix contract trades the freedom to chase a green
metric for the ability to attribute what a change actually did. The budget
line — 300B tokens for Agentic CPT, roughly 5% of pretraining for GLM-5 —
is what makes the trade irreversible: at that scale the stage is not
something a programme re-runs on a hunch, which is exactly why the
contract has to be written before the run, not after.

## 9. Evidence boundary

This chapter cites five dated, external reports and demonstrates the
mechanism the first two describe at a scale a single machine can execute. It
does not demonstrate: a 300B-token training run — no lane in this repository
reaches that budget, see [the compute-lane guides](../../../reference/tracking.md); a measured comparison of
"install the prior first" against "train it all during post-training," which
is the source paper's argument and is not re-derived here; that FAS/HAS
filtering generalizes beyond the two programmes that reported it; or the
AgentTuning/FireAct route to trajectory distillation itself — those two are
cited as precedent for where such data can come from, not implemented in
`core/` or `prod/`, which stay on the FAS/HAS synthesis path. `core/` and
`prod/` synthesize trajectories and mask observations correctly at toy
scale — they do not show that either technique still behaves the same way at
hundreds of billions of tokens.

The new run in this chapter (2026-08-05) demonstrates the three trajectory
shapes, separator conversion, truncation, and noise injection as rendered
output. It does not demonstrate: that any particular mix ratio or noise rate
improves a trained model (a training-run claim no single machine here can
make, and the mixing figures above are labeled practice, not measurement); or
that these scripted formats match what a specific production pipeline emits —
they are representative shapes, rendered by this repository's own code.

## Run the working path

`core/mid_training_data.py` builds a first-order trajectory from a toy
knowledge base, expands it into a high-order one with an explicit correction
step, and renders both with observation tokens masked out of the loss.
`core/format_agentic_text.py` renders the three trajectory families from
section 5 and demonstrates the separator, truncation, and noise decisions
from sections 6 and 7 with flags.
`prod/chat_template_masking.py` renders the same trajectories through a real
tokenizer's chat template, which is closer to how a production pipeline would
actually compute the mask. Neither script trains a model — the
[run record](runs/2026-08-05-agentic-formats.md) covers all three scripts, and
this chapter is `status: verified` for the mechanisms it demonstrates, not
for a training run (see the evidence boundary above).

## Check your mental model

Answer each before opening it.

**1. Why does installing an agentic prior cost pretraining-scale tokens rather
than SFT-scale tokens?**

<details>
<summary>Answer</summary>

Because deciding to call a tool mid-response, reading unpredictable output,
and continuing the reasoning after it is a genuinely new behavioral pattern,
not a small adjustment to format or turn-taking — and SFT's small, reviewed
demonstration set (sized in the millions of tokens) is designed for the
latter, not the former. The Agentic CPT paper's own numbers make the scale
concrete: 300 billion tokens across two context-length stages, before any
SFT or RL runs on top. That is a pretraining-scale intervention by any
convention, which is exactly why this chapter's pipeline diagram places it as
its own stage rather than folding it into either neighbor.

</details>

**2. What does the Agentic CPT paper argue goes wrong if that prior is installed
during post-training instead?**

<details>
<summary>Answer</summary>

It argues that folding agentic-prior installation into post-training asks one
optimization to do two incompatible jobs from the same small, carefully
curated signal at once: acquire a genuinely new behavioral pattern (tool use)
while also staying aligned to human preference. The gradient that best
teaches tool use is rarely the gradient that best preserves already-tuned
helpfulness and safety behavior, so pushing both through the same SFT/RL
signal sets them against each other. Installing the behavioral prior earlier,
under the plain next-token objective at pretraining scale, separates the two
problems — post-training then only has to align a model that already knows
how to act, rather than teaching it to act and align in the same pass.

</details>

**3. Why does context-length extension end up sharing a stage with
agentic-prior installation rather than happening on its own?**

<details>
<summary>Answer</summary>

Because both jobs want the same kind of input: long documents built from real
dependency chains, at the same token scale. Real agentic trajectories —
think, call a tool, read the result, continue, repeat — routinely run
64K-128K tokens before reaching an answer, which means training a model to
hold an agentic episode together already requires exactly the long-context
training data that context extension needs. GLM-5's three-band mid-training
schedule (32K, then 128K, then 200K) makes this explicit rather than
coincidental — the two jobs merge into one stage because the data that serves
one job serves the other equally well.

</details>

**4. What is the difference between what First-order and High-order Action
Synthesis each start from?**

<details>
<summary>Answer</summary>

First-order Action Synthesis (FAS) builds think/act/observe tuples directly
from a knowledge source, with the observation generated to stay consistent
with that source rather than returned by a live tool call — it constructs a
single clean trajectory from scratch. High-order Action Synthesis (HAS)
starts from an existing trajectory and expands it into a fuller decision
process: a wrong first attempt, an observation that reveals the mismatch,
and a corrected step. FAS produces one clean shot; HAS produces a trajectory
that includes getting something wrong and recovering from it.

</details>

**5. Why does this chapter's trajectory format stay neutral plain text instead
of adopting the special-token chat template SFT will eventually use?**

<details>
<summary>Answer</summary>

Because mid-training runs before post-training has decided which chat
template the shipped assistant will use, and committing to one convention's
special tokens (`<|im_start|>role\n...<|im_end|>`, as SFT's `render_and_mask`
renders) early would leave the model with that specific structure to unlearn
if SFT ends up settling on a different template. A neutral shape — think, act,
observe as plain text, the same loop ReAct describes — carries the behavioral
prior without betting on a template choice that has not been made yet, so it
survives unmodified whatever SFT decides later.

</details>

**6. What failure does masking the loss on observation tokens prevent, and what
does the model still see despite the mask?**

<details>
<summary>Answer</summary>

It prevents the model from learning to fabricate tool output. If training
loss ran on all three spans (think, act, observe), the model would learn to
generate convincing observation text as if predicting it were the goal — but
at inference time, no real tool result exists yet at the point the model
needs to condition on one, so a model trained to predict observations has
learned to hallucinate them instead of waiting for and using a real result.
Despite the mask, the model still *sees* the observation tokens in context —
conditioning on a real or synthesized tool result is exactly the skill being
trained — the mask only removes the gradient that would otherwise reward
reproducing that text, via `-100` in the loss (`CrossEntropyLoss`'s ignored
index) over every observation span.

</details>

**7. Why does a corpus of only clean-success trajectories fail to teach
recovery, and what does the format script's `--noise` flag do about it?**

<details>
<summary>Answer</summary>

Because the model never sees the thing it has to recover from. A clean-success
corpus teaches the loop — call a tool, read a valid result, continue — but
there is no example of an error, a timeout, or an empty result, so there is
nothing to condition a corrective step on. `--noise` replaces the *first*
tool result with one of those failures and leaves the rest clean, so the
rendered trajectory keeps its recovery shape (error -> inspect -> correct ->
success). Replacing every result instead collapses the trajectory into
all-failures, which is the degenerate version of the same design.

</details>

**8. Where in the training schedule does a small agentic slice usually sit,
and at roughly what share?**

<details>
<summary>Answer</summary>

Concentrated in the annealing phase, at a single-digit-percent share of the
corpus, per reported practice across programmes. The closest dated published
anchor in this chapter is GLM-5's mid-training at roughly 5% of its
pretraining budget. Neither figure is a measured optimum from this repository
— the chapter's own run renders formats and demonstrates the mechanics, and
the evidence boundary says so explicitly.

</details>

## Next

The output of mid-training is a base model that has already seen tool calls,
long dependency chains, and corrected mistakes under the plain next-token
objective. Continue to [SFT](../../03-sft/) to see what changes
when that same model is trained on a demonstration or a preference pair
instead.

The mix decision this stage's section 7 reports as practice is executed in
[when the annealed slice moves the evals](when-the-annealed-slice-moves-the-evals/):
the two-eval seesaw, the guardrail contract that decides where the share
stops, and why a blended metric rewards the move that breaks it.

Primary references: Scaling Agents via Continual Pre-training
(arXiv:2509.13310, 2025); GLM-5 data story (Kili Technology, 2026); AgentTuning
(Zeng et al., Findings of ACL 2024, arXiv:2310.12823); FireAct (Chen et al.,
2023, arXiv:2310.05915); ReAct (Yao et al., ICLR 2023, arXiv:2210.03629).
