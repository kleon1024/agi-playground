---
level: reference
---

# Research

The positioning and landscape research behind agi-playground. This repo was designed
research-first: before writing a single lesson, we surveyed what already exists, what
works pedagogically, and where the gaps are. These documents are updated periodically
as the landscape moves.

The synthesis distills four parallel surveys into the design principles the repo is
built on — most importantly the **"read the toy, then map to the real thing"** pedagogy
and the four gaps no existing resource covers with depth: data/annotation, progressive
RL post-training, exercise-driven inference infra, and agent harness engineering.

| Document | Contents |
|---|---|
| [synthesis.md](synthesis.md) | Distilled findings: positioning, per-track anchors, compute lanes |
| [01-curricula-landscape.md](01-curricula-landscape.md) | Existing curricula (Karpathy lineage, CS336, Raschka, HF courses, fast.ai) and gap analysis |
| [agentic-paradigm-restructuring.md](agentic-paradigm-restructuring.md) | 2026 survey: does the agentic turn restructure decision-loop industries (risk, search, ads, recsys) or layer on top of them |
| [lineages/](lineages/) | Model lineage notes no longer kept as one collection: each topic carries its own `lineage.md` beside the stages it traces (e.g. [`01-language-model/lineage.md`](../../01-language-model/lineage.md)). |

The later passes moved with the topic they describe: pretraining and
post-training landscape now sit beside the corpus and RL stages in
[`01-language-model/`](../../01-language-model/), and the agent-memory and
harness-effects passes sit beside the agentic platform stages in
[`04-agentic-platform/`](../../04-agentic-platform/).

> Passes 01-04 were conducted 2026-07-24; pass 05 on 2026-07-29; pass 06 on
> 2026-07-30; the agentic-paradigm pass on 2026-08-08. Landscape facts
> (versions, benchmarks, project status) reflect those dates; verify before relying
> on them.
