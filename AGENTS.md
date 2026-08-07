# AGENTS.md

Working notes for AI agents and human contributors. Read this before editing.

## What this repo is

Build AI systems from infrastructure to measurable outcomes. **Topics are the
only curriculum spine.** A learner starts with a stakeholder problem and stays
on that topic until it links to a mechanism or engineering reference needed
for the next decision. Foundations are a support library, not a parallel track
and not a prerequisite to read front to back.

A topic proves a problem got solved; a support chapter proves a mechanism
behaves the way the topic assumed.

## Layout

Nine topics, then two support libraries, and each boundary fits in one
sentence. There is no `missions/` level: the topics were pulled up one level
so the directory is the reader-facing domain, and the old `infra/` tree was
absorbed into the topic that uses the mechanism.

```
01-language-model/          raw text → tokenizer → pretrain → adapt → serve → act; vision lives under it
02-personalized-discovery/  recommendation, search, and ads as one decision loop (shared/ + per-surface)
03-quantitative-research/   point-in-time data → signal → portfolio → validation → capacity
04-agentic-platform/        the agent harness, its failure modes, and what a correct patch costs
05-game-ai/ 07-multimodal-generation/ 08-bio-pharma-modeling/ 09-autonomous-driving/
                            the remaining decision loops, each with its own artifact chain;
                            07 is voice and video under one topic (codec and video-token
                            mechanisms plus the codebook failures both surfaces share)
foundations/                mechanism that holds regardless of which topic you run
reference/                  contracts, governance, compute-lane guides, and dated survey material
```

There is no `platform/` and no `capabilities/`. Both existed and both were a
second telling of topic 01 over the same lifecycle — sixteen of seventeen
platform chapters served exactly one topic, nine interactives appeared on both
a topic stage and a platform twin, and roughly 2,100 lines of branch prose
owned no `core/`, `prod/`, or `runs/`. The `missions/` level repeated that
lesson at one remove, so it was deleted too. Cross-cutting views are an
**index**, not a directory: `site/topics.mdx` lists every chapter under the
decision it serves.

## Curriculum ownership

The landing page, Start here page, and sidebar route readers to Topics before
support libraries. A topic introduces one concrete artifact and links to a
foundation chapter, another topic's stage, or a reference guide only at the
point where that chapter is required. The linked chapter must return an
artifact, decision, or diagnostic that the next topic stage consumes.

- **Topic owns the outcome and the evidence for it.** It owns the
  stakeholder, job, decision, baseline, concrete artifact chain, integration
  handoffs, budgets, proxy, result, and evidence boundary. A deep-dive belongs
  to the stage whose decision it changes, even when other topics cite it.
- **Foundation owns mechanism that survives the topic.** Test: could this
  chapter be written without naming a topic's artifact? If not, it is a topic
  deep-dive and belongs beside the run. Scope the name honestly:
  attention, decoders, and a first language-model training loop are
  language-model foundations, not universal AGI prerequisites.
  `level: foundation` may appear only inside `foundations/`.
- **A shared chapter stays where it was built.** When a second topic needs the
  same input/output contract and objective, it links to the chapter in the
  topic that built and measured it. Moving an explanation away from the run
  that backs it is how a chapter ends up making a claim with no evidence beside
  it. The admission bar survives as a promotion criterion in
  `reference/standards/mission-contract.md`, and reuse of a noun or technique
  still does not clear it.
- **A machine chapter owns the machine underneath**, and names the stage or
  foundation it is the substrate for. Networking, storage, orchestration, and
  GPU-cluster concepts live under `foundations/04-distributed-training/`;
  observability and dedup live beside the serving and corpus stages that need
  them. Compute-lane guides live in `reference/`.
- **Reference owns contracts, governance, and dated survey material.** It is
  the only place a page may have no run and not be a defect.

A widget belongs to one page. After a fold, no `<!-- interactive: X -->` marker
may appear in two chapter READMEs; a test enforces it.

Use the central-question test when content overlaps. If a chapter's central
question, inputs, outputs, and acceptance are the same wherever it is read,
move the reusable explanation to Foundations and keep only the
topic-specific choice, handoff, and evidence in the Topic. Do not duplicate the
same tutorial in two places.

Do not call any support-chapter sequence the global curriculum spine. Such
ordering may organize a scoped reference collection, but it must not determine
the homepage, sidebar, prerequisites, or learner path. The language-model
topic is labeled **Language-model system** in reader-facing navigation; an
agent is one stage of that system, not the scope of the playground.

## The two invariants

**Every capability claim is backed by a run.**
**Every topic is backed by a measurable outcome.**

Every lesson is `README.md` + `core/` + `prod/` + `runs/`. `core/` is
from-scratch and dependency-light; `prod/` does the same job with the real
tool; `runs/` records the exact command, hardware, wall-clock, cost, and
metrics. A lesson without a `runs/` entry stays `status: draft` in its
frontmatter and shows as draft in the README tables.

Topics additionally need a `mission.yaml` written **before** building —
declaring stakeholder, job, decision, baseline, primary metric, guardrails,
budgets, and acceptance. (The contract file keeps the `mission-` name; the
directory does not.) Business outcomes cannot be executed, so they are proven
against declared reproducible proxies, and every topic must state what it does
*not* prove. Full rules in [`reference/standards/`](reference/standards/).

If you cannot run it, do not write the number. Estimates, plausible figures,
and "typical" results are all failures here. External published results are
fine when attributed and dated.

