---
status: verified
level: applied
base: scratch
label: Online experiments
verified: 2026-08-07
---

# How do you know the change you shipped actually helped?

**Question:** [stage 09's report](../09-report/) ended with an honest
refusal: offline replay cannot establish online outcome. This stage asks
the question 09 could not answer — how do you know a change to the
deployed funnel helped? — and answers: an online experiment, read through
a validity gate that catches the three ways an experiment's p-value can be
true while its conclusion is wrong.

**Before this:** [stage 09 — report](../09-report/) for the offline verdict
that cannot see online outcome, and [stage 47 — monitoring and drift](../47-monitoring-and-drift/)
for the prediction-observation gap the experiment is the controlled version
of. The traffic-efficient alternative to a between-user A/B,
[ads stage 38 — interleaving experiments](../../ads/38-interleaving-experiments/),
is where ranking-only comparisons go.

## The gate, executed

The run ([record](runs/2026-08-07-online-experiments.md)) reads three
synthetic experiment logs and returns a verdict for each. The gate checks
three validity conditions — the split matches the declared ratio, the
analysis unit matches the randomization unit, and switchback logs carry no
serial dependence — and names the first failure, the way 09's report names
the first breached guardrail:

| fixture | what is wrong | verdict |
|---|---|---|
| broken | bucket constant drifted to 51.5% while config says 50/50 | **INVALID — SRM**, chi2=21.52, p=3.51e-06 |
| fixed | same users, corrected buckets | INTERPRETABLE, chi2=0.04, p=0.832 |
| switchback | minutes analyzed as independent under block randomization | **INVALID — unit mismatch**, SE gap 3.19x |

The broken fixture is the lesson: an experiment "wins" with p=0.03 and the
effect is a ghost, because the traffic split itself is broken. The gate
finds it before the outcome test is read. The fixed fixture is the same
log with the constant corrected — which is why the gate exists: the fix is
cheap, the silence is not.

<!-- interactive: OnlineExperiments -->

## The three failure modes, named

**The split lies (sample ratio mismatch, SRM).** The bucketing hash that
decides who sees which arm can drift from the config that declares the
split: a changed constant, bucketing on the wrong key, eligibility computed
after bucketing. The allocation-ratio chi-square test catches any deviation
with far less traffic than the outcome test needs — the
[when-the-split-lies detour](when-the-split-lies/) measures that it fires
at roughly 2,000 users while a 2% effect needs 78,000. SRM is the first
metric to check in every experiment, daily (Fabijan et al., 2019, KDD);
Kohavi, Tang and Xu (2020) call it the most important experiment metric
because it signals the experiment is not measuring what the config says.

**The analysis unit does not match the randomization unit.** Users are
randomized once, but sessions are analyzed as if each were an independent
observation. Sessions from the same user are correlated, the naive standard
error is too small, and the p-value lies toward significance — the
[when-the-user-crosses-groups detour](when-the-user-crosses-groups/)
measures 24% false positives at a declared alpha of 5%. The same mismatch
appears as carryover: a user who sits in treatment and then control carries
the treatment's residue into the control measurement, biasing the estimate.
Tang et al. (2010, KDD) solve the interference side of this with layered
experiments: each experiment randomizes within its own layer keyed to the
user, so two experiments do not overwrite each other's buckets and a user
can be in treatment for one layer and control for another.

**The market leaks across the groups (two-sided traffic).** In a
marketplace or ad exchange, randomizing users does not contain the
intervention: a treatment user's purchase consumes shared supply, and a
changed ranking changes the equilibrium for everyone. The unit of
randomization becomes a time block, and the 
[when-the-traffic-is-two-sided detour](when-the-traffic-is-two-sided/)
measures the consequences: per-minute analysis rejects 53% of null
experiments, and the block unit is so coarse that a 1% effect needs 36
years of half-hour blocks. Bojinov, Simchi-Levi and Zhao (2023, Management
Science) formalize the switchback design and its variance inflation; Uber's
engineering practice is the field account of when it is worth it.

## The fix and its trade

The fix is the validity gate itself: check the split (allocation-ratio
chi-square), the analysis-unit-to-randomization-unit match, and serial
dependence before reading the outcome, so an experiment is INTERPRETABLE
only when all three hold. The executed fixtures price the repair — the
broken fixture's drifted bucket (51.5 percent against a declared 50/50)
fails SRM with chi2 = 21.52, p = 3.51e-06 while its p = 0.03 outcome
would have shipped a ghost, and the corrected log turns INTERPRETABLE
(chi2 = 0.04, p = 0.832). The gate is cheap relative to what it stops:
SRM fires at roughly 2,000 users while a 2 percent effect needs 78,000,
so the split is checked daily, before the outcome test is read.

The trade is that validity costs power, and the honest design is
sometimes the slow one. Matching the analysis unit to the
randomization unit means clustering standard errors instead of reading
naive p-values — the session-nested analysis that skips it sees 24
percent false positives at a declared alpha of 5 percent — and
two-sided markets need switchback blocks whose variance inflation is
severe: per-minute analysis rejects 53 percent of null experiments, and
the block unit is so coarse that a 1 percent effect needs 36 years of
half-hour blocks. Where ranking-only comparisons are the question, the
traffic-efficient alternative is stage 38's interleaving, which is why
the unit choice itself is owned by the product team, not the
experimentation platform alone.

## Who owns the loop

The experiment only proves what it claims if someone owns each side of
the validity gate, and the handoffs are where the stage's failure modes
live:

- **The experimentation platform team** owns the split: the bucketing
  hash, the declared ratio, and the daily allocation-ratio check that
  catches SRM before the outcome test is read. It owns the
  randomization, and the when-the-split-lies detour is its failure mode.
- **The analysis team** owns the unit: the analysis unit must match the
  randomization unit, the standard error must be clustered when sessions
  are nested in users, and the carryover washout must be declared. It
  owns the verdict, and the when-the-user-crosses-groups detour is its
  failure mode.
- **The product or market team** owns the unit choice itself: when the
  traffic is two-sided, it decides whether user-level randomization can
  contain the intervention or whether switchback blocks are the only
  honest design. It owns the power trade, and the
  when-the-traffic-is-two-sided detour is its failure mode.

When the ownership is implicit, each side optimizes its own number: the
platform team ships buckets, the analysis team reads p-values, and nobody
owns the unit — so a session-nested analysis declares significance that
the design never supported, and the marketplace scales a change that
leaked across the control.

## Why this belongs in the mission

Every stage before this one changed something the mission can ship: a
retrieval cut, a value-tree weight, a cascade stage. Stage 09 said the
offline report cannot establish that any of it helped a real user. This
stage is the only way to make that claim, and it owns the discipline that
keeps the claim honest. The guardrail discipline of 09 — a report is NOT
MET if any guardrail breaches — carries over exactly: an experiment is
INTERPRETABLE only if all three validity conditions hold, and the guardrail
metrics (latency, revenue, cold-start) ride on the same experiment as vetoes,
not extra points.

## Evidence boundary

The three fixtures are explicitly synthetic: they prove the gate's verdict
logic, not any real experiment or mission outcome. The gate is what runs
against a real log; a production service persists the same shape in a
metrics store and renders the verdict in an experimentation platform (the
`prod/` path reads an emitted log with pandas and scipy and returns the
same verdicts). The runs do not verify that any deployed change helped; they
verify that the tool for finding that out refuses to lie.

## Check your mental model

Answer each before opening it.

**1. An experiment reports p=0.03. Why might the effect still be a
ghost?**

<details>
<summary>Answer</summary>

Because the p-value is only as real as the experiment behind it. If the
traffic split is broken (SRM), the two arms are not the populations the
config says they are, and every comparison built on them is biased. If the
analysis unit does not match the randomization unit, the standard error is
too small and the p-value lies toward significance. The p-value is
computed correctly; the experiment it describes does not exist.

</details>

**2. Why is the allocation-ratio check run daily, before the outcome
test?**

<details>
<summary>Answer</summary>

Because SRM detection needs far less traffic than outcome detection: the
split check fired at roughly 2,000 users in this stage's run while a 2%
effect needs about 78,000 for 80% power. Waiting for the outcome to
discover the split is broken wastes the whole experiment; the daily check
is the platform's job, declared in the experiment config, not the
analyst's afterthought.

</details>

**3. Why does a marketplace randomize time blocks instead of users?**

<details>
<summary>Answer</summary>

Because user-level randomization leaks treatment into control: a treatment
user's purchase consumes shared supply, and a changed ranking moves the
equilibrium for everyone. Time blocks contain the intervention, but the
price is power — the effective sample is the number of blocks, so only
large effects are detectable in reasonable time. Interleaving (ads stage
38) is the traffic-cheap alternative for ranking-only changes; switchback
is for marketplace-scale changes.

</details>

## Next

An experiment passes the gate or it does not; the three detours measure why
each check exists. A detour from here: [the split lies](when-the-split-lies/)
— the executed read: a bucket threshold that drifted from 50 to 52 fires
the SRM check at 2,000 users, 39x before the outcome test has power.

Another detour: [the user crosses groups](when-the-user-crosses-groups/) —
the executed read: per-session analysis rejects 24% of null experiments at
declared alpha 5%, and a treatment session pollutes the next control
session by 0.3 until a washout removes it.

A third detour: [the traffic is two-sided](when-the-traffic-is-two-sided/)
— the executed read: per-minute analysis rejects 53% of null switchbacks,
block-level analysis restores validity, and the block unit prices a 1%
effect at 36 years.

A fourth detour: [the budget runs out](when-the-budget-runs-out/) — the
executed read: the 39,244-users-per-arm figure derived from the sample-size
formula, and the four levers (MDE, metric variance, CUPED, allocation and
ramp) priced in calendar days, which is how the experiment that cannot
finish this quarter gets its design verdict.

A fifth detour: [the experiments overlap](when-the-experiments-overlap/) —
the executed read: a shared bucket makes both experiments report 1.994 for
effects that sum to 1.5 plus a 0.5 interaction, independent layers restore
each experiment's own main effect, and only the 2x2 factorial reads the
interaction.
