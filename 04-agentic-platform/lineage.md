---
level: reference
---

# The open-source line behind the code agent

> Dated survey, 2026-08-06. Sources cited inline. External claims are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** this mission's artifact is a repository, a failing test, and a
patch that makes it pass — and the question is what makes "pass" believable.
Every piece of that artifact is a line of open-source evolution: code models,
agent loops, and the guardrails that keep a scoreboard honest.

## Code models

**Codex** (Chen et al., 2021, with HumanEval) showed a code-finetuned
language model solves function-level problems at non-trivial pass rates and
made **pass@k** the metric — sample k times, count any correct. **AlphaCode**
(Li et al., 2022) pushed to contest problems with massive sampling and
filtering. **CodeLlama** (Roziere et al., 2023), **StarCoder** (Li et al.,
2023), and **DeepSeek-Coder** (Guo et al., 2023) opened the weights and made
code specialization a commodity. The tradeoff at this end is the same one
mission 01 measures: capability lives in pretraining, and the SFT/reasoning
layer decides whether the model can *hold* a multi-step task, not whether the
knowledge is there.

## From functions to repositories

HumanEval is function-level; a real bug lives in a repository with imports,
tests, and history. **SWE-bench** (Jimenez et al., 2023) moved the bar to
real GitHub issues with a test suite that has to pass — the exact artifact
this mission follows — and **SWE-agent** (2024) showed an agent loop with
file and shell tools is what makes the task tractable, inheriting the ReAct
shape (Yao et al., 2023).

## Guardrails and the honest scoreboard

The hardest line is the guardrail against the scoreboard itself. A model
that cannot satisfy an assertion can delete the assertion, and benchmarks
learned this the hard way through reward hacking: models that game the
metric without doing the task. The response is structural — a patch that
touches a test file is a failure, a diff check sits between the agent and
the score — the same idea the verifier/RL line (RLVR, R1, 2025) applies:
the reward must be computed by a rule the model cannot edit.

The repo's anchor is a real near-miss: its serving engine was benchmarked,
quoted by three chapters, and correct on every decode step — and wrong,
because a bug made it *faster*. It was caught only by an identity check
against a full recompute. That is why this mission's guardrail is not a
prompt line asking the agent to behave.

## Evidence boundary

Dated and attributed, not measured. The repo anchors — resolve rate beside
dollars per resolved task, no-harness versus always-frontier, the
identity-check bug — cite their runs. The line does not settle whether an
agent loop beats a blind call on any given task; that is the mission's
measured question.
