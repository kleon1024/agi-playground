# AGENTS.md

Working notes for AI agents and human contributors. Read this before editing.

## What this repo is

Build AI systems from infrastructure to measurable outcomes. Five layers:
business goal → mission → capabilities → platform → infrastructure. A
capability proves a hammer works; a mission proves a problem got solved.

## Layout

```
foundations/   mathematics and mechanism, bound to no product
platform/      data, training, adaptation, serving, evaluation, safety
capabilities/  composable hammers — admitted only when two missions need them
missions/      infrastructure through to business outcome
infra/         compute lanes (local GPU via Tailscale/WSL2, and Modal)
research/      the landscape evidence behind every technical choice
standards/     the contracts everything else must satisfy — read these first
```

## The two invariants

**Every capability claim is backed by a run.**
**Every mission is backed by a measurable outcome.**

Every lesson is `README.md` + `core/` + `prod/` + `runs/`. `core/` is
from-scratch and dependency-light; `prod/` does the same job with the real
tool; `runs/` records the exact command, hardware, wall-clock, cost, and
metrics. A lesson without a `runs/` entry stays `status: draft` in its
frontmatter and shows as draft in the README tables.

Missions additionally need a `mission.yaml` written **before** building —
declaring stakeholder, job, decision, baseline, primary metric, guardrails,
budgets, and acceptance. Business outcomes cannot be executed, so they are
proven against declared reproducible proxies, and every mission must state what
it does *not* prove. Full rules in [`standards/`](standards/).

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
- **Human-readable tutorials have one causal spine.** Open with the concrete
  question the learner will answer and the prerequisite they need. Move through
  one running example in this order: problem, mental model, mechanism,
  manipulation, observed consequence, evidence boundary, and next question.
  Each section must consume an output or resolve a question from the preceding
  section. Define jargon at first use, prefer plain sentences and concrete
  nouns, and keep one main idea per paragraph. Headings name learner decisions
  or questions; they do not merely label implementation modules.
- **Progressive disclosure protects the narrative.** Put the minimum explanation
  required to reason about the example in the main path. Move derivations,
  production alternatives, and implementation detail after the learner has the
  mental model they depend on. Split a chapter only when the learner is making
  a different decision, not to satisfy an arbitrary length target.
- **Components are teaching instruments.** Introduce an interactive only after
  its variable, outcome, and prediction are clear in prose. It must let the
  learner change one causal variable, make the consequence legible without
  guessing, and return that consequence to the next paragraph. Decorative
  dashboards, unexplained controls, autoplay-only demonstrations, and
  components that duplicate prose are defects. Every component needs a useful
  static reading order and keyboard-accessible controls.
- **One teaching surface.** Interactive explanations use the shared
  `learning-widget` contract in `site/src/css/widgets.css`; component-local
  colors, type scales, button systems, and mobile breakpoints are defects.
  Explanatory text and controls are at least 15px, semantic metadata is at least
  13px, and every widget must fit a 390px viewport without page overflow.
- **Motion explains state.** Animate causal transitions such as scheduling,
  allocation, accumulation, and verification; do not add decorative motion.
  Every animation has manual control when timing matters and respects reduced
  motion.
- **Interaction follows the lesson.** Frame one question, explain the minimum
  mechanism, let the learner change one causal variable, state the observed
  consequence, then hand that consequence to the next section. One interactive
  owns one cognitive task; if its controls cannot confirm or falsify a mental
  model, keep the explanation as prose.
- **Diagrams are navigable explanations.** System flows use the shared
  `ProcessDiagram` grammar: clickable stages, explicit ownership and handoff,
  vertical mobile adaptation, and no horizontal-scroll dependency. Do not add
  new Mermaid diagrams.
- **The landing page routes, chapters teach.** Mechanism-specific demos live in
  the chapter that establishes their prerequisites and consumes their output.
  The landing page only explains the curriculum model and sends the learner to
  a coherent starting path.
- **A lesson is a complete decision path, not a stub.** State the mechanism,
  why it exists, its failure boundary, the executable path, and what the
  evidence does not prove. Split a lesson only when two chapters have distinct
  learning outcomes; do not split or pad to hit a line count.
- **No emoji.** Do not use emoji in published prose, navigation, status labels,
  controls, code examples, commit messages, or project instructions. Use words,
  semantic HTML, and the shared icon system when an icon is necessary. The
  repository test suite enforces this across authored text and source files.
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
