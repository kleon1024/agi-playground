---
status: draft
---

# Speedrun 05 — Serve

## Goal

Serve the RL'd model with a minimal inference engine you built and understand
line-by-line, rather than a black-box production server.

## Deliverable

A minimal engine implementing KV cache → paged blocks → continuous batching,
benchmarked against naive `generate()` on throughput and latency.

## Anchor project

nano-vLLM (see `platform/serving/LANDSCAPE.md` for the toy/production
mapping). Seed lessons: `platform/serving/README.md`, `01-kv-cache`
through `03-continuous-batching`.

## Verification criterion

No verified run yet — depends on `04-rl` landing first. When built, its
`runs/` entry must show: the exact serving benchmark command, hardware, the
naive-`generate()` baseline numbers alongside the paged/batched engine's
numbers (throughput and latency), and the model checkpoint served.
