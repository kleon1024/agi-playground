---
level: reference
---

# The lesson and run contract

Two rules govern everything published here:

> **Every capability claim is backed by a run.**
> **Every mission is backed by a measurable outcome.**

Technical numbers trace to `runs/`. Outcome claims trace to a baseline, an
outcome, and guardrails — see [`mission-contract.md`](mission-contract.md).

## Lesson anatomy

Every lesson, wherever it sits in the tree, is a directory:

```
<lesson>/
├── README.md   # intuition → mechanism → walkthrough → production notes → exercises
├── core/       # from-scratch: minimal dependencies, written to be read
├── prod/       # the same job with the real tool, config included
└── runs/       # what actually happened
```

`core/` teaches mechanism; `prod/` teaches practice. Both must run. A `core/`
implementation that quietly imports the framework its `prod/` counterpart uses
has defeated its own purpose.

## Run record

Every `runs/` entry states:

- **Command** — exactly what was executed, copy-pasteable
- **Hardware** — the machine, not a category
- **Software** — versions that affect the result
- **Wall-clock** — real elapsed time
- **Cost** — dollars for cloud runs, `$0 (local lane)` otherwise
- **Metrics** — the numbers, as produced
- **Notes** — what surprised you, what broke, what a reader should expect

A number that appears in a `README.md` but in no `runs/` entry is a bug.

## Status

Frontmatter carries `status:`, and it is not decoration:

- `draft` — written, not yet run. Shows as draft in every index.
- `verified` — has a `runs/` entry, with `verified: YYYY-MM-DD`.

A lesson is promoted to `verified` by running it, not by finishing the prose.

## Level

Every published page declares `level:`. Curriculum position and difficulty are
different things, and the sidebar can only carry one of them — a reader looking
at an ordered list of chapters cannot tell which are prerequisites and which
assume everything before them.

- `foundation` — a mechanism later chapters assume you hold. Read out of order
  and the pages that depend on it stop parsing.
- `applied` — a decision with a measured tradeoff. Assumes the mechanism, and
  spends its words on what to choose and what the choice costs.
- `frontier` — a claim at the edge of what this repository can establish. The
  evidence boundary is the point of the chapter, not a closing caveat.
- `reference` — a lookup or contributor surface, not a rung on the ladder:
  standards, infrastructure runbooks, research passes, and `LANDSCAPE.md`
  tables.

The level is about what the page assumes, not how long it is. Reading time is
computed from the prose at sync time and never written by hand, so it cannot
drift away from the page it describes.

## Base

Any lesson that trains, adapts, serves, or evaluates a model declares which
weights its claims rest on. The field is required in the frontmatter of every
lesson under `foundations/` and `01-language-model/`:

- `base: scratch` — **Track A.** Weights this repository produced, tracing back
  to a random initialization here. Nothing published was downloaded.
- `base: external:<model-id>` — **Track B.** A published checkpoint, named
  exactly as it is distributed, e.g. `external:Qwen/Qwen3-0.6B-Base`.
- `base: none` — the lesson trains and evaluates no model at all. A corpus
  lesson, a tokenizer lesson, or a harness whose recorded run uses a scripted
  backend.

The field describes the model being trained or measured. A teacher, a judge,
or a reference model is named in the prose, not here — `distillation` trains a
Track A student against an external teacher and declares `scratch`.

### Why this is a required field and not a note

Track A exists because building the thing from random initialization is the
only way to learn what the thing is. Track B exists because Track A's 88M
model cannot do most of what the later stages are about, and pretending
otherwise produces lessons that teach something false while logging clean
curves.

The sharpest case is RL. GRPO normalizes advantage within a rollout group: the
advantage of each sample is its reward minus the group mean, divided by the
group standard deviation. If every rollout in the group fails, every reward is
identical, the standard deviation is zero, and the advantage is zero for every
sample — so the gradient is zero and the update is a no-op. A base model with
a zero pass rate on the task therefore cannot be improved by GRPO, and the
loss curve will look perfectly reasonable while nothing happens. An RL lesson
that does not say which base it ran on cannot be checked for this, which is
why the declaration is machine-enforced in `tests/test_repo_structure.py`
rather than left to the author's memory.

## Rules that came from getting it wrong

Each of these is here because it was violated first:

- **If the model comes out at 88M, the docs say 88M.** Do not round a measured
  number toward a nicer one, and do not pad an implementation to match a claim
  written before it existed. Fix the claim.
- **Hardware-neutral in curriculum prose.** Write "a 24GB card" or "the local
  lane". Specific hardware belongs in `infra/` and `runs/`, which describe
  machines that actually ran something.
- **Name at least two production alternatives** in any landscape table. Single
  tools get acquired and archived; the curriculum should survive that.
- **Dated external numbers must be dated.** A 2024 benchmark figure cited as
  current is a false claim with extra steps.
- **Flush your long-running logs.** A two-hour job that block-buffers stdout
  looks identical to a hung one.
- **Verify the process, not the wrapper.** `pgrep | head -1` can match a shell
  and report 0% CPU for a perfectly healthy job.
