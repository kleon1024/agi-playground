---
status: verified
level: applied
base: scratch
label: When the training plateaus
verified: 2026-08-08
---

# The crawl is the plateau: three ways a run can stall

**Question:** [the optimization chapter](../) races SGD, momentum, and
Adam on a bowl whose minimum is reachable. A production run instead
flattens far above the floor — the loss curve looks done, the run is
not. This chapter executes the plateau audit: which failure class does
the stall belong to?

**Before this:** [the optimization chapter](../) and its recorded
optimizer comparison, where the same three update rules converge on an
ill-conditioned bowl.

## The plateau, executed

The run ([record](runs/2026-08-08-plateau.md)) races four update rules
on the flat-minimum surface L(x, y) = x²y² under a fixed 1,000-step
budget, then repeats the race with an irreducible +0.01 term:

| optimizer | loss at 500 | final loss | verdict |
|---|---:|---:|---|
| SGD | 2.43e-5 | 6.16e-6 | crawling above the floor |
| momentum, mu=0.9 | 2.02e-7 | 5.51e-8 | converged |
| momentum, mu=0.99 | 1.30e-3 | 7.52e-12 | converged |
| Adam | 6.29e-7 | 7.36e-8 | converged |

On the floored surface the same four rows all end at 0.0100 — the same
number to four digits, no matter which update rule runs.

## The failure mode, named

**Flat-direction stall, measured.** On x²y² the minimum at the origin is
genuinely flat: the gradient is (2xy², 2x²y), so near the minimum the
per-coordinate step shrinks as the loss shrinks. Plain SGD's relative
progress collapses with it — in its final 100 steps it moves 18.9
percent of the remaining loss and ends 6x above the tolerance, with
each halving of what remains costing about 331 steps and the cost still
growing. The curve looks converged; the run is not. That crawl is the
plateau, and it is an optimizer failure: momentum and Adam both
converge inside the same budget.

**The saddle is the high-dimensional version.** The measured flat
minimum is the limit case of a saddle point: a direction of near-zero
curvature that an update rule has to escape, slowly, because the
gradient there is tiny. Dauphin et al. (2014, arXiv:1406.2572) argue
high-dimensional non-convex surfaces are dominated by saddles, and
escaping them is the hard part, not the local minima. The toy isolates
the mechanism the saddle shares: small gradients a fixed step size
cannot convert into progress.

**Surface floor, measured, and it is not an optimizer failure.** Add an
irreducible +0.01 to the same surface and every optimizer stalls at
0.0100 — all four rules land on the same number. The diagnostic falls
out of the run: when every update rule and every learning rate stalls at
the same loss, the floor is in the data or the model capacity, not in
the optimization loop. That is the first question to ask of a stalled
run, because the answer changes who fixes it: the optimizer owner for
the first class, the data or capacity owner for the third.

## The fix and its trade

The fix for the flat-direction class is to change the update rule, and
the run measures both ways it works. **Momentum** accumulates the small
gradients into a velocity that carries the iterate through the flat
region (Sutskever et al., 2013, ICML); the knob is mu, and its trade is
measured — mu=0.99 escapes fastest but is still ringing at step 500
(1.30e-3) and settles later, while mu=0.9 is gentler. **Adam** replaces
the raw gradient with a normalized step, so progress through the flat
region is roughly linear in budget (Kingma & Ba, 2015, ICLR); its trade
is an extra hyperparameter pair and per-parameter statistics. Neither
fixes the surface floor — there the fix is more data, better labels, or
a bigger model, and the diagnostic is that the stall did not move when
the optimizer changed.

Two named fixes sit outside this run's surface. **Warm restarts**
(Loshchilov & Hutter, 2017, ICLR) re-anneal the learning rate to escape
an attractor — the local-minimum class of stall, different from the
flat one here. **Warmup** addresses the early-run instability the
vision track measured
([the warmup-stability chapter](../../../01-language-model/vision/06-warmup-stability/)),
not the mid-run flattening here.

## Who owns the loop

Each stall class has one owner, and the diagnostic is what assigns the
class:

- **The optimizer and algorithm team** owns the update rule and the mu
  knob — the flat-direction class. It owns the crawl: plain SGD ending 6x
  above the tolerance inside the 1,000-step budget while momentum and
  Adam converge, with the escape-versus-ringing trade measured at mu=0.99
  against mu=0.9.
- **The training-infra team** owns the budget and the schedule — the
  step cap is the contract a run is measured against, and warmup and warm
  restarts are the schedule-level fixes for the early-instability and
  attractor classes it has to hand the optimizer team a verdict on.
- **The research and evaluation team, or the data and capacity owner,
  owns the surface floor** — the class where every update rule stalls at
  the same loss. The +0.01 run makes all four rules land on 0.0100, and
  who fixes it changes by class: no learning rate moves a data or
  capacity floor, so the diagnosis has to name the owner before anyone
  retunes.

When ownership is implicit, the optimizer owner retunes a learning rate
that cannot move a surface floor, and the data owner washes data that
cannot fix a flat-direction crawl — the same misdiagnosis from opposite
sides.

## Evidence boundary

The executed audit uses one flat-minimum surface with a fixed budget and
tolerance, four update rules with a shared learning rate, and an
irreducible-term variant. It demonstrates the flat-direction stall, the
momentum knob's escape-versus-ringing trade, and the surface-floor
diagnostic on this surface. It does not extend to real transformer loss
surfaces, where a stall can be any mix of the three classes at once and
the saddle escape is the high-dimensional version the toy's limit case
stands in for — those claims rest on the cited papers, not this run.

## Check your mental model

Answer each before opening it.

**1. The loss curve flattens. Why is that not convergence?**

<details>
<summary>Answer</summary>

Because a flattening curve and a converged run are different claims.
Plain SGD's loss is still falling — 18.9 percent in its final 100 steps
— but the rate is collapsing: about 0.2 percent per step, each halving
of what remains costing about 331 steps and growing. The curve looks
done while the run ends 6x above the tolerance. A plateau is a rate
that has collapsed, not a loss that has stopped.

</details>

**2. How do you tell a flat-direction stall from a surface floor with
one experiment?**

<details>
<summary>Answer</summary>

Change the update rule and keep everything else fixed — the measured
run is exactly that experiment. On the flat surface, momentum and Adam
converge where plain SGD crawls, so the stall is in the optimizer. On
the floored surface all four rules land on 0.0100, so the stall is in
the surface, and the owner of the fix changes: data or capacity, not
optimization.

</details>

**3. Why is mu=0.99 not strictly better than mu=0.9 on this surface?**

<details>
<summary>Answer</summary>

Because momentum trades escape speed against settling time. mu=0.99
carries more velocity into the flat region, so it crosses it faster,
but it also arrives ringing — at step 500 its loss is 1.30e-3, orders
of magnitude above the others — and settles later. mu=0.9 escapes more
slowly and lands more gently. Both converge within the budget; the
trade only shows up when the budget is tight enough to force a choice.

</details>

## Next

Back to [the optimization chapter](../), which is the prerequisite this
plateau diagnosis sits on, or to
[fewer flips, fewer steps](../the-flips-that-separate-optimizers/) to
see the companion failure the bowl's ill-conditioning produces.
Pretraining asks the surface-floor question at scale:
[what are you actually training?](../../../01-language-model/02-pretrain/).
