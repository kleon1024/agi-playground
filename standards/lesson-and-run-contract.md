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
