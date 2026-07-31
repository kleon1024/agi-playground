# Design — Bring missions 04-09 to interactive-widget parity with 01-03

## Context

The user asked for a large, repo-wide tutorial-deepening pass: "从基础到进阶
到前沿，从模型结构，数学理论，可视化都要涉及，有数据支撑，大量可视化，动画，
图表，可交互组件" (basics through frontier, covering architecture, math
theory, and visualization, backed by real data, with extensive
visualization/animation/charts/interactive components). Two scoping answers
pinned this down: scope is the whole repository (foundations, missions 01-09,
platform, capabilities), and priority is to run this in parallel with the
still-open mission 08/09 build work, not sequenced after it.

This is too large for one spec, so it is split into four sequential
sub-projects. **This spec covers only the first: missions 04-09.** The
others (foundations, platform, a 01-03/capabilities review pass) are named as
backlog below, each to get its own spec when its turn comes.

### Why 04-09 first (confirmed with the user over 01-03/foundations)

A repo-wide audit of `site/sync-docs.py`'s `<!-- interactive: Name -->`
convention (the mechanism that turns a README into a live component on the
site) shows the gap precisely:

| Section | Chapters with a widget | Chapters without |
|---|---|---|
| foundations | 1 | 1 |
| capabilities | 2 | 1 |
| platform | 12 | 9 |
| missions 01-03 | 21 | 0 |
| **missions 04-09** | **0** | **18*** |

*18 = the chapters that exist today (mission 09 has no stages built yet, so
it is out of scope for this pass — its stages get the same treatment once
Track A builds them). Missions 01-03 already have 40 components between them
and were built with the site's full teaching-instrument toolkit from the
start; missions 04-09 were built stage-by-stage this session with real code
and real runs, but zero interactive teaching surface and no worked math. That
is almost certainly what "现在太简单了" is pointing at, so it is the most
visible gap and goes first.

## What "deepen a chapter" means here (the method, applied uniformly)

For each of the 18 target chapters (README-level entries below), in order:

1. **Read the existing causal spine.** Identify where the chapter currently
   *asserts* a mechanism (a formula, an architectural choice, a training
   dynamic) rather than showing the reader how to derive or verify it.
2. **Add one worked math/architecture explanation** at that point, using the
   chapter's own real numbers from its `runs/` artifact wherever a concrete
   example is needed — never an invented number. Examples already identified
   by name below (e.g., mission 08's VQ nearest-neighbor argmin and why a
   saturating decoder activation kills its gradient; mission 06's GRPO
   advantage normalization; mission 04's agent-loop stopping-condition
   logic).
3. **Add one interactive component**, built on the shared `learning-widget`
   CSS contract (`site/src/css/widgets.css`) and, if it is a process/flow
   diagram, the shared `ProcessDiagram` grammar (no new Mermaid). One causal
   variable, a prediction the reader can confirm or falsify by moving it, a
   static-readable fallback, controls ≥44px, fits a 390px viewport. Reuse an
   existing component from `site/src/components/` (40 already exist) if one
   already models the right variable — do not build a near-duplicate.
4. **Add one dated historical-evolution note** where a real, citable prior
   technique or published result clarifies why the chapter's mechanism looks
   the way it does (e.g., VQ-VAE lineage for mission 08, GRPO's origin for
   mission 06, codec lineage for mission 07). Labeled explicitly as external
   and dated; never placed beside this repo's own measured number in a way
   that implies they were run the same way.
5. **Word budget**: this is an addition to an already-complete causal spine,
   not a rewrite. Each chapter should grow by roughly 200-500 words plus one
   widget — if a chapter would need more than that to make the addition make
   sense, that is a signal the chapter's existing spine has a gap this pass
   should also close, not a license to pad.

Chapters are **not** rewritten wholesale. The existing problem → mental model
→ mechanism → manipulation → consequence → evidence-boundary spine stays;
this pass inserts depth at the one or two points in each chapter where the
mechanism was previously just stated.

## Target chapters (sub-project 1 scope, 18 chapters across 5 missions)

| Mission | Chapters | Where the math/widget gap is sharpest |
|---|---|---|
| 04 — code agent | README, 00-task-set, 02-agent-loop, 03-cheap-or-expensive | agent-loop stopping condition and cost/quality tradeoff curve |
| 05 — vision-language | README, 00-image-caption-task, 01-vision-fusion, 02-report | patch-embed math, cross-attention fusion mechanism |
| 06 — game AI | README, 00-gridworld-baselines, 01-grpo, 02-report | GRPO advantage normalization, reward variance across seeds |
| 07 — realtime voice | README, 00-audio-codec, 01-streaming-decode, 02-report | VQ codec math (shared lineage with 08), KV-cache streaming latency |
| 08 — video generation | README, 00-synthetic-video-dataset, 01-video-tokenizer, 02-generation-model | VQ codebook collapse mechanics (three real failure modes already documented in prose — this is the strongest candidate for a genuinely new interactive component: let the reader manipulate decoder-activation boundedness and watch gradient flow to a codebook vector) |

Mission 09 is excluded — no stages exist yet. Its README will get the same
treatment once Track A builds its stages; that is a follow-up, not part of
this spec.

## Sequencing within this sub-project

By mission, oldest-built first (04 → 05 → 06 → 07 → 08), one fork per
mission (4 README-scope chapters each, self-contained, no shared output
file), matching the parallel-fork pattern already used this session for the
five new mission contracts. Each fork:

- Proposes the specific widget (new or reused) and math insertion per
  chapter before writing, so a mismatched or decorative widget is caught
  before code is written, not after.
- Runs `uv run ruff check .` / `uv run pytest -q`, then
  `cd site && npm run sync && npm run typecheck && npm run build` with no
  broken-link/anchor warnings, before its commit.
- Commits per-mission (5 commits total for this sub-project), not per-file,
  matching this session's commit granularity elsewhere.

## What this sub-project does not attempt

- No rewrite of chapters' existing narrative arc — only depth insertion.
- No new Mermaid diagrams (forbidden by AGENTS.md) — new diagrams use
  `ProcessDiagram`.
- No touching foundations, platform, capabilities, or missions 01-03/09 —
  those are separate, later sub-projects:
  1. **Foundations** (2 chapters) — highest leverage, so missions can link
     instead of re-deriving math locally.
  2. **Platform** (9 zero-widget chapters, plus a review of whether the 12
     existing widgets are load-bearing or decorative).
  3. **Missions 01-03 + capabilities review** — already mature; lightest
     touch, only where a real gap remains after 04-09/foundations/platform
     are done.
- No new numbers. Every math example uses a chapter's existing `runs/`
  artifact; nothing here re-opens a mission's acceptance verdict.

## Testing / acceptance

Same gates as every other change in this repo: `ruff`, `pytest`, then the
site sync/typecheck/build with zero broken-link/anchor warnings. Additionally,
per AGENTS.md's own tutorial-acceptance rule: for each changed chapter, check
the actual generated route, the widget's manual-control state change, and the
page at 390px with no horizontal overflow before considering that chapter
done — not just a successful build.
