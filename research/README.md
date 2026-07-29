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
| [02-pretraining-and-data.md](02-pretraining-and-data.md) | Pretraining reference implementations; data pipeline, curation, annotation, tokenizer tooling |
| [03-post-training-and-rl.md](03-post-training-and-rl.md) | Post-training frameworks, the 2026 algorithm canon (DPO family, GRPO/RLVR), recipes, 4090 feasibility |
| [04-infra-and-agent-harness.md](04-infra-and-agent-harness.md) | Inference engine internals, training infra, agent harness engineering, evals, solo-builder infra |
| [05-agent-memory.md](05-agent-memory.md) | Agent memory storage shapes, what Anthropic actually ships, the provenance of the "graph engineering" claim, and the edge-density measurement nobody publishes |

> Passes 01-04 were conducted 2026-07-24; pass 05 on 2026-07-29. Landscape facts
> (versions, benchmarks, project status) reflect those dates; verify before relying
> on them.
