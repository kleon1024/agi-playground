---
status: draft
level: applied
label: Evaluation
---

# What evidence justifies replacing what you already run?

And when the candidate wins, which part of that evidence belongs to the model,
which to the harness, and which to the serving configuration?

Start with [metric gaming](01-metric-gaming/) if you have not yet seen why a
proxy metric's meaning can invert under the optimization pressure the rest of
this chapter assumes you already trust it against.

Every mission ends here: [language-model system stage 07](../../missions/01-language-model-agent/07-eval/),
[discovery stage 09](../../missions/02-personalized-discovery/09-report/), and
[quantitative research stage 05](../../missions/03-quantitative-research/05-report/)
all need the same thing — variance, and the disclosure a result has to carry
before it means anything. Take that back to whichever one sent you.

Begin with a decision, not a benchmark:

```text
candidate change
  -> stated hypothesis
  -> evaluation unit and slices
  -> repeated measurement
  -> guardrail check
  -> ship, reject, or investigate
```

The output is a decision record another reviewer can reproduce.

**Before this:** nothing, though it lands hardest after you have a number you
want to believe. Every other chapter in this section produces one.

## 1. Name the unit being evaluated

A model checkpoint, decoding configuration, prompt, tool set, retry policy, and
environment can all change the result. “Model A beat Model B” is meaningful
only if every other relevant variable is fixed or disclosed.

For a static task, the unit may be:

```text
checkpoint + prompt template + decoding parameters
```

For an agent task, it is larger:

```text
checkpoint + harness + tools + permissions + environment + budget
```

Store that unit as versioned configuration. Otherwise a score change cannot be
attributed.

## 2. Choose tasks that represent the decision

Static benchmarks score a fixed input and output. Agentic evaluations execute a
trajectory with state, tools, retries, and termination. The difference is not
simply difficulty; it is where behavior can diverge.

Use static tasks for bounded capabilities such as classification, math, or
code generation with deterministic tests. Use environments when the product
depends on choosing actions over time.

Every evaluation set needs:

- target population and exclusion criteria;
- task source and collection date;
- expected output or verifier;
- important slices;
- contamination policy;
- failure taxonomy.

A large public benchmark may be less decision-relevant than a smaller reviewed
set from the actual workflow.

## 3. Treat the harness as an independent variable

Tool descriptions, context selection, retries, timeout, stop rules, and
permission prompts can change agent success more than a small model upgrade.
Record them in the result.

For each episode, log:

```text
task and environment version
model and prompt version
tool calls and observations
token, time, and cost budget
termination reason
outcome score
policy and safety violations
```

Task success without policy adherence is not a complete result. A system that
finishes by violating the action boundary fails the product decision.

## 4. Prevent the evaluation set from entering training

Contamination can occur through pretraining data, fine-tuning examples,
retrieval corpora, prompt exemplars, or manual debugging on the test set.

Use layered checks:

- exact and normalized hashes;
- near-duplicate search;
- source and timestamp separation;
- private held-out tasks;
- a record of every test item inspected during development.

No detector proves absence of contamination. The objective is to reduce risk
and disclose what was checked.

## 5. Use judges only where their errors are measured

An LLM judge is useful when exact matching misses semantic quality, but it can
prefer longer answers, its own style, confident tone, or a response presented
first.

Calibrate a judge against reviewed human labels. Randomize answer order, hide
model identity, test rubric variants, and report agreement by slice. If a
deterministic verifier exists, prefer it for correctness and use the judge for
dimensions the verifier cannot observe.

Judge score is another model output. It is not ground truth.

## 6. Quantify uncertainty before comparing close scores

An observed success rate is an estimate from a finite sample. With a small
evaluation set, the same underlying system can produce visibly different
rates across repeated samples.

Change sample size and successes below. Watch the interval narrow with more
evidence, not with a more confident narrative.

<!-- interactive: EvaluationUncertainty -->

Report the estimate with an interval and the number of tasks. For paired
candidate-versus-baseline comparisons, preserve task pairing and inspect the
disagreements: tasks only the candidate wins, and tasks only the baseline wins.

Seeds matter when generation or environments are stochastic. Repeat enough to
estimate variance, and define the evidence threshold before seeing the result.

## 7. Convert failures into owned actions

Aggregate scores are release signals; failure records are engineering inputs.
Use a taxonomy that maps to an owner:

| Failure | Likely owner |
|---|---|
| wrong knowledge or reasoning | model, data, or retrieval |
| correct plan, malformed tool call | harness schema or model |
| correct action, stale observation | environment or tool |
| timeout after repeated work | loop policy or serving |
| successful outcome, forbidden action | permission policy |
| inconsistent result across seeds | sampling or environment variance |

Store representative traces with the classification. A pie chart without
examples cannot guide a fix.

## 8. Make the release decision explicit

A candidate ships only if:

