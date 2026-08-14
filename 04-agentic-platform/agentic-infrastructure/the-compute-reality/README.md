---
status: draft
level: reference
label: The compute reality
---

# What a 24GB card can and cannot run

> Dated survey, 2026-08-14. The repository's compute-lane guides in
> `reference/` document the actual machines; this chapter is the boundary
> statement.

**Question:** every claim in this topic must respect the hardware it runs
on. What can the local lane actually execute, and when is the honest move
an external source instead of a reduced local run?

## The lane

The local lane is a 24GB card (documented in `reference/local-4090.md`).
It can run: the mission's harness demos (scripted backends), small-model
mechanism demos, and the a-sqlite-memory / sandbox / judge runs — all
recorded in this topic. It cannot run: 90,000-table migrations, frontier
model evaluations at scale, or production TensorRT deployments.

## The rule

The repository rule is the boundary statement: if a model does not fit the
hardware, do not train a reduced model and present it as evidence — link
dated external sources instead. Every survey chapter in this topic follows
that rule: the numbers are attributed, and no local run claims a frontier
result.

## Why this chapter exists

The agentic-infrastructure stage is about reading the industry's machine
room; this chapter keeps that reading honest by naming the machine this
repository can actually stand on. The real-tasks stage's capstone runs on
it; the industry cases (OpenAI's migration, TRT deployments) are surveys
precisely because they do not.

## What this does not say

It does not claim the lane's limits are fixed — hardware upgrades change
them. It states the current boundary so every number in the topic carries
its provenance.
