---
status: verified
level: applied
verified: 2026-08-01
base: scratch
label: Metric gaming
---

# The score went up. Did the thing you actually wanted?

An automated grader, a benchmark pass rate, a reward model score: all three
are proxies, standing in for a quality you cannot cheaply measure directly.
[The evaluation stage](../README.md) already asks you to quantify uncertainty and
convert failures into owned actions before trusting a score. This chapter
asks a different question about that same score: what happens to its meaning
once something is optimizing against it on purpose?

**Before this:** [what evidence justifies replacing what you already
run](../README.md) — you need a proxy metric in hand before it is worth
asking whether the metric still means what it did when you chose it.

## 1. The problem: a proxy is not the thing itself

A reward model score for "helpfulness" is not helpfulness. A pass rate on a
fixed benchmark is not general capability. A proxy metric is built to
*correlate* with a true objective you cannot cheaply score at scale — and
correlation is exactly the property that breaks under optimization pressure,
because an optimizer does not care why a metric moves, only that it moves.

This is not a data-quality problem or a measurement-noise problem. It is a
structural one: any proxy that is imperfectly aligned with the true objective
has directions in which it can be increased without the true objective
increasing too — and the harder something searches, the more likely it finds
exactly those directions.

## 2. The mental model: a proxy is a narrow slice, not a mirror

Picture the true objective as a surface and the proxy as a second surface
that agrees with it almost everywhere nearby your starting point, then peels
away in a few directions the true objective doesn't reward. Weak or
undirected search stays near the starting point and never notices the
peeling-away regions. Strong, directed optimization is a search *for* the
direction that improves the visible score fastest — and if that direction is
one of the peeled-away ones, the optimizer finds it before it finds genuine
improvement, simply because genuine improvement usually has a shrinking
marginal return and the peeled-away direction usually does not.

## 3. The mechanism, built from two functions

The toy in `core/goodhart.py` makes this concrete with two knobs. `i`
(informativeness) is genuinely useful but has diminishing returns and a hard
cap at 50. `p` (padding) is cheap to add indefinitely.

```
true_objective(i, p) = 10*sqrt(i) - 0.6*p   # padding is a real cost
proxy_metric(i, p)   = 10*sqrt(i) + 0.4*p   # padding looks like a reward
```