1. the primary outcome clears its predeclared evidence bar;
2. every hard guardrail remains within limit;
3. important slices do not hide a material regression;
4. latency and cost fit the service budget;
5. failures have an owner and acceptable residual risk.

If the result is mixed, state which additional evidence would change the
decision. “Run more tests” is not sufficient; name the slice, sample size, or
failure mechanism.

## Run the vertical slice

[Mission 01, evaluation](../../missions/01-language-model-agent/07-eval/)
collects stage-level model and harness evidence. It should compare the base,
SFT, RL, served, and agent-wrapped artifacts without attributing a harness
change to model weights.

The published record can establish behavior on its declared tasks. It cannot
claim broad capability or production impact beyond that task population.

## Check your mental model

**1. What is the actual evaluation unit for an agent?**

<details>
<summary>Answer</summary>

Not just `checkpoint + prompt template + decoding parameters` — that's the
static-task unit. An agent's unit is larger because more of it can change the
trajectory: `checkpoint + harness + tools + permissions + environment +
budget`. Two runs that share a checkpoint but differ in retry policy or tool
set aren't comparing the same system, even though "the model" is identical —
which is exactly why Section 3 insists the harness gets logged as its own
variable, not folded silently into "the model's score."

</details>

**2. Why can a higher score be unattributable?**

<details>
<summary>Answer</summary>

Because tool descriptions, context selection, retries, timeout, stop rules,
and permission prompts can move agent success more than a small model
upgrade — so if a new score comes from a run where the harness also changed,
there's no way to say how much of the gain is the model versus the harness
around it. The fix isn't a better statistic, it's discipline: log the
per-episode harness configuration alongside the outcome, so a reviewer can
at least check whether the harness moved before crediting the model.

</details>

**3. Which contamination paths exist after pretraining?**

<details>
<summary>Answer</summary>

Pretraining data is only the first path the chapter names — after that,
contamination can still enter through fine-tuning examples, a retrieval
corpus, prompt exemplars shown to the model at inference time, or simply a
developer manually debugging on what's supposed to be the held-out test set.
That last one is easy to miss because it isn't a data-pipeline bug at all —
it's a person, mid-development, looking at the answer to a question the
evaluation set is supposed to ask blind. It's why the chapter's layered
checks include "a record of every test item inspected during development,"
not just hash-based dataset scanning.

</details>

**4. When is an LLM judge appropriate?**

<details>
<summary>Answer</summary>

Only where a deterministic verifier can't observe the dimension you care
about, and only after the judge itself has been calibrated against reviewed
human labels — order randomized, model identity hidden, rubric variants
tested, agreement reported by slice. A judge that hasn't been checked this
way carries its own biases (preferring longer answers, its own style,
confident tone, whichever answer came first) straight into your result. The
chapter's framing is blunt about what a judge actually is: "Judge score is
another model output. It is not ground truth" — so it's a tool for the
things a verifier structurally cannot see, not a default replacement for one.

</details>

**5. What evidence is missing from a score without an interval or failure slices?**

<details>
<summary>Answer</summary>

Without an interval, you can't tell whether an observed difference between
two systems is real or just the sampling noise of a finite evaluation set —
the same system can produce visibly different success rates across repeated
samples of the same size, so a bare point estimate can't support a ship
decision on its own. Without failure slices and owners, even a passing
aggregate score hides *which* failures happened and who is responsible for
fixing them — "an aggregate score is a release signal; failure records are
engineering inputs," and a pie chart without representative traces "cannot
guide a fix." Both gaps point at the same problem: a number by itself can't
tell you whether it's safe to trust, or what to do next if it's borderline.

</details>

## Next

Evaluation closes one build loop and starts the next. Continue to
[agent systems](../../capabilities/act-coordinate/) to see how the harness
changes the unit under test, or return to the subsystem that owns the dominant
failure.

Primary references, in the order each widened what "evaluation" had to cover:
EleutherAI's lm-evaluation-harness (2021) standardizes static-benchmark
scoring across checkpoints, which is the simpler half of Section 2's
static-versus-agentic split; Jimenez et al., "SWE-bench" (2023) moves the
unit of evaluation from a single output to a multi-step trajectory against
a real repository, forcing the harness-as-independent-variable point Section
3 makes; the UK AI Safety Institute's Inspect framework (2024) generalizes
that trajectory-eval pattern into a reusable tool rather than a
benchmark-specific harness; and Debenedetti et al., "AgentDojo" (2024) adds
adversarial tool-use and prompt-injection scenarios, which is where the
policy-adherence failure row in Section 7's table comes from. Three years
separate the first tool from the last, tracking the same shift the rest of
this chapter argues for: from scoring an output to scoring a trajectory.
Also relevant: standard binomial and paired-test methods, which are older
than any tool named here and unchanged by this history.

[The evaluation landscape](LANDSCAPE.md) sets those harnesses side by side —
what each one fixes for you, and what it therefore stops you from disclosing.
