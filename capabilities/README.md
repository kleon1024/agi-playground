---
status: draft
level: applied
---

# What makes something a capability rather than a platform chapter?

Not "more than one mission uses a similar technique." A capability is a
reusable *decision*: the same input/output contract and the same objective,
needed by at least two missions independently — reused by at least two
missions, a clear input/output contract, objectively evaluable on its own, a
toy-to-production mapping, and running on an existing compute lane, per
[the admission gate](../reference/standards/mission-contract.md#the-capability-admission-gate).
Fail any one of those and the explanation stays local to the mission that
needed it first, because reuse of a noun is not reuse of a decision — a rank
in a recommendation slate and a rank in a trading portfolio share a word, not
a contract.

That is why this section currently holds exactly one entry, not because
nothing else is reusable-looking. `platform/adaptation` and `platform/data`
each name techniques several missions could plausibly use, and stay platform
reference precisely because no second mission has yet needed the same
contract for the same reason — an empty promotion is a promise this repo
would rather not owe.

## [Act and coordinate](act-coordinate/)

The agent-loop contract — tools, permissions, stop conditions — that
[the language-model system's agent harness](../missions/01-language-model-agent/06-agent/)
and [personalized discovery's rule engine](../missions/02-personalized-discovery/07-rule-engine/)
both need with the same inputs and the same objective: decide what a proposed
action is validated, permitted, and observed against, without trusting the
model to enforce its own boundary. [The code-agent mission](../missions/04-code-agent/)
is this capability's third consumer, unmodified except for the tools its task
set requires — which is the strongest evidence yet that the contract, not
just the code, generalizes.

## Before this, and where this returns to

**Before this:** [serving](../platform/serving/) — a model that cannot be
called cannot act, and this is the software layer around the call. **Next:**
[evaluation and observability](../platform/evaluation-observability/), which
has to judge the harness this section describes, not only the model inside
it — and [safety and governance](../platform/safety-governance/), which turns
this section's permission contract into an enforced guardrail.
