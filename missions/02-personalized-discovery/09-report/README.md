---
status: verified
level: applied
verified: 2026-07-27
base: none
label: Outcome report
---

# Did the mission earn the right to claim anything?

**Question:** the funnel produces slates. Is the mission accomplished? No claim is checkable until it is judged against the contract written before the system existed. This stage turns that contract into a report that can say met, not met, or cannot determine.

**Before this:** [stage 08's latency budget](../08-serving/) is one input
this report demands alongside quality and guardrails — the funnel above it
in the mission's stage table supplies the rest.

**Related:** the variance and disclosure discipline this stage enforces is
[evaluation and observability](../../../platform/evaluation-observability/),
the same discipline mission 01's [stage 07](../../01-language-model-agent/07-eval/)
and mission 03's [stage 05](../../03-quantitative-research/05-report/) apply
to a language model and a trading signal respectively.

The artifact is a run-artifact JSON document plus a verdict. It contains seed-level nDCG@10 for the candidate and both declared baselines, guardrails, p50/p95 latency, cost, and failure cases. Its shape is documented in `core/report.py`. The report reads `mission.yaml`; it does not decide after seeing results which baseline, metric, or threshold would have been easier to pass.

## Why the baselines and guardrails are non-negotiable

The mission contract requires every acceptance condition to hold: beat the declared baseline by more than measured run-to-run variance, run end to end, preserve guardrails, stay inside latency and cost budgets, catalogue failures, and trace evidence to runs. Beating popularity establishes that the system does more than show the same head items to everyone. Beating the stronger item-item collaborative-filtering baseline is what could justify the added complexity. Beating only the weak baseline is not a result worth the system's cost.

Treat guardrails as vetoes, not extra points — a higher nDCG with degraded cold-start performance is still a loss. Bury a guardrail breach beneath a headline win in a report and you invite the wrong reading, so the evaluator returns `NOT MET` whenever a required guardrail fails, no matter how the headline number looks. Run the synthetic breached fixture and you see exactly that: the headline candidate nDCG@10 mean is 0.4102 versus 0.3012 for popularity and 0.3552 for item-item CF, but the cold-start guardrail is 0.271 versus 0.298 and the verdict is still `NOT MET`.

<!-- interactive: GuardrailPanel -->

Failure cases are also required evidence. A report with none has either not looked or is not telling you. The fixtures include a cold-start boundary group and rare lexical-query starvation; they are illustrative only, not mission results. Offline replay is not online outcome. Logged interactions were produced by a previous policy, cannot reveal items never exposed, and cannot establish retention or satisfaction in real users. Every number this mission can eventually report is bounded by that fact.

## The honest default is refusal

Run the evaluator with no artifact. It scans actual `runs/` directories and returns `CANNOT DETERMINE`, naming the missing seed-level primary metric, guardrails, cost, and failure catalogue. That refusal is the core lesson. It follows `platform/data/01-ablation-harness`: a tool that always returns a winner has hidden uncertainty rather than resolved it. A serving-only latency run is not an end-to-end mission outcome.

```bash
uv run python core/report.py
uv run python core/report.py --fixture met
uv run python core/report.py --fixture breached
uv run python prod/experiment_report.py core/fixtures/met.json
```

The complete fixtures are explicitly synthetic and show the report format only.
The production path reads the same schema into pandas, applies Welch tests,
reports observed power as a diagnostic, and keeps every guardrail as a veto.
A warehouse-backed report job and a dedicated experimentation platform are
alternatives. None turns offline estimates into online business evidence, and
planning still needs a predeclared minimum detectable effect rather than power
calculated from the observed result.

This stage's executed runs verify the parser, contract drift guard, verdict logic, the missing-input refusal, and the two illustrative branches. They do not verify that mission 02 beat either baseline, met all guardrails, met cost, or has a real failure analysis. Until a real integrated run emits the required artifact, `CANNOT DETERMINE` is the only honest mission conclusion.

Generate the report from immutable run inputs — never transcribe it into a slide. Record command, code revision, dataset split, random seeds, environment, cost basis, and artifact checksums next to the metric arrays, so a later reader can tell whether a baseline was rerun fairly or copied from a different setup. This matters most for recommendation replay, where a change in logging cutoff or eligibility rule can dominate a model change while leaving a familiar metric label unchanged.

Treat the report as a release gate, not a retrospective decoration — a missing measurement should block a success claim just as a breached constraint does. Name ownership and next action for every missing field or failure slice, but never let that silently convert uncertainty into failure or success. That three-way distinction is why `CANNOT DETERMINE` is a first-class result rather than an exception.

Variance belongs in the decision, not only in an appendix. The contract requires at least five seeds because one lucky training or evaluation sample cannot establish a margin. The evaluator compares the candidate and each baseline using their sample spreads and rejects a positive mean gap that is not larger than its 95% uncertainty margin. This normal approximation is a readable teaching choice, not a substitute for selecting a test appropriate to a real experiment’s dependence structure.

The report should preserve comparisons over time without moving goalposts. If the catalogue, split, metric definition, or eligibility policy changes, label it as a new evaluation context and rerun both baselines. Do not append incomparable points to a trend line. The most valuable result can be a documented failure: it tells the next system exactly which baseline, guardrail, slice, or budget stopped complexity from becoming value.
