---
status: draft
level: reference
label: The adoption matrix
---

# Three variables decide whether an industry can stand an agent

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** which industries can actually adopt autonomous agents? The
evidence splits on three variables: how measurable the outcome is, how
expensive a wrong action is, and whether the industry already operates
under audit requirements.

## The three variables

**Outcome measurability** — can "done" be verified? Software has tests;
legal drafts and clinical documentation have review; creative work has
neither. Measurability decides where auto-merge-style autonomy is even
possible.

**Failure cost** — what does a wrong action cost? A dependency bump gone
wrong costs a CI run; an auth change gone wrong costs an incident; a
medical recommendation gone wrong costs differently. Cost decides the
approval gate's position on the authorization matrix.

**Audit readiness** — does the industry already require traceability?
Finance, healthcare, and government do — which is why they lead adoption:
regulation is the blueprint for trustworthy agents
([regulated-sectors analysis](https://itbrief.co.uk/story/regulated-sectors-legal-teams-tipped-to-lead-ai-2026)).

## The matrix

| Variable | High | Low |
|---|---|---|
| Outcome measurability | software, customer service | creative, strategy |
| Failure cost | auth, payments, medical | docs, formatting |
| Audit readiness | finance, healthcare, government | startups, internal tools |

The cells with high measurability, high audit readiness, and manageable
failure cost are where production agents live in 2026.

## What this does not say

It does not claim the matrix is static — measurability improves as
verification tooling improves. It maps the variables that decide whether
an industry claim about agentic AI is real.
