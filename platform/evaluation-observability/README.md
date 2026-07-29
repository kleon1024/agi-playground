---
status: draft
level: applied
label: Evaluation
---

# What evidence justifies replacing what you already run?

And when the candidate wins, which part of that evidence belongs to the model,
which to the harness, and which to the serving configuration?

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

1. What is the actual evaluation unit for an agent?
2. Why can a higher score be unattributable?
3. Which contamination paths exist after pretraining?
4. When is an LLM judge appropriate?
5. What evidence is missing from a score without an interval or failure slices?

## Next

Evaluation closes one build loop and starts the next. Continue to
[agent systems](../../capabilities/act-coordinate/) to see how the harness
changes the unit under test, or return to the subsystem that owns the dominant
failure.

Primary references: lm-evaluation-harness, Inspect, SWE-bench methodology,
AgentDojo, policy-adherence environments, and standard binomial and paired-test
methods.

[The evaluation landscape](LANDSCAPE.md) sets those harnesses side by side —
what each one fixes for you, and what it therefore stops you from disclosing.
