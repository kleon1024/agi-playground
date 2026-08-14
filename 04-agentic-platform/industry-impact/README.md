---
status: draft
level: frontier
base: none
label: Industry impact
---

# The platform works in this repo. Does it work in your industry?

**Question:** this topic built an agentic platform and measured it on a
task set with known answers. The outward question is the hard one: which
industries can actually stand an autonomous agent, and which cannot? The
evidence splits on three variables — how measurable the outcome is, how
expensive a wrong action is, and whether the industry already operates
under audit requirements. Regulated sectors are paradoxically the leaders,
because they already have the traceability infrastructure trustworthy
agents need. Why does that paradox hold, and where does it break?

**The artifact this stage follows** is the adoption matrix
([the-adoption-matrix](the-adoption-matrix/)): industries mapped by
outcome measurability and failure cost, with real deployments on each cell.
Every deployment cited below is a dated source, not a number measured here.

**Before this:** stages 00–15 built and governed the platform. This stage
asks where the whole machine lands.

## The software industry already has the measurement

Start with the industry this platform came from, because it is the one
with the most data. GitClear and GitKraken analyzed 623M real-world code
changes (2023–2026) and the picture is blunt
([software-itself](software-itself/)): AI-assisted commits are ~25% of all
commits, duplication is up ~81%, reuse is down ~70%, legacy refactoring is
down ~74%, and error masking is up ~47%. DORA's research adds the
instability correlation — each 25% of AI usage adds roughly 7%
instability.

Read those numbers with this topic's vocabulary: software has
highly measurable outcomes (a test suite, a diff, a deploy), so agents
were admitted at high autonomy — and the *consequences* are exactly what
[stage 15's authorization matrix](../autonomy-and-orchestration/) exists
to bound. Duplication and error masking are escaped defects; the matrix's
tuning signal is the same thing at task scale. Software is not the story
of agents working; it is the story of what happens when measurability lets
autonomy run ahead of the control setup, and of the control setup
catching up.

## The three variables

Whether an industry can stand an agent is decided by three variables, and
they predict the adoption map
([the-adoption-matrix](the-adoption-matrix/)):

| Variable | High-scoring industries | Why it decides adoption |
|---|---|---|
| Outcome measurability | software, customer service, admin | the agent can be scored — this topic's whole premise |
| Failure cost | finance, healthcare, government | a wrong action is expensive, so the gate is worth building |
| Audit readiness | finance, healthcare, government | traceability exists, so the agent's actions can be reviewed |

The third variable is the paradox. Regulated sectors score *worst* on
freedom to act but *best* on readiness to be governed — and governance is
what autonomous agents actually need. Finance already keeps registries and
lineage for regulatory reasons; an agent registry is the same discipline
applied to a new actor ([finance-and-regulated](finance-and-regulated/)).
That is why the first production agents landed in the most-regulated
places, not the least.

## What a real deployment looks like on each cell

The cells are not hypothetical
([finance-and-regulated](finance-and-regulated/),
[healthcare-and-legal](healthcare-and-legal/),
[retail-and-operations](retail-and-operations/)):

| Industry | Deployment | What the gate is |
|---|---|---|
| Customer service | Klarna's replacement agent | outcome measurable — resolution, handle time |
| Legal | A&O Shearman + Harvey multi-step workflows | human signoff on each step |
| Finance | Ramp's audit-hours agent; Bank of America's Erica at ~90% employee adoption | audit trail as the product |
| Healthcare admin | clinical documentation agents; ABA claim denials held below 2% | human signoff on clinical content |

Read the gate column: every deployment that survived did not remove the
human — it moved the human to the boundary the industry already had.
Legal signs off per step because legal already signs off per document.
Healthcare signs off on clinical content because that boundary predates
the agent. The agent inherited an existing trust infrastructure.

## The cells that are empty, honestly

The matrix has empty cells ([where-agents-cannot-go-yet](where-agents-cannot-go-yet/)):
domains where the outcome is unmeasurable (so the agent cannot be scored),
where a wrong action is catastrophic with no rollback (so even a good
gate is too late), or where no audit trail exists (so governance is
invented from scratch alongside the agent). These are not "no AI" cells;
they are "no agent" cells — assistive tools still work, because an
assistive tool does not need the three variables to hold, it just needs a
human in front of it.

## What this stage does and does not establish

It establishes the decision rule: the three variables predict adoption,
and the paradox — regulated sectors lead because governance is the
precondition — explains why the first agents landed where they did. All
figures are dated surveys with sources cited; none is measured here.

It does not claim the deployments prove the platform this topic built; it
claims they show which variable each industry's adoption turns on. And it
does not claim the empty cells stay empty — the point of naming the three
variables is that an industry moves into the matrix when one of them
changes, which is a prediction, not a prophecy.

**Next:** the matrix says where agents land. The last stage runs this
topic's own platform on the hardest local work — [real tasks](../real-tasks/).
