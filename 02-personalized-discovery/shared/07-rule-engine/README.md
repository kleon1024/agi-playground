---
status: verified
level: applied
verified: 2026-07-27
base: none
---

# Who can answer why this item was shown?

**Question:** when a regulator, lawyer, or partner asks why an item appeared, is “the weights said so” an answer? It is not. Some decisions need an external owner who can read, change, and be held accountable for them without waiting for a model retrain.

The artifact is a decision record: for one impression it lists the policy version, rules that fired, candidates each removed or boosted, precedence, and the final result. That is the boundary between a learned preference and a rule. A learned ranker is appropriate when the system must infer an uncertain preference from data. A rule is appropriate when a legal, safety, contractual, or editorial owner defines what must happen and must be able to revise it on a policy timescale.

**Before this:** [stage 06's assembled slate](../06-mixing/) — this stage
applies constraints that slate assembly has no way to know about, and can
remove candidates mixing already spent a beam search choosing.

**Related:** the permission and precedence contract here is
[the agent harness](../../../01-language-model/06-agent/) applied to a
ranking decision rather than an agent's tool call — the same two missions
that need this contract are what promoted it out of mission-local code.

## Put policy in data, not in scattered branches

Scatter policy across imperative `if` statements in serving code and you get something hard to inspect, reorder, or attribute. Represent it as declarative data instead — the way the core engine does for regional blocks, safety blocks, an editorial boost, and a per-creator cap — and you can apply it in explicit priority order: blocks terminal, boosts annotating surviving scores, the cap running after ranking because its outcome depends on the order of survivors. That ordering is product policy, not an implementation accident.

<!-- interactive: ConstraintLadder -->

The executable candidate set has sixteen fixed items. In the US request, the regional block removes ten EU-only candidates and keeps six. Tightening the per-creator cap from two to one then removes three more, each with its own explanation. In the EU request, regional eligibility leaves ten candidates and the safety rule removes those ten. Neither rule empties the full catalogue alone; together, in that request context, they produce an empty set. The engine reports the joint condition and each rule's solo removal rather than silently returning an empty slate.

Watch for why this empty-set detection matters: independently reasonable policies compose. Let a system quietly return nothing and the caller can no longer distinguish "there were no candidates" from "the policy intersection removed all candidates." A real serving path must instead choose a declared fallback, escalate to an operator, or return a transparent unavailable state — never bypass a safety rule merely to populate a page.

Every rule has recall cost. The run reports it as candidates removed out of the requested set. That makes policy tradeoffs inspectable: safety and licensing may justify a loss of reach, while an accidental cap may not. Rules do not merely explain an existing slate; they constrain what later learned stages can ever choose.

## Change quickly without claiming correctness

The production example includes a CEL-style policy document and evaluator. Production alternatives include Open Policy Agent/Rego and a feature-flag-plus-policy service. Each should version policies, capture the evaluated inputs, and make rollout/rollback ownership explicit. A policy edit can then take minutes, while retraining a model could take days. That speed is the point of the layer, not a reason to evade review.

```bash
uv run python core/rule_engine.py
uv run python prod/cel_policy.py
```

The core has no third-party dependency. Its candidate set is hand-built so the empty-set case remains reproducible. The run verifies the engine's precedence and attribution mechanics, not that any displayed policy is good. Auditable enforcement of a bad policy is still bad policy. Nor does this stage prove that the recall cost is acceptable; it only makes the cost measurable and visible. Stage 08 must serve the resulting funnel inside the declared latency budget.

Policy changes require their own review trail: author, owner, justification, effective time, targeted surface, test cases, and rollback. A policy service that can alter eligibility in minutes must make that power observable. Keep the decision record with the impression event, not only in mutable logs, so later investigation can evaluate the exact version and context that produced a result. This does not require exposing sensitive policy internals to end users; it requires a trustworthy internal explanation boundary.

Decide, for each rule, whether it fails closed or fails open — do not let that be an accident. Make licensing and safety fail closed: if the evaluator is unavailable, do not show uncertain inventory. Let a non-critical editorial boost fail open instead: omit the boost but keep eligible content. That choice belongs in each rule's contract because the availability cost and safety cost differ. The core illustrates the prerequisite fact: an engine must make its removal and its empty output visible before any fallback is safe to design.

Rules can be tested as policy examples before rollout. Include a representative input, the expected kept and removed IDs, the expected reasons, and a counterexample that must remain allowed. Evaluate old and proposed policy versions on the same candidate sample to quantify how much reach changes. This is not enough to approve a policy, but it prevents an accidental syntax or precedence change from silently becoming a broad block. Human review then decides whether the measured change is intended.

Do not use the rule layer as a hiding place for model defects. A temporary rule that masks a bad prediction may be appropriate for immediate safety, but it should name an expiry, owner, and remediation path. Otherwise policy accumulates into a second, untestable ranker. The invariant is clear ownership: rules state externally accountable constraints; learned stages estimate preferences inside those constraints.

## Next

[Stage 08 — serving](../08-serving/) has to fit everything upstream of it,
rule engine included, inside one request's latency budget.

A detour from here: [when does the rule engine return an empty
set?](when-the-rules-collide/) — the frontier swept across region and cap:
EU empties at every cap, US never does, and the audit record is what makes
the emptiness diagnosable and the policy conversational.

Another detour: [a rule engine's failure mode is interaction, not any
single rule](the-empty-set-was-two-rules/) — the recorded run read: EU
regional and safety each leave survivors, and applied together they empty
the set — the joint failure the engine's check exists to find.

A third detour: [the rule nobody tested](when-the-rule-is-a-typo/) — the executed typo read: a misspelled attribute matches nothing and returns an empty set silently, so every rule needs a coverage check.
