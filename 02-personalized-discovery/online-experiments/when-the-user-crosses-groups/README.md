---
status: verified
level: applied
base: scratch
label: When the user crosses groups
verified: 2026-08-07
---

# The analysis unit and the user who sits in both arms

**Question:** [stage 54's gate](../) checks that the analysis unit matches
the randomization unit. This chapter measures what happens when it does
not — the same user's sessions are treated as independent — and when the
same user carries treatment into a later control session.

**Before this:** [stage 54's gate](../) for the unit check and its place
in the verdict, and [stage 48 — realtime user state](../../48-realtime-user-state/)
for why a user's sessions are a user property, not a stream of independent
draws.

## The unit mismatch, executed

The run ([record](runs/2026-08-07-unit-mismatch.md)) repeats a null
experiment 500 times: 400 users, 5 sessions each, user effect and session
noise equal (ICC 0.5). Users are randomized once; the analysis differs:

| analysis | false positives | declared alpha |
|---|---:|---:|
| per-session (naive) | 24.0% | 5% |
| per-user (clustered) | 4.2% | 5% |

The design effect matches the closed form sqrt(1 + (m-1)*ICC) = sqrt(3) =
1.73: the naive standard error understates the clustered one by that
factor, so the per-session p-value lies toward significance nearly five
times more often than it should.

## The carryover, executed

The same user can sit in treatment for two sessions and control for the
next two. If the treatment changes behavior persistently, the later control
session carries the treatment's residue. The run measures it:

| estimator | estimate | bias vs true +0.5 |
|---|---:|---:|
| naive per-session | +0.428 | -0.072 |
| washout (drop first session after switch) | +0.495 | -0.005 |

The naive estimate understates the effect because control sessions that
follow treatment inherit its residue — the control arm is polluted by
users who just left treatment. The washout removes the first session after
an arm switch and recovers the estimate.

## Why this is the unit, not the model

Both failures are properties of the experiment design, not of the model:
no ranker can fix an experiment whose standard error is computed over the
wrong independence assumption, and no estimator can recover the effect from
control sessions that were never clean. The industry fixes are structural.
Analyze at the randomization unit (per user, or cluster-robust standard
errors at the user level). Declare a washout window when users can cross
arms. And where two experiments must run on the same users, use layered
randomization (Tang et al., 2010, KDD): each experiment owns a layer keyed
to the user, so a user in treatment for one layer can be control for
another without the two experiments overwriting each other's buckets. The
cost of these fixes is what the gate measures: per-user analysis has less
effective sample than per-session, and washout windows waste the first
sessions after every switch — both price the experiment's power, which is
why 09's report and this stage both demand the trade be stated before the
run.

## The fix and its trade

The fix is structural, not model-side: analyze at the randomization unit
(per user, or cluster-robust standard errors at the user level), declare
a washout window when users can cross arms, and use layered
randomization where two experiments run on the same users (Tang et al.,
KDD 2010). The executed runs price both failures — per-session analysis
rejects 24.0 percent of null experiments against a declared 5 percent,
with the naive standard error understating the clustered one by the
design effect sqrt(3) = 1.73; and the carryover run shows the naive
estimate at +0.428 against the true +0.5, recovering to +0.495 once the
first session after each switch is dropped.

The trade is that every fix prices the experiment's power: per-user
analysis has less effective sample than per-session, and washout windows
waste the first sessions after every arm switch, so the cost is stated
before the run rather than discovered in the analysis. Both failures are
properties of the design, not of the model — no ranker can fix a
standard error computed over the wrong independence assumption, and no
estimator can recover an effect from control sessions that were never
clean — which is why the unit, the washout, and the layering are owned
before the experiment starts.

## Who owns the loop

- **The experimentation-platform team** owns the analysis-unit check and
  the clustered analysis at the randomization unit.
- **The product and analysis team** owns the washout-window decision,
  set from the logged sequences of arm exposure.
- **The measurement team** owns the within-user ICC measurement and the
  power statement that prices the unit and washout before the run.

## Evidence boundary

The simulations are synthetic and deterministic. They demonstrate the
mechanism and its measured size, not a real experiment's ICC or carryover.
A real experiment measures its own within-user correlation (ICC) and its
own carryover window from logged sequences of arm exposure; the washout
length is an empirical decision, and the price is declared in the power
analysis before the experiment starts.

## Check your mental model

**1. Why does per-session analysis reject 24% of null experiments?**

<details>
<summary>Answer</summary>

Because sessions from the same user are correlated: the naive standard
error treats them as independent, so it is too small by the design effect
sqrt(1 + (m-1)*ICC). A too-small denominator makes the p-value too small.
The per-user analysis, which aggregates each user to one observation,
restores the declared 5%.

</details>

**2. Carryover biases the estimate downward in the run. Could it bias
upward?**

<details>
<summary>Answer</summary>

Yes. The direction depends on the mechanism: if treatment changes behavior
persistently, control sessions after treatment inherit a residue and the
control mean moves toward the treatment value, shrinking the estimated
effect. If the residue is negative (a backlash, a novelty that wears off),
the bias runs the other way. The sign is mechanism-specific; the washout
removes the contamination regardless.

</details>
