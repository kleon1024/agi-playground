---
status: draft
level: applied
label: Safety and governance
---

# How does a guardrail become something that actually stops you?

Rather than a sentence in a design document that no code reads.

Every `mission.yaml` in this repository declares guardrails. This chapter is
what has to exist for those declarations to be worth writing down, and missions
arrive here at the point where a guardrail must be enforced rather than
promised.

Safety is a system property. A model may produce an acceptable sentence while
the surrounding system exposes private data, applies the decision to the wrong
person, or performs an action the user never authorized.

This layer turns each mission guardrail into:

```text
definition -> measurement -> enforcement point
           -> audit record -> escalation owner
```

**Before this:** [act and coordinate](../../capabilities/act-coordinate/), for
the permission and stop-condition contract a guardrail has to attach to.

## 1. Write guardrails as executable conditions

“Do not harm quality” cannot be measured. A useful guardrail names a population,
metric, direction, tolerance, and decision:

```text
For new users in each launch market,
report rate must not exceed the agreed baseline limit.
If it does, stop expansion and roll back the treatment.
```

Every guardrail needs:

- numerator and denominator;
- event and attribution window;
- slices where the rule applies;
- missing-data behavior;
- warning and hard-stop thresholds;
- owner and escalation path.

If two teams calculate the guardrail differently, it is not yet a shared
boundary.

## 2. Enforce at the subsystem that owns the risk

Measurement after the event is not enforcement. Place the control where the
harm can still be prevented:

| Risk | Enforcement point |
|---|---|
| ineligible content enters ranking | candidate eligibility |
| forbidden tool call | harness permission check |
| private field enters training | data access and export policy |
| latency exceeds service budget | admission and rollout gate |
| unsafe model version ships | release gate |

A downstream dashboard cannot compensate for an upstream system that still
allows the action.

## 3. Minimize authority and blast radius

Grant only the data, tools, duration, and population required for the current
job. Separate:

- identity from product enrollment;
- data possession from permitted use;
- read access from action authority;
- experiment exposure from full launch;
- local rollback from external irreversibility.

Smaller blast radius turns a defect into a bounded incident. It does not make
the defect acceptable, but it preserves recovery options.

## 4. Preserve provenance

For every high-impact decision, retain enough information to reconstruct:

```text
who or what initiated it
which policy and model version applied
which input evidence was used
which action occurred
which guardrails were evaluated
what result and override followed
```

Do not log secrets or unrestricted personal data merely to make an audit
complete. Provenance itself must follow retention and access policy.

## 5. Treat data use as a scoped permission

“The company has this data” is not evidence that every product may use it.
Record purpose, consent basis, retention, geography, access group, and deletion
path.

Derived features inherit restrictions from their source when they can still
identify or materially affect a person. A shared database is not an automatic
authorization boundary.

Training and evaluation datasets need provenance through every transformation.
Once source scope is lost, later filtering cannot reconstruct whether the use
was permitted.

## 6. Test the failure path

Before launch, exercise:

- guardrail breach;
- missing or delayed telemetry;
- policy-service unavailability;
- rollback;
- human override;
- audit reconstruction.

A policy that works only when every dependency is healthy is not an enforcement
boundary. Define fail-open versus fail-closed behavior explicitly for each
risk.

## 7. Make escalation a decision, not a meeting

An escalation packet should contain:

1. the breached condition;
2. affected population and duration;
3. current containment;
4. evidence quality and unknowns;
5. options with residual risk;
6. the named decision required.

Escalation does not transfer ownership of analysis. It transfers a decision
whose authority exceeds the current team.

## Chapters that measure instead of naming

| Read this | When you need to decide | It returns |
|---|---|---|
| [eval gates](01-eval-gates/) | whether a release-blocking threshold can be computed instead of reviewed by hand | a from-scratch gate mechanism, and a real sweep showing no threshold clears both false blocks and false passes at once |

## Current forcing function

Mission 01 is local and single-user, so it exercises tool permissions and
artifact provenance but has little external blast radius. Mission 02,
[personalized discovery](../../missions/02-personalized-discovery/), forces
this layer to become concrete through content eligibility, diversity, fairness,
latency, and market-specific launch guardrails.

This page defines the contract. It remains `draft` until those controls have
executable implementations and recorded failure-path tests.

## Check your mental model

**1. What makes a guardrail executable?**

<details>
<summary>Answer</summary>

"Do not harm quality" fails as a guardrail not because it's wrong but because
no code can evaluate it — there's no numerator, no denominator, no window, no
threshold. The report-rate example works because every one of those is
answered: the population (new users, each launch market), the metric
(report rate), the comparison (agreed baseline limit), and the action
(stop expansion, roll back). A guardrail becomes executable exactly when two
teams computing it independently get the same number — if they don't, the
"boundary" is still just a shared intention, not a shared measurement.

</details>

**2. Why must enforcement live upstream of the harmful action?**

<details>
<summary>Answer</summary>

Because a dashboard can only tell you the harm already happened — it has no
power to prevent the next occurrence. The table's five examples all name a
point *before* the action completes: candidate eligibility before a ranked
item ships, the harness permission check before a tool call executes, the
data access policy before a private field reaches training. Move the check
one step later — say, auditing ranked results after they've shipped — and the
harm has already reached the user by the time anyone measures it. Enforcement
has to sit at the last point where the system can still say no.

</details>

**3. Which permissions should a derived feature inherit?**

<details>
<summary>Answer</summary>

A derived feature inherits its source's restrictions whenever it can still
identify or materially affect the person it came from — the transformation
doesn't launder the restriction away just because the output looks different
from the input. This is why "the company has this data" and "a shared
database" are explicitly called out as *not* automatic authorizations: a
database boundary is a storage fact, not a permission fact, and a feature
derived from restricted data stays restricted unless the derivation itself
breaks the link back to an identifiable person.

</details>

**4. When should a dependency failure fail open versus fail closed?**

<details>
<summary>Answer</summary>

The chapter deliberately doesn't give one rule for every risk — it asks you to
define fail-open vs. fail-closed *per risk*, because the two failure modes
trade off differently depending on what's at stake. Fail closed when the
uncontrolled action is the worse outcome (an unsafe model version shipping
without its release gate) — better to halt than let harm through unchecked.
Fail open when the guardrail is a secondary check and refusing service
entirely is the worse outcome relative to the risk it guards against. Picking
one policy for every dependency, instead of reasoning about each risk's own
asymmetry, is exactly the shortcut this section is warning against.

</details>

**5. What exact decision is an escalation asking another owner to make?**

<details>
<summary>Answer</summary>

Item 6 in the escalation packet — "the named decision required" — is the
whole point: an escalation is not a request for someone else to re-run the
analysis, it's a request for someone whose authority exceeds the current
team's to make one specific call, informed by the other five items (the
breach, its scope, current containment, evidence quality, and the options with
their residual risk already laid out). If the packet doesn't name that
decision explicitly, it has handed over the file without handing over the
question — the receiving owner is left to reconstruct what's actually being
asked of them.

</details>

## Next

Apply these rules inside a mission contract before implementation. A guardrail
added after a favorable experiment result is not a precommitted launch
boundary.