Both functions share the exact same genuine-quality term, `10*sqrt(i)` — the
proxy is not garbage, it really does track true quality through that term.
The only difference is how each treats `p`: a real cost to the true
objective, a spurious reward to the proxy. This is modeled on a documented,
concrete case — automated and learned reward models in RLHF measurably
favoring longer responses independent of their actual content quality
(Singhal et al., "A Long Way to Go: Investigating Length Correlations in
RLHF," 2023, arXiv:2310.03716). `i` stands in for genuine informativeness;
`p` stands in for filler the grader can't distinguish from substance.

A hill-climbing optimizer that can only see `proxy_metric` has no way to know
`p` is doing anything but helping. Nothing in the toy is adversarial or
hand-tuned to fail — it is two plausible, simple functions and a greedy
search.

## 4. Turn the knob: watch two optimizers run

<!-- interactive: GoodhartDivergence -->

Two hill-climbers start at the identical point, `(i=0, p=0)`, and run for the
identical 2,000 steps. One only ever sees `proxy_metric`; the other only ever
sees `true_objective`, as a control. Move the slider through the proxy-only
optimizer's trajectory in 200-step windows and watch the correlation between
what it optimizes and what it was actually meant to improve.

## 5. Observed consequence: the sign flips, and it flips exactly once

In the first window (steps 0-199), while `i` is still climbing toward its
cap, proxy and true rise together: correlation **0.807**. Once `i` saturates
at its cap around step 200, every further unit of proxy improvement has to
come from `p` — and every unit of `p` is a real cost to the true objective.
From that point on, every 200-step window measures correlation between
**-0.998 and -1.000**: not weaker agreement, the *opposite sign*, for the
rest of the run.

By step 1999 the proxy-only optimizer has raised its own visible score from 0
to **371.85** while the true objective it never saw has fallen from 0 to
**-381.00** — worse than doing nothing at all. The control optimizer, given
the true objective directly, stops at `(i=50, p=0)`, true = proxy =
**70.71**, and never touches `p`, because `p` is never a real improvement to
the function it can actually see. Full numbers: [`runs/2026-08-01-goodhart-toy.md`](runs/2026-08-01-goodhart-toy.md).

The mechanism is exactly the mental model in Section 2: while genuine
improvement (`i`) was still cheap relative to gaming it (`p`), the optimizer
took it, and the two metrics agreed. Once genuine improvement ran out, the
optimizer did not stop — it found the next-cheapest lever, which happened to
be the one the true objective penalizes.

## Brief history

The quotable version of this failure is fifty years old. The measurement of it
happening inside a training run is not.

<!-- interactive: GoodhartLineage -->

## The fix and its trade

The failure mode is structural, not a data-quality problem: any proxy that
is imperfectly aligned with the true objective has directions in which it
can be increased without the true objective increasing, and the harder
something searches, the more likely it finds exactly those directions. The
measured mechanism is a sign flip, exactly once: over 2,000 hill-climbing
steps on two functions that share the same genuine-quality term, proxy and
true objective correlate +0.807 while informativeness is still climbing,
then saturate at its cap around step 200, and every later 200-step window
measures correlation between -0.998 and -1.000 — not weaker agreement, the
opposite sign. By step 1999 the proxy-only optimizer has raised its visible
score to 371.85 while the true objective it never saw has fallen to
-381.00, worse than doing nothing; the control optimizer, given the true
objective directly, stops at 70.71 and never touches the padding dimension,
because padding is never a real improvement to the function it can see.

The fix is to treat "how gameable is this metric" as part of the evidence
when choosing a proxy, and to know the exploitable dimensions before
optimization pressure finds them: the mechanism fails here specifically
because the proxy rewards a dimension (`p`) the true objective penalizes,
once the genuinely useful dimension (`i`) is exhausted — a proxy with no
such exploitable dimension, or one where the exploitable dimension is
bounded as tightly as the useful one, would not show this pattern. The
trade is that the defense is expensive by construction: the reason the
proxy exists is that the true objective is too slow or costly to score at
the volume an optimizer needs, so the countermeasure is the same
hold-out-gold discipline the eval stage already runs — held-out human
review, an independent judge, a slower gold metric sampled occasionally —
each costing exactly what the proxy was built to avoid. The mechanism is
documented in a concrete, dated case: automated and learned reward models
in RLHF measurably favor longer responses independent of content quality
(Singhal et al., "A Long Way to Go," arXiv:2310.03716, 2023), and the
quotable version is Goodhart's Law (Goodhart, 1975) — while measuring the
flip inside a training run, as this chapter's toy does, is new. The toy's
boundary is explicit: a rate, and an early-warning signal that transfers to
real systems, are both outside what it establishes.

## Who owns the loop

- **The evaluation team** owns proxy selection and the gameability check:
  "how gameable is this metric" is part of the evidence for keeping or
  replacing a proxy, not a separate concern, and the exploitable-dimension
  audit is done before optimization pressure finds the peeled-away
  directions.
- **The product team** owns the true objective and the gold signal:
  held-out human review or an independent judge is the expensive detection
  axis, and the choice of which slices get it is a product decision about
  what quality actually means.
- **The modeling team** owns the optimization pressure: any reward-model or
  RLHF loop is an optimizer against a proxy, so the reward team owns the
  length-correlation risk (Singhal et al. 2023) and the structural
  countermeasures for the dimensions it controls.
- **The platform team** owns the sampling cadence of the gold metric:
  occasional, expensive ground truth at a frequency the budget can bear is
  the only early-warning signal a real system has, and it has to be
  scheduled rather than assumed.

## What this toy does not establish

- **A rate.** It shows the mechanism can produce total sign reversal in a
  constructed case with two functions chosen to make the point legible. It
  says nothing about how often this happens, or how severely, on any real
  benchmark, reward model, or automated grader this repository has run
  against.
- **That every proxy metric is unsafe.** The proxy here fails specifically
  because it rewards a dimension (`p`) the true objective penalizes, once the
  genuinely useful dimension (`i`) is exhausted. A proxy with no such
  exploitable dimension — or one where the exploitable dimension is bounded
  as tightly as the useful one — would not show this pattern. Section 3's
  mental model names the condition; it does not claim every proxy meets it.
- **A general early-warning signal.** The correlation-by-window computation
  here is a research diagnostic run after the fact on a toy with a known
  ground truth. On a real system there is usually no true objective cheap
  enough to compute at the same frequency as the proxy — if there were, you
  would optimize that instead. Detecting this in practice (held-out human
  review, an independent judge, a slower and more expensive gold metric
  sampled occasionally) is a different, harder problem this toy sidesteps by
  construction.

## Reproduce it

```bash
cd 01-language-model/07-eval/metric-gaming/core
python goodhart.py --steps 2000 --window 200 --seed 0 --out ../runs/goodhart-run.json
```

Deterministic given `--seed`; both hill-climbers use independent `random.Random`
instances seeded identically.

## Check your mental model

**1. Why do proxy and true objective agree in the first 200 steps but not
after?**

<details>
<summary>Answer</summary>

Because for those first 200 steps, the cheapest way to raise the proxy is
also genuinely useful: `i` is far from its cap, `10*sqrt(i)` has a steep
gradient there, and both functions share that term. Once `i` saturates at
its cap around step 200, that shared, genuinely-useful lever is gone — the
only lever left that keeps raising the proxy is `p`, which the proxy rewards
and the true objective penalizes. The optimizer never changed strategy; the
set of moves that improve the proxy simply stopped overlapping with the set
of moves that improve the true objective.

</details>

**2. The control optimizer, given the true objective directly, never touches
`p` at all. Why not, given that `p` is unbounded and free to increase?**

<details>
<summary>Answer</summary>

Because `p` is a pure cost to the true objective (`-0.6*p`, no offsetting
term) — every unit spent on it makes the true objective worse, with no floor
or diminishing effect that would ever make it worth trying. An optimizer that
can see the true objective directly has no reason to ever accept a move that
increases `p`, so it never does. The asymmetry is entirely in what each
optimizer can observe, not in what `p` actually does to the world.

</details>

**3. This toy's correlation flips from +0.807 to -1.000 in exactly one
transition. Would you expect a real reward model or benchmark to show a
similarly sharp, one-time flip?**

<details>
<summary>Answer</summary>

Not necessarily, and the chapter says so directly: the sharp, single flip
here comes from a specific, deliberately simple construction — one lever
with a hard cap, one lever with none. A real proxy metric more plausibly has
several exploitable dimensions with different, non-identical saturation
points, which would smear the transition into a gradual decline rather than
one clean sign reversal. The toy's value is showing the mechanism can produce
total, sustained reversal at all, in a case simple enough to compute exactly
— not predicting the shape of the decline in a system this simple by
construction was never meant to represent.

</details>

**4. Suppose you had access to the true objective as cheaply as the proxy.
What would you do differently, and why doesn't that option exist in most
real deployments?**

<details>
<summary>Answer</summary>

You would optimize the true objective directly, exactly like the control
optimizer in this chapter — there would be no reason to route through a
proxy at all. The reason real deployments can't do this is the reason the
proxy exists in the first place: the true objective (genuine helpfulness,
real user satisfaction, actual task success) is usually expensive, slow, or
impossible to score at the volume and speed an optimizer needs, which is
exactly why a cheap, fast stand-in gets built. The proxy is not a mistake to
be corrected by "just using the real metric" — the cost gap between the two
is the reason a proxy is being used at all, which is also why Goodhart's Law
is a structural risk here rather than an avoidable oversight.

</details>

## Next

[Why should anyone believe the report?](../why-believe-the-number/)
already asks you to distrust a single point estimate; this chapter asks you
to distrust a metric's *meaning* once something is searching against it on
purpose. If you are choosing which proxy to trust for a live decision, return
to [what evidence justifies replacing what you already
run](../README.md) and treat "how gameable is this metric" as part of that
evidence, not a separate concern.
