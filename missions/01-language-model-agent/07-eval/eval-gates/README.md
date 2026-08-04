---
status: draft
level: applied
base: none
label: Evaluation gates
---

# How does a release get blocked before a person has to eyeball it?

**Question:** [who decides to ship](../who-decides-to-ship/) says every guardrail
must become `definition -> measurement -> enforcement point`. A release gate
is where that chain has to close for the single highest-stakes decision this
layer makes: does this candidate ship. What does it take for that decision to
be a computation instead of a meeting?

**Before this:** [who decides to ship](../who-decides-to-ship/), for why "do not harm
quality" fails as a guardrail and what an executable one needs instead — a
population, a metric, a direction, a tolerance, and a decision. This chapter
takes exactly one guardrail of that shape — a capability-eval threshold — and
runs it.

You will finish able to compute a gate decision by hand, see why any single
threshold trades one error type for the other, and read a real sweep that
shows a hidden second rule quietly setting the floor of the first.

## The problem a threshold is trying to solve

A single reviewer reading a model's eval transcripts does not scale: they get
tired, they disagree with the next reviewer, and their judgment leaves no
record another team can recompute. An eval gate replaces that judgment with a
declared rule computed the same way every time — but a rule is only as good
as its threshold, and every threshold sits somewhere on a tradeoff between
two failure directions: blocking a release that was actually fine (a false
block), and passing one that was not (a false pass). No threshold removes
both errors at once; picking one is a policy decision that a gate mechanism
executes, not one it can make for you.

## The mechanism: two rules, computed the same way every time

[`core/eval_gate.py`](core/eval_gate.py) generates synthetic candidates —
each with a hidden `true_risk` in [0, 1] and four noisy observed category
scores (`cbrn_uplift`, `cyber_uplift`, `persuasion`, `autonomous_replication`,
illustrative labels only, not a claim about a complete taxonomy) — then gates
each one against a declared rule:

```text
block if:
  any category score exceeds a declared per-category ceiling
  OR
  the aggregate (mean across categories) rises more than a declared
  delta over the previous release's baseline aggregate
otherwise: pass
```

Run it on one candidate that should block:

```
candidate: candidate-0000  true_risk=0.844 true_unsafe=True
scores: {'cbrn_uplift': 0.849, 'cyber_uplift': 0.761, 'persuasion': 0.839, 'autonomous_replication': 0.94}
decision: BLOCK
  reason: cbrn_uplift=0.849 exceeds ceiling 0.700
  reason: cyber_uplift=0.761 exceeds ceiling 0.700
  reason: persuasion=0.839 exceeds ceiling 0.700
  reason: autonomous_replication=0.940 exceeds ceiling 0.700
  reason: aggregate 0.847 rose 0.497 over baseline 0.350, exceeds allowed delta 0.150
```

and one that should pass:

```
candidate: candidate-0042  true_risk=0.467 true_unsafe=False
scores: {'cbrn_uplift': 0.526, 'cyber_uplift': 0.315, 'persuasion': 0.487, 'autonomous_replication': 0.419}
decision: PASS
  reason: no category exceeded its ceiling, aggregate delta within bound
```

The mechanism itself is nothing more than the arithmetic above, computed
identically for every candidate — the entire value of a gate over a
discussion is that two people running this script get the same answer.

## Manipulate the one threshold that decides everything

Drag the aggregate-delta threshold below and watch both error rates move —
in opposite directions, never both toward zero:

<!-- interactive: EvalGateTradeoff -->

## The observed consequence: a hidden floor, not a bug

Sweeping only the aggregate-delta threshold (category ceiling held disabled)
over 2,000 synthetic candidates, 635 of them labeled unsafe by construction,
produces a real crossover:

```
delta_ceiling  false_block_rate   false_pass_rate
         0.05             0.423             0.000
         0.15             0.275             0.000
         0.25             0.141             0.000
         0.35             0.026             0.044
         0.40             0.003             0.140
         0.50             0.000             0.488
         0.65             0.000             1.000
```

Tightening the threshold drives false blocks toward 0.42 and false passes to
zero; loosening it does the reverse. Now sweep the *other* rule — the
per-category ceiling — while holding the aggregate-delta rule fixed at 0.15,
the value used in the demo candidates above:

```
 ceiling  false_block_rate   false_pass_rate
    0.40             0.548             0.000
    0.60             0.287             0.000
    0.70             0.275             0.000
    0.90             0.275             0.000
    1.15             0.275             0.000
```

Past ceiling 0.65 this sweep goes flat at exactly 0.275 — the same number
Result 3 hits at delta_ceiling=0.15. The category rule has stopped mattering;
the aggregate rule is doing all the work, and sweeping the category ceiling
in isolation would make it look like the gate hit some floor intrinsic to
that rule, when the floor actually comes from the *other* one. A gate built
from more than one rule cannot be read by varying a single threshold and
treating the rest of the system as absent — full numbers and both isolated
sweeps: [`runs/2026-08-01-eval-gate-sweep.md`](runs/2026-08-01-eval-gate-sweep.md).

## A brief history

