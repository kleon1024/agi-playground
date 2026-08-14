---
status: draft
level: frontier
label: Real tasks
---

# The platform passed its own tests. What happens on real work?

**Question:** every stage so far scored the harness on six mined tasks.
Real work is different in kind, not just size: data engineering migrations,
large-project refactors, and deployment modernization have dependency
graphs, org boundaries, and failure costs that a bug-fix task set cannot
represent. The industry's proof points are the dataset migrations (OpenAI's
90,000-table cloud move, Spotify's Honk across 1,800 pipelines) and
deployment rewrites (TensorRT-LLM's AutoDeploy). What does this topic's
platform actually buy on tasks like those, and what is still human?

**The artifact this stage follows** is the capstone run: a real task drawn
from this repository's own history — a genuine regression or failure with a
recorded fix — executed by the platform built across stages 02–15, with the
full evidence trail in `runs/`.

By the end you will be able to take a real engineering task, decompose it
with the orchestration decisions of stage 11, run it under the platform's
authorization matrix, and report what the platform resolved and what
required a human — without fabricating either number.

**Before this:** all fifteen stages of the platform. This is the
integration test.

## What this stage decides

Whether the platform is worth anything on work the mission did not
construct. The decision is measured: resolve rate and cost per resolved on
the real task, against the same no-harness baseline from stage 01.

## Planned chapters

- **data-engineering-migration** — the reference cases: OpenAI's migration
  of 90,000 tables / ~600PB across clouds on a ~100,000-node dependency
  DAG, and Spotify's Honk migrating ~1,800 downstream pipelines with
  LLM-as-judge verification; what made them agents-shaped and what stayed
  human.
- **large-project-refactor** — codebase-level work: the 90-file monorepo
  refactor cases, why retrieval quality decides success, and what an
  architect-agent layer changes.
- **trt-deployment-modernization** — deployment work as an agent task:
  TensorRT-LLM AutoDeploy converting PyTorch models to TensorRT-LLM
  automatically (sharding, quantization, KV-cache, fusion passes) — a
  modern example of "the model deployment" real task the mission could run
  on hardware that fits.
- **run-a-real-task** (capstone, recorded) — a genuine task from this
  repository's history executed under the full platform, with the same
  evidence contract as every other run.

## Evidence strategy

`run-a-real-task` is a real recorded run on the local lane. The three
reference chapters are dated surveys of published engineering posts with
their numbers attributed; the repository's rule stands — if it cannot run
here, it is a survey, not a result.

## Industrial grounding

OpenAI's data agent migrated 90,000 tables and 600PB across clouds with a
dependency graph on the order of 100,000 nodes in about two months.
Spotify's Honk automated ~1,800 dataset-pipeline migrations, saving an
estimated 10 engineering weeks, using an LLM-as-judge verification loop.
NVIDIA's TensorRT-LLM AutoDeploy automates PyTorch-to-TensorRT conversion
with compiler-style fusion passes. All three are dated external results,
cited inline.
