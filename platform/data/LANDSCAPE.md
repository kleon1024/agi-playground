---
status: draft
---

# Data: Landscape

Source: `research/synthesis.md` anchor table, "Data pipeline" and
"Annotation/synthetic" rows.

| Toy (teach-from) | Production | Our take |
|---|---|---|
| datatrove reruns of published FineWeb pipeline stages on Common Crawl shards | NeMo Curator (GPU-accelerated, runs well on Modal), dolma, DCLM methodology | datatrove is CPU-bound and readable end-to-end, which is why we teach from it — but it's also a real production tool (HuggingFace uses it for FineWeb), not a toy stand-in. NeMo Curator is the GPU-accelerated path once corpus size demands it; dolma and DCLM are the methodology references for filtering/mixing decisions. Naming three keeps us off a single vendor. |
| distilabel + Argilla for annotation and synthetic data; Label Studio for generic labeling tasks | Same tools — distilabel/Argilla/Label Studio are the production tools, not toy stand-ins | Unlike most rows in this curriculum, there's no from-scratch-vs-production split here: annotation tooling is complex enough (UI, workflow state, review queues) that reimplementing it teaches little. We teach the real tools directly, at small scale. Label Studio is the generic-purpose alternative if a team doesn't want Argilla's Hugging Face-centric workflow. |

**Single-vendor-rot note:** the annotation row is the one place in this
curriculum where "toy" and "production" collapse to the same tools. That's a
deliberate exception, not drift — see the row's rationale above. The data
pipeline row still keeps three independent projects (datatrove/HF, NeMo
Curator/NVIDIA, dolma+DCLM/Allen AI &co.) so no single vendor's roadmap can
strand this lesson.
