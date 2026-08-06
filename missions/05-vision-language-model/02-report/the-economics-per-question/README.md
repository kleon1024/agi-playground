---
status: verified
level: applied
base: scratch
label: The economics per question
verified: 2026-08-06
---

# The \$0.00128/question that decides build-vs-buy

**Question:** [stage 02's report](../) returned NOT MET. This chapter reads
the recorded economics and asks what the per-question price does to the
verdict.

**Before this:** [stage 02's report](../) and its recorded hosted-API run.

## The economics, read

The run ([record](runs/2026-08-06-econ-read.md)) reads the recorded numbers:

| number | value |
|---|---|
| hosted API cost | \$1.0033 total, \$0.00128/question |
| hosted API accuracy | 0.8329 (653/784) |
| vision + text-only training | \$0 marginal, ~20 min CPU |

## Two readings

**The per-question price is the build-vs-buy floor.** Any nonzero
per-question cost already exceeds the \$0 training cost — there is no
volume of API questions that reaches the vision pathway's cost, because
its training is free. The entire tradeoff is on the accuracy axis, where
the hosted API leads decisively (0.8329 vs 0.4375). The economics make the
NOT MET verdict a clean one, not a budget judgment call.

**The cost axis is one-directional, so the accuracy axis is the whole
story.** Because the API's marginal cost is tiny and the self-trained
pathway's fixed cost is zero, the comparison reduces to accuracy alone —
and there the API wins by a wide margin. The recorded pair (\$0.00128 vs
\$0) is what turns the verdict from "depends on your budget" into "buy,
not build."

## Evidence boundary

The recorded hosted-API run (784 questions, cost from OpenRouter's
usage.cost, not estimated). It reads that artifact; it does not re-call the
API and the economics are for this one model and eval set.

## Check your mental model

Answer each before opening it.

**1. Why does the \$0 training cost make the API's price the floor?**

<details>
<summary>Answer</summary>

Because the comparison is per-question. The vision pathway costs \$0 once
to train and then \$0 per question; the API costs \$0.00128 per question,
forever. Any nonzero per-question price means the API can never be beaten
on cost — so the build-vs-buy decision rests entirely on whether the
self-trained pathway beats the API's accuracy, which it does not.

</details>

**2. What would make the cost axis two-directional?**

<details>
<summary>Answer</summary>

If the self-trained pathway had a nonzero per-question serving cost, or if
the API were priced high enough to matter. Neither holds here: the pathway
serves locally at \$0 and the API is \$0.00128. With only one direction on
cost, the verdict collapses to the accuracy comparison — which is why the
report reads NOT MET rather than "depends on your budget."

</details>

## Next

Back to [stage 02's report](../), or to
[where the NOT MET verdict hides the pathway's signal](../when-the-category-breaks-down/)
which reads the same report's category structure.
