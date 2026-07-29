---
status: verified
level: applied
base: scratch
verified: 2026-07-28
label: Does it pay off
---

# Does the extra capacity earn back what it cost?

The surgery is free and exact: the upcycled model starts at its parent's loss
to the digit. That is where the parent chapter stops, and it is the easy half.
The hard question is whether 2.93x the storage and 1.64x the compute buy
anything once you keep training — and the run that answers it starts by getting
*worse*.

**Before this:** [upcycling a dense checkpoint](../README.md), through the cost
section. You need the surgery, the replication argument, and both parameter
counts.

## Both arms get worse before either gets better

Continuing to train the upcycled model made it worse first — and so did
continuing to train the dense parent. At `lr=1e-4` both rose from 3.0576 to a
peak near 3.1445 at 53M tokens, then fell steadily for the remaining 147M
without either one getting back to where it started.

This is not the surgery failing. The parent finished a cosine schedule at
nearly zero learning rate, sitting in a minimum. Raising the rate to 1e-4 kicks
it back out, and the model has to re-descend before it can make progress the old
one could not.

The effect is large enough to swamp everything else in the run, and it hits both
arms equally — which is precisely why the comparison is run **as a pair** rather
than as one arm against a remembered number. Against a remembered 3.0576, this
run reads as a catastrophe. Against its own control, it reads correctly.

## The difference, once the disruption cancels

| Tokens | dense continue | upcycled MoE | difference |
|---:|---:|---:|---:|
| 0 | 3.0576 | 3.0576 | 0.0000 |
| 32.8M | 3.1364 | 3.1362 | -0.0002 |
| 131.1M | 3.1145 | 3.1084 | -0.0061 |
| 200.0M | 3.0939 | **3.0851** | **-0.0088** |

The upcycled arm is *behind* for the first 32.8M tokens, crosses over, and then
pulls away monotonically for the remaining 167M with no sign of flattening.

That shape is what replication predicts. At step 0 the four experts are
identical, so the extra 170M parameters compute nothing the dense model did not
already compute. They begin to pay only once the experts have diverged into
different functions, and that takes tokens.

**An experiment stopped at 30M tokens would have reported the opposite result
with a straight face.** The crossover is not a detail of this run; it is a
property of the method, and it sets a floor on how short a continued-training
comparison can be and still mean anything.

## The budget reopens the question

Under an equal *wall-clock* budget the ranking is not settled. The MoE arm took
1.93x as long, so the dense arm would get 1.93x the data — and it was still
improving when the run ended. That arm was not run.

This is the same trap
[the architecture ladder](../../02-architecture-ablations/the-rung-that-flipped/)
found on its own feed-forward rung: an equal-token result and an equal-wall-clock
result are different claims, and only one of them was bought.

## What this establishes and what it does not

**Established**, at an equal token budget: the upcycled model ends 0.0088 nats
ahead of the dense continuation, with the gap monotone across 25 consecutive
evaluations. Full curve in
[`runs/2026-07-28-continue-training.md`](../runs/2026-07-28-continue-training.md).

**Not established:** that it is ahead under any other budget. **Not
established:** that 0.0088 survives replication — one seed per arm cannot bound
run-to-run variance, and what carries the result is the shape of the gap, not
the endpoint. **Still untested:** whether 4 experts at top-2 is a good shape. It
was chosen to make the identity check exact, not because it was tuned.

## Check your mental model

1. Both arms got worse for 53M tokens. What would you have concluded if only
   the upcycled arm had been run?
2. Why is the upcycled arm behind at 32.8M tokens and ahead at 200M?
3. What does that crossover imply about the shortest continued-training
   comparison worth running?
4. The gap is 0.0088 nats from one seed per arm. Which part of that result is
   load-bearing, and which part is not?

## Next

Return to [what this chapter hands back](../README.md#next). Then
[architecture ablations](../../02-architecture-ablations/) trains the same block
from scratch against a dense control, and reports the result this pair of runs
cannot.
