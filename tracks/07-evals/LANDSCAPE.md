---
status: draft
---

# 07 — Evals: Landscape

Source: `research/synthesis.md` anchor table, "Evals" row, and the "Harness
disclosure matters" note under key 2025-2026 shifts.

| Toy (teach-from) | Production | Our take |
|---|---|---|
| lm-eval-harness, inspect-ai | inspect_evals (including AgentThreatBench), SWE-bench Pro, Terminal-Bench 2.0, τ²-bench, GAIA | As with the annotation row in `02-data`, there's no sharp toy/production split here — lm-eval-harness and inspect-ai are themselves the production-grade evaluation frameworks, taught at small scale (a handful of tasks, one model) rather than reimplemented. The named benchmark suites (inspect_evals, SWE-bench Pro, Terminal-Bench 2.0, τ²-bench, GAIA) are what you point the frameworks at once you move past toy tasks. |

**Our take on harness disclosure:** "Stop Comparing LLM Agents Without
Disclosing the Harness" is the framing this track (and `08-agents`) takes
seriously — an agent eval score without the harness's tool set, loop
structure, and context-management strategy disclosed alongside it is not a
comparable number. `03-harness-disclosed-agent-evals` makes this explicit
rather than treating it as a caveat.

**Single-vendor-rot note:** five independent benchmark suites are named
alongside the two frameworks, spanning different labs and evaluation
philosophies (software-engineering tasks, terminal tasks, tool-use dialogue,
general assistant tasks).
