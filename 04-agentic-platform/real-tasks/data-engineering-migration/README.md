---
status: draft
level: reference
label: Data engineering migration
---

# 90,000 tables, 600PB, a 100,000-node DAG: the agent-shaped migration

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the stage's claim is that data engineering is agent-shaped
because its work is measurable and decomposable. The industry proof points
are the dataset migrations. What made them work, and what stayed human?

## OpenAI's cross-cloud migration

OpenAI migrated 90,000 tables and ~600PB across clouds in roughly two
months, with dependency graphs on the order of 100,000 nodes — the hard
problem was ordering, because during cutover some tables live on the old
cloud while downstream consumers are on the new one
([ZenML case summary](https://www.zenml.io/llmops-database/building-a-production-data-agent-for-90000-tables-at-scale);
[ByteByteGo](https://blog.bytebytego.com/p/how-openai-built-its-data-agent)).
Codex did much of the hundreds of thousands of small code changes that
pointed workloads at the new cloud.

## Spotify's Honk

Honk automated migrating ~1,800 downstream dataset pipelines across three
pipeline frameworks in six months, generating 240 automated PRs and
saving an estimated 10 engineering weeks, with an LLM-as-judge
verification loop ([Spotify Engineering](https://www.engineering.atspotify.com/2026/4/background-coding-agents-dataset-migrations-honk-part-4)).

## What made them agent-shaped

Both were: outcome-measurable (does the pipeline still produce the same
data), decomposable (one pipeline at a time), and verifiable (tests
decide). The orchestration skeleton from stage 11 — deterministic ordering,
per-pipeline workers, verification gates — is exactly the shape both used.

## What stayed human

Migration order (the DAG), the cutover window, and the judgment calls on
downstream breakage. The human designed the skeleton; the agents filled
the cells.

## What this does not say

It does not claim the mission's local lane can reproduce these — they are
dated external results cited inline, the boundary the whole repository
enforces. It maps the shape that makes data engineering agent-shaped.
