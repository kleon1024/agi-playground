---
status: draft
level: frontier
base: none
label: Capstone B — the science loop
---

# A hypothesis in, a validated finding out. What does the science loop need?

**Question:** the software capstone lands a change in production. Science
has no production — it has *nature*, and the loop is different in kind:
a hypothesis is not verified by a test suite but by measurement, and the
measurement is expensive, noisy, and irreproducible unless the loop is
designed for that. This capstone maps the science loop — research
objective to validated finding — and names which parts a computational
tutorial can run, which parts require a laboratory, and what the
evaluator has to be to avoid Goodhart on the most dangerous metric there
is: a proxy for truth.

**The artifact this chapter follows** is the science loop itself, drawn as
its handoffs, anchored to this repository's own computational-science
stage — [molecular property prediction](../../08-bio-pharma-modeling/),
where a small model predicts whether a compound is toxic and a dataset
decides whether the model is believed.

**Before this:** the delivery-stack objects and Capstone A. Science is the
second domain where the same seven objects compose, with a different
evaluator.

## Why the loop is not the software loop

Software delivery ends when production agrees. Science ends when
*measurement* agrees — and measurement has properties tests do not:

| Software test | Scientific measurement |
|---|---|
| fast and cheap | slow and expensive (a replicate costs real instrument time) |
| deterministic | noisy — the same experiment twice is not the same number |
| covers the code's inputs | covers one point in an enormous space |
| no concept of calibration | calibration is the precondition of believing any number |
| negative results are failures | negative results are data |

The last row is the one that breaks naive automation. In software, a
failing test is a defect to fix. In science, a negative result is a
*posterior update* — information the next experiment consumes. A loop that
treats negatives as failures is a loop that cannot learn.

## The loop, with its handoffs

```text
research objective  -> a question with a defined scoring metric (ObjectiveSpec)
  | 1 provenance    -> literature and prior data, dated and cited (EvidenceRecord)
  | 2 hypothesis portfolio -> several hypotheses, not one (WorkGraph)
  | 3 computational screening -> cheap models rank the candidates (harness)
  | 4 experiment design -> controls, replicates, randomization (domain model)
  | 5 execution      -> simulation or instrument (side-effect semantics: a run is a side effect)
  | 6 measurement    -> numbers with uncertainty, not without (EvidenceRecord)
  | 7 replication    -> an independent repeat before belief (trust boundary)
  | 8 posterior update -> beliefs revised by the data, including negatives
  v
next experiment     -> the loop restarts with a narrower question
```

The load-bearing handoffs are 6 and 7. Measurement without uncertainty is
a number pretending to be a fact; replication is the only evaluation that
does not depend on the proposer. The rest of the chain is the delivery
stack's machinery applied to a different evaluator.

## What the industry loop adds that a computational tutorial cannot

The physical side of the loop is a system of record in its own right, and
it is where AI-for-science platforms (Lila's AI Science Factory, Periodic
Labs, Recursion's drug-discovery loop) spend most of their engineering:

- electronic lab notebooks and LIMS — the experiment's RunLedger;
- sample and material lineage — the domain model's dependency graph;
- instrument scheduling — the WorkGraph's executor registry;
- calibration — the precondition of believing measurement;
- replicates and negative-result capture — the EvidenceRecord's honesty
  contract, made physical;
- experiment data flowing back automatically — the bounded-improvement
  loop with nature as the evaluator.

None of these is a LangGraph node. They are the same seven objects,
installed in a laboratory instead of a repository. The tutorial's honest
position: a 24GB card can run computational screening
([the molecular-property stage](../../08-bio-pharma-modeling/) is exactly
that), and it cannot run the physical loop, which is why the capstone
names the boundary instead of blurring it.

## The evaluator that avoids Goodhart

Science's Goodhart is sharper than software's, because the proxy is a
proxy for *truth*. The mitigation is a metric set, not a single score:

| Metric | It answers |
|---|---|
| Information gain per experiment | did this run narrow the space? |
| Reproducibility | does the finding survive an independent repeat? |
| Calibration | does the stated uncertainty match the observed error? |
| Physical validity | is the result consistent with what the domain already knows? |
| Negative-result capture | did the loop record what did not work? |
| Cost per validated finding | the economics object, applied to science |

The first and fifth rows are the ones software never needs: a loop that
scores only "papers that look like papers" is optimizing a proxy, which
is the exact failure this topic's [origin story](../../README.md) names —
a metric improved while the result did not move.

## What this does not say

It does not claim a science finding has been produced here — the
molecular stage is a modeling tutorial, not a discovery. It does not
claim the physical loop is implementable on the local lane — it is not,
and the chapter says so. And it does not claim the metric set is
sufficient for all science; it claims it is the set that keeps the loop
honest, which is the same role the [evidence contract](../../verification-and-evals/)
plays for the software half.

**Next:** the six objects and two capstones are mapped. The remaining
agenda is the same audit applied to the other topics — the
[language-model](../../01-language-model/) and
[discovery](../../02-personalized-discovery/) spines still carry
survey-mode chapters that need the tutorial treatment.
