# AGENTS.md

Working notes for AI agents and human contributors. Read this before editing.

## What this repo is

A curriculum you learn by building: data → pretraining → post-training → RL →
inference → evals → agent harnesses. Every topic pairs a readable from-scratch
implementation with the production tool it mirrors, and nothing claims a result
it has not actually produced.

## Layout

```
speedrun/     the flagship pipeline, stages 00-07 — the repo's integration test
tracks/       01-08, the systematic curriculum; each holds lessons
infra/        compute lanes (local GPU via Tailscale/WSL2, and Modal)
research/     the landscape research the curriculum's scope is argued from
```

## The one invariant

**A published number must be traceable to a `runs/` entry.**

Every lesson is `README.md` + `core/` + `prod/` + `runs/`. `core/` is
from-scratch and dependency-light; `prod/` does the same job with the real
tool; `runs/` records the exact command, hardware, wall-clock, cost, and
metrics. A lesson without a `runs/` entry stays `status: draft` in its
frontmatter and shows as draft in the README tables.

If you cannot run it, do not write the number. Estimates, plausible figures,
and "typical" results are all failures here. External published results are
fine when attributed and dated.

## Before you commit

```bash
uv run ruff check .    # must pass
uv run pytest -q       # must pass
```

Tests are CPU-only structural checks. GPU work is verified by hand and recorded
in `runs/` — never in CI.

## Conventions

- **English** for all published content.
- **Hardware-neutral in curriculum prose.** Write "a 24GB card" or "the local
  lane", not a specific GPU model. Naming real hardware is for `infra/` docs and
  `runs/` records, which describe machines that actually ran something.
- **Name at least two production alternatives** in `LANDSCAPE.md` tables. Single
  tools get acquired and archived; the curriculum should survive that.
- **Commits**: `<type>(<scope>): <subject>`, imperative, ≤72 chars, no emoji.
  Types: `feat|fix|docs|refactor|perf|test|chore|build|ci|style`.
- **Files ≤800 lines.** `core/` files should be far shorter — they are read.

## Running GPU work

Local lane and Modal lane are both documented in [`infra/`](infra/), including
a verified setup path and the failure modes worth knowing in advance. Modal
lessons print their dollar cost into `runs/`.

## What not to do

- Do not report a run you did not execute, or round a measured number toward a
  nicer one. If a model comes out at 88M, the docs say 88M.
- Do not vendor external projects. Link them, and explain when to reach for
  which.
- Do not let a `core/` implementation quietly depend on the framework its
  `prod/` counterpart uses. The point is that it does not.