Two frontier labs published the first versions of this exact mechanism
within three months of each other. Anthropic published its Responsible
Scaling Policy on September 19, 2023, defining AI Safety Levels (ASL) with
capability thresholds that gate further development and deployment once
crossed. OpenAI published its Preparedness Framework (Beta) on December 18,
2023, scoring models "low," "medium," "high," or "critical" across named risk
categories (including cybersecurity, CBRN, persuasion, and model autonomy —
the categories this chapter's toy borrows labels from) and declaring that
only models scoring "medium" or below may be deployed without further
mitigation. Both frameworks were preceded by the Frontier Model Forum,
founded July 26, 2023 by Anthropic, Google DeepMind, Microsoft, and OpenAI
specifically to develop shared safety-evaluation practice across labs. All
three are policy commitments about *how* a threshold-based decision gets
made; none of them are the specific numbers this toy script computes, which
are entirely synthetic.

## What this does not establish

- **Nothing about real model safety.** Every candidate score here is
  synthetic, generated by `generate_synthetic_candidates` with a fixed seed.
  No real model, real eval suite, or real capability was measured.
- **Nothing about where a real gate's threshold should sit.** The 0.35-0.40
  crossover in the sweep above is a direct consequence of this script's own
  synthetic-data construction (a declared baseline of 0.35 and a declared
  true-unsafe cutoff of 0.70), not a recommendation for any real policy.
- **Nothing about which categories, or how many, a real framework needs.**
  The four category names are illustrative, not a claim of a complete or
  correct taxonomy — real frameworks name and revise their own categories as
  new capabilities emerge.
- **Nothing about enforcement, escalation, or audit** — the other four links
  in [the release chain](../who-decides-to-ship/) (`measurement -> enforcement point ->
  audit record -> escalation owner`) are outside this chapter's scope; this
  chapter is only the `definition -> measurement` half, computed as a
  pass/fail decision.

## Check your mental model

**1. Why can't a single threshold minimize both false blocks and false passes at once?**

<details>
<summary>Answer</summary>

Because they move in opposite directions along the same axis. Lowering the
allowed delta makes the gate stricter — it blocks more candidates overall, so
it blocks more truly safe ones near the boundary too (false blocks rise) while
catching almost every truly unsafe one (false passes fall toward zero).
Raising the allowed delta does the reverse: fewer safe candidates get caught
(false blocks fall) but more truly unsafe ones slip through the looser rule
(false passes rise). The sweep in this chapter shows this directly —
false_block_rate falls from 0.423 to 0.000 as the threshold rises from 0.05
to 0.65, while false_pass_rate rises from 0.000 to 1.000 over the exact same
range. There is no single setting where both numbers are small; every point
on that curve is a tradeoff, not a solution.

</details>

**2. In the sweep, why does the category-ceiling rule go flat past ceiling 0.65 instead of continuing to fall?**

<details>
<summary>Answer</summary>

Because the aggregate-delta rule (held fixed at 0.15 during that sweep) is
still active and still blocking the same 27.5% of safe candidates regardless
of what the category ceiling is set to. Once the category ceiling is loose
enough that it never fires on its own, every remaining block in that sweep
comes from the other rule — raising the category ceiling further can't
change anything, because it was never the rule doing the blocking past that
point. This is exactly why isolating one rule at a time (as the interactive
widget and Result 3 do, with the category ceiling disabled) is necessary to
see either rule's own tradeoff curve cleanly.

</details>

**3. Two people re-run this exact script with the same seed and get different pass/block decisions on the same candidate. What does that tell you?**

<details>
<summary>Answer</summary>

That they used different declared thresholds (a different category ceiling
or aggregate-delta value), not that the mechanism is unreliable. The whole
point of an executable gate is that the same candidate, the same thresholds,
and the same scores always produce the same decision — `evaluate_gate` is a
pure function of its three arguments. A different outcome means a different
input somewhere, and the gate's job is to make that difference visible
(which threshold, which score) rather than hide it behind "the reviewers
disagreed."

</details>

**4. Real frameworks name specific risk categories (CBRN, cyber, persuasion, autonomy) rather than one aggregate danger score. What does this chapter's sweep suggest is lost if you only look at the aggregate?**

<details>
<summary>Answer</summary>

The two-rule result shows the aggregate-delta rule alone catches every
synthetic unsafe candidate at delta_ceiling=0.15 (false_pass_rate=0.000) even
with the category ceiling fully disabled — meaning the per-category ceiling
in this toy is redundant with the aggregate rule for this synthetic
population. But that's an artifact of how the synthetic data correlates all
four categories with one underlying `true_risk`; a real model could plausibly
score dangerously high in exactly one category (say, cyber capability) while
scoring low everywhere else, keeping the aggregate low enough to pass. A
per-category ceiling is what catches that case; an aggregate-only rule
would not. This chapter's toy doesn't generate that scenario, so it can't
demonstrate the gap directly — it can only tell you the gap is there in
principle once categories aren't perfectly correlated.

</details>

## Next

The framework's remaining links — `measurement -> enforcement point`, then
`audit record -> escalation owner` — are where a gate decision like this one
actually stops a deployment pipeline and gets recorded, rather than staying a
number a script prints. [Who decides to ship](../who-decides-to-ship/) names both;
neither has a from-scratch `core/` chapter here yet.

Primary references: Anthropic, *Responsible Scaling Policy* (September 19,
2023); OpenAI, *Preparedness Framework (Beta)* (December 18, 2023); Frontier
Model Forum, founding announcement (July 26, 2023).
