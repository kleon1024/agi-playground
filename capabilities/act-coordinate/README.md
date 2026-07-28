---
status: draft
label: Agent systems
---

# Agent systems

**Question:** what must the software around a language model own before the
model can take useful actions safely and repeatably?

An agent is not “a model with a long prompt.” It is a loop with explicit state,
tools, validation, permissions, and termination:

```text
observe -> decide -> propose action -> validate
        -> execute -> record result -> decide again
```

The harness owns every arrow. The model proposes; the harness decides what is
valid, permitted, and observable.

## 1. Start from a task contract

Before calling the model, state:

- the goal and completion evidence;
- available actions and their argument schemas;
- state the model may observe;
- time, token, and tool-call budgets;
- prohibited actions;
- when to stop and ask a human.

Without this contract, the loop cannot distinguish progress from plausible
motion.

Use a bounded example throughout this chapter: inspect a repository, change one
file, run a focused test, and return the verified result. The task has a visible
artifact and a deterministic check.

## 2. Make the loop inspectable

Advance the loop below one phase at a time. Notice where generation ends and
deterministic software begins.

<!-- interactive: AgentLoopSimulator -->

The model may generate reasoning and a proposed tool call. The harness then
parses, validates, checks permission, executes, and returns the real
observation. The model must never invent the observation that a tool would have
returned.

The trace needs stable event types:

```text
model_request
model_response
action_proposed
action_rejected | action_executed
observation
completion | budget_exhausted | human_required
```

This event log is both the debugging surface and part of the evaluation record.

## 3. Design tools around decisions

A tool should perform one bounded operation with a schema that makes invalid
states difficult to express.

Bad contract:

```text
run(command: string)
```

Safer contract for a search task:

```text
search_text(query, path, file_glob, max_results)
```

The second contract narrows permission, improves error messages, and produces
structured output. General code execution may still be necessary, but it
belongs behind stronger isolation and confirmation.

For every tool define:

- arguments and validation;
- side effects;
- idempotency and retry behavior;
- timeout and output limit;
- sensitive fields to redact;
- error classes the model can act on.

MCP standardizes how tools, resources, and prompts are exposed across hosts. It
does not decide whether a call is safe. The host remains the policy boundary.

## 4. Treat observations as untrusted data

Web pages, files, tool output, and retrieved documents can contain instructions
that conflict with the user's task. The harness must distinguish user authority
from data being processed.

Layered controls include:

- label tool output as untrusted context;
- grant only task-scoped capabilities;
- prevent read content from directly authorizing a higher-privilege action;
- validate action arguments outside the model;
- require confirmation at the irreversible boundary;
- log actor, action, arguments, result, and policy decision.

Prompt wording alone cannot enforce these properties. The security invariant
lives in runtime permissions.

## 5. Choose context instead of filling it

More context is not automatically better. Irrelevant or stale evidence can
dilute the information needed for the current decision.

Use three layers:

1. **stable contract**: goal, policies, and tool schemas;
2. **working state**: recent actions and current artifact;
3. **retrievable history**: files, traces, or summaries loaded when needed.

Exact filesystem search is often better than embedding retrieval for code
because names and paths are addressable. Semantic retrieval earns its cost when
the corpus is unstructured and the relevant evidence cannot be named exactly.

Compaction must preserve decisions, constraints, unresolved failures, and
artifact identifiers. A summary that keeps the narrative but drops an error
message or file path can make the next action impossible to verify.

## 6. Separate reversible and irreversible actions

Risk is a property of the action and its destination:

| Tier | Examples | Default handling |
|---|---|---|
| read-only | search, inspect, calculate | allow within scope |
| reversible local change | edit tracked files | checkpoint and verify |
| privileged but bounded | deploy, modify shared config | require explicit authority and logs |
| irreversible external effect | send, pay, delete production data | confirm at action time |

Frequent confirmation for low-risk reads trains users to approve blindly.
Broad standing permission for high-risk actions makes one bad turn expensive.
Capability-scoped permission keeps the confirmation rate aligned with risk.

A sandbox reduces blast radius for code execution. It does not make network,
credential, or external-system effects reversible.

## 7. Recover from malformed and failed actions

Tool use is probabilistic at the model boundary and deterministic after
validation. Handle failures explicitly:

```text
parse failure        -> return schema error, do not execute
validation failure   -> return field-level correction
permission failure   -> stop or request authority
tool failure         -> return typed runtime error
ambiguous outcome    -> inspect state before retry
```

Retries need a reason and a limit. Repeating the same call after an unknown
side effect can duplicate writes. Idempotency keys or state inspection should
own that boundary.

## 8. Delegate only independently verifiable work

Sub-agents are useful when a task decomposes into bounded work with separate
evidence. A delegated task should name:

- its output artifact;
- allowed files or systems;
- prohibited actions;
- verification command;
- unresolved-risk format.

The child returns a result, not authority. The parent still integrates and
verifies it.

Delegation carries costs: context fragmentation, coordination overhead, and
error propagation. If two tasks edit the same state or depend on each other's
intermediate decisions, parallel agents usually make the system harder to
reason about.

Depth limits and budgets prevent recursive delegation from becoming unbounded.

## 9. Evaluate the harness, not only the model

Run the same task set while changing one variable:

- model with harness fixed;
- tool description with model fixed;
- context strategy with both fixed;
- retry or permission policy with everything else fixed.

Measure task completion, policy adherence, tool errors, retries, latency, cost,
and human interventions. A model comparison that changes the tool set at the
same time cannot attribute the result.

The best trace is not the longest. It is the shortest trace that preserves why
each action was allowed and how completion was verified.

## Run the vertical slice

[Mission 01, agent](../../missions/01-language-model-agent/06-agent/) wraps the
served model in a minimal harness. The minimum credible artifact contains:

- typed tools;
- validation and permission checks;
- real observations;
- termination and budget handling;
- structured traces;
- success and failure episodes.

That run can establish behavior for its declared tools and tasks. It cannot
establish autonomous reliability across arbitrary systems.

## Check your mental model

1. Which steps belong to the model, and which belong to deterministic runtime?
2. Why is tool output untrusted even when the tool itself is trusted?
3. What information must survive context compaction?
4. When is retrying more dangerous than stopping?
5. Which property makes a task suitable for sub-agent delegation?

## Next

This capability completes the first vertical slice. Return to
[evaluation](../../platform/evaluation-observability/) and evaluate the full
unit: checkpoint, serving configuration, harness, tools, permissions, and
environment.

Primary references: ReAct, SWE-agent and agent-computer interfaces, MCP,
MemGPT, AgentDojo, harness-aware evaluation, and policy-adherence environments.
