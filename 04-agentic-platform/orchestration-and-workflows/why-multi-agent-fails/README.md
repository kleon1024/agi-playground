---
status: draft
level: reference
label: Why multi-agent fails
---

# The production record of free multi-agent coordination

> Dated survey, 2026-08-14. Sources cited inline. No number here was
> measured in this repository.

**Question:** the stage claims deterministic workflows fail less than free
multi-agent coordination on structured work. What is the evidence, and
what exactly breaks when agents are left to coordinate with each other?

**The artifact this chapter follows** is the failure taxonomy of the
2025–2026 multi-agent frameworks — CrewAI, AutoGen/AG2, LangGraph — as
reported by teams that ran them in production. The repository's own
orchestration demo sits beside this chapter as the deterministic contrast.

By the end you will be able to defend "orchestrate the steps deliberately"
with named failure modes instead of instinct.

## The three failure modes that dominate

Production write-ups of the 2025–2026 multi-agent wave converge on three
patterns ([Aliyun engineering analysis,
2026-06](https://developer.aliyun.com/article/1744508), covering CrewAI,
AutoGen/AG2, and LangGraph deployments):

1. **Non-terminating conversation.** The highest-frequency failure in
   AutoGen production runs. Two agents negotiate, neither can satisfy the
   other, and the loop does not end. The fix deployed in practice is an
   aggressive termination condition — which is, in the write-up's own
   words, "a parent stepping in".
2. **Command races and state hallucination.** With no shared state
   primitive, agents act on stale or invented beliefs about what another
   agent already did — duplicate work, conflicting edits, and a
   failure-rate multiplication that one write-up states plainly: two agents
   working together does not double throughput, it doubles faults.
3. **Framework immaturity as a multiplier.** AutoGen went into maintenance
   mode with its migration target stated as Microsoft Agent Framework or
   AG2 ([FutureAGI comparison,
   2025-12](https://futureagi.com/blog/crewai-vs-langgraph-vs-autogen-2026/)).
   The one differentiator that survived production scrutiny was LangGraph's
   persistence — durable state, not coordination.

## What the fix looks like

Every fix production teams converged on moves *away* from free
coordination: aggressive termination, durable state, and a deterministic
skeleton. Anthropic's 2026 guidance
([multi-agent coordination
patterns](https://claude.com/blog/multi-agent-coordination-patterns))
frames the same conclusion positively: for structured, mission-critical
work, orchestrate the steps deliberately and let the agent fill the gaps;
reserve free agents for exploration. The taxonomy of patterns (orchestrator
-subagent, agent teams with persistent workers, message bus, shared state)
is a menu of *governed* coordination, not a license for agents to talk
unattended.

## What this does not say

It does not say multi-agent systems never work — Spotify's Honk and the
orchestrator-subagent patterns are production successes. It says the
successes have a skeleton: a bounded task, a verifier, and a coordinator
that owns routing. The failures are the cases where the skeleton was left
to emerge from conversation.

**Next:** the stage's mechanism demo — the deterministic contrast, run
against this mission's own task set ([stage root](../)).