Runs must earn credibility from scale, not from merely existing. A dataset too small
to support the claim (a hand-written toy set, a few dozen examples, a shrunk
model) is the same failure as a fabricated number. Use the largest public
dataset that fits the lesson, and record sample size, model size, and hardware
in `runs/`. If the model does not fit on the hardware we can actually run (the
local lane's card, e.g. a 24GB 4090), do not train a reduced model and present
it as evidence: link dated external sources instead (papers, official model
cards, public leaderboards, vendor benchmarks) and let the chapter's claims
rest on those. A local run that is unavoidably small is allowed only as a
mechanism demo and must say so in the chapter, never as the primary evidence.

## Before you commit

```bash
uv run ruff check .    # must pass
uv run pytest -q       # must pass
```

Tests are CPU-only structural checks. GPU work is verified by hand and recorded
in `runs/` — never in CI.

For any tutorial, navigation, component, or site change, also run:

```bash
cd site
npm run sync
npm run typecheck
npm run build
```

The site build must complete without broken-link or broken-anchor warnings.

## Pushing to main

This repo is solo-owned with no PR-review gate on `main`, and Vercel's git
integration deploys straight from a push to `main` — there is no separate
merge step to gate. The moment a commit or batch of commits lands on local
`main` and the gates above pass, push to `origin/main` in that same turn —
proactively, without waiting for the user to say "push" or "deploy" first,
and without asking for confirmation. This holds across multiple rounds of
work landing in one session: push after each batch settles, not only once,
at the end, when asked.

## Conventions

- **English** for all published content.
- **A tutorial update must change the tutorial.** New components, CSS, diagrams,
  navigation, or build plumbing do not count as a tutorial rewrite. Before and
  after acceptance must compare the learner-visible outline, opening question,
  running example, causal transitions, and evidence boundary. If the prose and
  reading order are materially unchanged, report the work as a UI or component
  update, not as a tutorial update.
- **The first viewport establishes the learning contract.** It must show the
  central question, the concrete artifact or example the chapter follows, and
  what the learner will be able to decide or explain. Do not open with repository
  history, survey commentary, a generic "why this track exists" section, a list
  of planned lessons, or implementation taxonomy.
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
- **Keep the main path bounded.** A main tutorial should normally take 10–20
  minutes to read and use roughly 800–1,500 words of core prose. Above 1,600
  words, split a distinct learning outcome or move reference material out of the
  causal path. Below 700 words, verify that mechanism, failure boundary,
  executable path, evidence limit, and learner check are still complete. Word
  count is a diagnostic, not permission to pad or cut required reasoning.
- **Components are teaching instruments.** Introduce an interactive only after
  its variable, outcome, and prediction are clear in prose. It must let the
  learner change one causal variable, make the consequence legible without
  guessing, and return that consequence to the next paragraph. Decorative
  dashboards, unexplained controls, autoplay-only demonstrations, and
  components that duplicate prose are defects. Every component needs a useful
  static reading order and keyboard-accessible controls.
- **Interactive numbers obey the evidence contract.** A component that depicts
  a recorded run defaults to that run's measured values and links or names the
  evidence boundary. Rounded or hypothetical values must be labeled as such.
  Never place an illustrative number beside a measured narrative in a way that
  makes them appear to be the same result.
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
- **The landing page routes to topics; chapters teach.** Mechanism-specific
  demos live in the chapter that establishes their prerequisites and consumes
  their output. The landing page explains the topic-first curriculum model and
  sends the learner to a concrete topic, never to a carousel of abstract
  layers or a foundations/platform reading sequence.
- **A lesson is a complete decision path, not a stub.** State the mechanism,
  why it exists, its failure boundary, the executable path, and what the
  evidence does not prove. Split a lesson only when two chapters have distinct
  learning outcomes; do not split or pad to hit a line count.
- **Tutorial acceptance is reader-visible and route-complete.** For every
  changed tutorial, verify the actual generated route, first heading sequence,
  interactive state change, and next-step link. Check the full page and every
  widget at 390px with no horizontal overflow, controls at least 44px high, and
  no browser warnings or errors. Link generation must preserve `/playground`
  and pass the Docusaurus broken-link and broken-anchor checks.
- **Online claims require production evidence.** Do not say a tutorial is
  updated or live from a local build, commit, or deployment job alone. Confirm
  the deployed SHA, successful CI and deployment, then read the production
  page's opening question and section order and exercise at least one changed
  interaction. A successful build with unchanged learner-visible content is
  not acceptance.
- **No emoji.** Do not use emoji in published prose, navigation, status labels,
  controls, code examples, commit messages, or project instructions. Use words,
  semantic HTML, and the shared icon system when an icon is necessary. The
  repository test suite enforces this across authored text and source files.
- **Hardware-neutral in curriculum prose.** Write "a 24GB card" or "the local
  lane", not a specific GPU model. Naming real hardware is for `reference/`
  compute-lane guides and `runs/` records, which describe machines that
  actually ran something.
- **Name at least two production alternatives** in `LANDSCAPE.md` tables. Single
  tools get acquired and archived; the curriculum should survive that.
- **Commits**: `<type>(<scope>): <subject>`, imperative, ≤72 chars, no emoji.
  Types: `feat|fix|docs|refactor|perf|test|chore|build|ci|style`.
- **Files ≤800 lines.** `core/` files should be far shorter — they are read.

## Running GPU work

Local lane and Modal lane are both documented in [`reference/`](reference/),
as [`local-4090.md`](reference/local-4090.md) and [`modal.md`](reference/modal.md),
including a verified setup path and the failure modes worth knowing in advance.
Modal lessons print their dollar cost into `runs/`.

## What not to do

- Do not report a run you did not execute, or round a measured number toward a
  nicer one. If a model comes out at 88M, the docs say 88M.
- Do not vendor external projects. Link them, and explain when to reach for
  which.
- Do not let a `core/` implementation quietly depend on the framework its
  `prod/` counterpart uses. The point is that it does not.
