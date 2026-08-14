---
status: draft
level: frontier
label: Industry impact
---

# The platform works in this repo. Does it work in your industry?

**Question:** this topic built an agentic platform and measured it. The
question this stage asks is outward: which industries can actually stand an
autonomous agent — and which cannot? The evidence splits by three
variables: how measurable the outcome is, how expensive a wrong action is,
and whether the industry already operates under audit requirements.
Regulated sectors (finance, healthcare, government) are paradoxically the
leaders, because they already have the traceability infrastructure
trustworthy agents need.

**The artifact this stage follows** is the adoption matrix: industries
mapped by outcome measurability and failure cost, with real deployments on
each cell — customer service (Klarna's replacement agent), legal (A&O
Shearman + Harvey), finance (Ramp's audit-hours agent), healthcare
administration, retail supply chains.

By the end you will be able to take any industry claim about agentic AI and
say which variable — measurability, failure cost, audit readiness — decides
whether it is real, and which part of this topic's platform maps to it.

**Before this:** stages 00–15 built and governed the platform. This stage
takes the whole machine and asks where it lands; [stage 17](../real-tasks/)
then runs it on the hardest local tasks.

## What this stage decides

Whether to adopt agentic capability in a given domain, and at what autonomy
level — the industry-level version of the authorization matrix in
[stage 15](../autonomy-and-orchestration/).

## Planned chapters

- **the-adoption-matrix** — outcome measurability, failure cost, and audit
  readiness as the three variables; which industries score high on each,
  and why regulated sectors lead on trust infrastructure.
- **software-itself** — the industry the platform came from: AI-assisted
  commits at ~25% of all commits, the GitClear maintainability deficit
  (duplication up ~81%, reuse down ~70%, legacy refactoring down ~74%,
  error masking up ~47%), DORA's instability findings, and how the
  authorization matrix is the direct response.
- **finance-and-regulated** — banking, insurance, payments: agent
  registries and lineage as regulatory exposure (MAS-style oversight),
  Ramp's finance agent, Bank of America's Erica at 90% employee adoption;
  why audit infrastructure is the unlock.
- **healthcare-and-legal** — clinical documentation agents, ABA claim
  denials held below 2%, A&O Shearman's agentic multi-step legal workflows;
  the human-signoff boundary in each.
- **retail-and-operations** — inventory, supply chain, customer service;
  where the outcome is measurable enough for auto-merge-style autonomy, and
  where it is not.
- **where-agents-cannot-go-yet** — the honest cells: domains with
  unmeasurable outcomes, catastrophic failure cost, or no audit trail; what
  has to change for them to enter the matrix.

## Evidence strategy

Every claim in this stage is a dated survey with an inline source; none is
measured here. Industry numbers (GitClear's 623M-change analysis, DORA,
deployment case studies) are attributed to their reports.

## Industrial grounding

GitClear and GitKraken analyzed 623M real-world code changes (2023–2026):
AI-assisted commits are ~25% of all commits, duplication is up ~81%, reuse
down ~70%, legacy refactoring down ~74%, error masking up ~47%. DORA links
AI usage to downstream instability. On the adoption side, regulated sectors
lead because they already require the traceability trustworthy agents need;
deployments exist in customer service (Klarna), legal (A&O Shearman +
Harvey), finance (Ramp, Bank of America), and healthcare administration.
