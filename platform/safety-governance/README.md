---
status: draft
label: Safety and governance
---

# Safety and governance

**Question:** how does a declared guardrail become an enforceable boundary
rather than a sentence in a design document?

Safety is a system property. A model may produce an acceptable sentence while
the surrounding system exposes private data, applies the decision to the wrong
person, or performs an action the user never authorized.

This layer turns each mission guardrail into:

```text
definition -> measurement -> enforcement point
           -> audit record -> escalation owner
```

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

## Current forcing function

Mission 01 is local and single-user, so it exercises tool permissions and
artifact provenance but has little external blast radius. Mission 02,
[personalized discovery](../../missions/02-personalized-discovery/), forces
this layer to become concrete through content eligibility, diversity, fairness,
latency, and market-specific launch guardrails.

This page defines the contract. It remains `draft` until those controls have
executable implementations and recorded failure-path tests.

## Check your mental model

1. What makes a guardrail executable?
2. Why must enforcement live upstream of the harmful action?
3. Which permissions should a derived feature inherit?
4. When should a dependency failure fail open versus fail closed?
5. What exact decision is an escalation asking another owner to make?

## Next

Apply these rules inside a mission contract before implementation. A guardrail
added after a favorable experiment result is not a precommitted launch
boundary.
