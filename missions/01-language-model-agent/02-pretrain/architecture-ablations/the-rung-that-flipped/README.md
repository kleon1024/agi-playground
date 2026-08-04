---
status: verified
level: applied
base: scratch
verified: 2026-07-28
label: The rung that flipped
---

# What happens when the budget definition decides the winner?

Nine training runs. Two headlines, both true, pointing opposite ways. This is
the feed-forward rung, and it is where
[the budget you hold equal](../README.md) stops being a caution in section 1
and starts rewriting the conclusion.

**Before this:** the parent chapter, through the ladder's results table. You
need the three budget definitions and the fact that a mixture-of-experts block
has two parameter counts — what it stores and what a token passes through.

## Three arms, one variable

Eight routed experts with top-2 routing plus one shared expert. Only the
per-expert width moves.

| Arm | Total parameters | Active per token | Mean val loss |
|---|---:|---:|---:|
| `dense` | 33,661,440 | 33,652,736 | 3.8608 |
| `moe-equal-active` | 67,314,176 | 33,685,504 | **3.7707** |
| `moe-equal-total` | 33,694,208 | 22,478,848 | 3.8607 |

Holding **active** parameters equal, MoE wins on every seed by 0.0901 nats.
Holding **total** parameters equal, the difference is 0.0001 and its sign flips
between seeds.

Read that second row carefully, because "MoE ties dense" is the wrong summary.
This ladder *cannot tell them apart* — and the MoE arm reached the same loss
through **33.2% fewer parameters per token**. A tie in loss at two thirds of the
per-token cost is not a tie.

Switch the definition below and watch one set of nine runs change its verdict.

<!-- interactive: EqualBudget -->

## The third definition has no winner at all

Both MoE arms ran at roughly half of dense throughput. `moe-equal-total`
performs *less* arithmetic per token and still took **1.85x as long**, which is
routing overhead measured rather than argued: gathers, a router, and extra
sequential dependencies that current kernels are not fast at.

That has a consequence nobody enjoys. In the 1,645.9 seconds
`moe-equal-active` needed, dense would have seen 391M tokens instead of 200M.
Under an equal-wall-clock budget the honest comparison is therefore against a
dense arm trained on nearly twice the data — **and that arm was not run.**

So the 0.0901 is not evidence about it. A budget you did not buy is a blank,
not a tie, and writing "MoE wins" without qualifying the budget would be
picking the definition that flattered the result.

## Why this rung refuses to pick

Every other rung on the ladder holds one budget fixed by construction. This one
cannot, because the question "how many parameters does a mixture-of-experts
block have" has two correct answers and they differ by a factor of two here.
`moe_arms()` therefore returns one arm matched on each, and the run record
declares which definition each result belongs to.

That is the general shape of the problem. Any architecture that decouples
stored capacity from per-token compute — conditional computation, weight
sharing across passes, early exit — will do this to a comparison. The
definition stops being bookkeeping and becomes the claim.

## Check your mental model

Answer each before opening it.

**1. Section 4's two MoE arms support opposite headlines from the same nine
runs. Which sentence is true of both, and which of each alone?**

<details>
<summary>Answer</summary>

True of both arms: mixture-of-experts reaches at least as good a loss as
dense while using fewer active parameters per token — `moe-equal-active` wins
outright at equal active parameters, and `moe-equal-total` ties dense's loss
while using 33.2% fewer active parameters per token, which is a real
efficiency win even without a loss improvement. True of `moe-equal-active`
alone: it wins by 0.0901 nats, but only under the equal-active-parameters
definition, at double the total stored parameters. True of `moe-equal-total`
alone: its loss is statistically indistinguishable from dense's (0.0001
difference, sign flips across seeds) — it does not win on loss under this
budget, it only wins on per-token efficiency.

</details>

**2. `moe-equal-total` matched dense's loss using 33.2% fewer active parameters
and still took 1.85x as long. Which budget does that make it better under,
and which worse?**

<details>
<summary>Answer</summary>

Better under an equal-total-parameters budget measured by per-token
compute-efficiency: same loss, less arithmetic per token, which is a genuine
win on that specific axis. Worse under an equal-wall-clock budget: despite
doing *less* arithmetic per token, it still took 1.85x as long as dense to
train, because routing, gathers, and extra sequential dependencies cost real
wall-clock time that current kernels aren't fast at — a cost that has nothing
to do with the architecture's FLOP efficiency and everything to do with
implementation overhead. The same model can be a clear win on one budget
definition and a clear loss on another, simultaneously, which is exactly the
chapter's point.

</details>

**3. What would you have to run before you could say anything at all under an
equal-wall-clock budget?**

<details>
<summary>Answer</summary>

A dense arm trained on the amount of data dense would have seen in the same
wall-clock time the MoE arm took — in this chapter's own numbers, dense would
have processed roughly 391M tokens in the 1,645.9 seconds `moe-equal-active`
took to process 200M. That dense-at-391M-tokens run was never executed, so
there is no result to compare against under an equal-wall-clock budget; the
0.0901-nat MoE win is not evidence about that comparison, because the arm
that would settle it doesn't exist. A budget you didn't buy a comparison run
for is a blank, not a tie.

</details>

**4. Name another architectural idea that would force the same
two-parameter-count problem, and say which budget would flatter it.**

<details>
<summary>Answer</summary>

Any architecture that decouples stored capacity from per-token compute forces
the same problem — the chapter names conditional computation, weight sharing
across passes, and early exit as examples (upcycling, covered elsewhere in
this same platform section, is another concrete instance: it changes total
stored parameters while, at initialization, changing active compute only
modestly). Equal-parameters budgets flatter these designs, since they get
credit for large stored capacity while a well-designed variant spends only a
fraction of it per forward pass; equal-FLOPs budgets do the opposite, letting
a plain dense control grow larger to match the conditional model's compute
and closing or reversing the apparent advantage. Whichever definition isn't
stated is the one likely being used to flatter the result.

</details>

## Evidence boundary and next step

Nine runs at 33M parameters on 200M tokens of FineWeb-Edu, scored by validation
cross-entropy on the same distribution. Nothing here establishes that the
equal-active result holds at a larger size, on another corpus, or on any
downstream task — Fedus et al. (2022) report scale-dependent mixture-of-experts
behavior, which is a reason to expect this rung's answer to move, not a reason
to assume which way.

Return to
[what earns the right to say any of this](../README.md#5-what-earns-the-right-to-say-any-of-this),
which is the seed-noise floor every number on this page is measured against.
