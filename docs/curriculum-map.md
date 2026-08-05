# Curriculum map — how every chapter relates

> Dated 2026-08-06. Generated from the repository tree and the depth-pass
> audit. This is the authoritative index of the tutorial system: what each
> mission owns, which stage each detour belongs to, where the lineage and
> model-anatomy content lives, and which stages still lack the deep-dive
> chapters the program requires.

## The spine and the four sections

Missions are the only curriculum spine: a learner starts from a stakeholder
problem and stays on the mission until it links to the mechanism or
engineering reference the next decision needs. Foundations and infra are
support libraries reached at that point, never read front to back. Reference
holds contracts, standards, and dated research.

Reading order is decided by the reader's decision, indexed in `site/topics.mdx`.
The level field encodes what each chapter assumes: foundation (a mechanism
later chapters assume), applied (a decision with a measured tradeoff),
frontier (an edge-of-evidence claim), reference (contributor surface). The
beginner-to-frontier path is mission-first; each detour returns an artifact
the stage consumes.

## Mission map

| Mission | Stages | Existing detours | Lineage survey | Anatomy chapters | Deep-dive gap |
|---|---|---|---|---|---|
| 01 language-model system | 8 (00-corpus..07-eval) | 36 detours across every stage | 01-language-model-system.md | attention-variants (KV anatomy) | stages already detoured; deepen on audit findings |
| 02 personalized discovery | 10 (00..09) | when-the-trade-weight-moves, when-the-cut-bites, when-you-lose-a-queue, when-the-weight-moves, when-the-cheap-cut-fails, when-the-rules-collide, when-sharing-hurts | 02-personalized-discovery.md | value-tree (strategy anatomy) | — |
| 03 quantitative research | 6 (00..05) | when-breadth-inflates-the-winner, when-purge-matters, when-the-cap-bites, asof-vs-naive, when-the-book-stops-making-money | 03-quantitative-research.md | none | no-gap |
| 04 code agent | 7 (00..06) | when-the-patch-cannot-apply, the-tier-that-won, what-the-task-set-contains, when-the-guardrail-refuses, does-feedback-help | 04-code-agent.md | none | — |
| 05 vision-language | 7 (00..06) | where-the-decoder-looks, seed-vs-pixels, when-warmup-closed-the-collapse, when-the-margin-is-narrow | 05-vision-language.md | none | — |
| 06 game AI | 7 (00..06) | the-diversity-direction, when-two-seeds-stopped-paying, when-the-cold-start-is-total | 06-game-ai.md | none | fixing-collapse (deepen) |
| 07 realtime voice | 7 (00..06) | why-codebooks-collapse, when-the-reset-never-stops, when-the-fix-did-not-generalize | 07-realtime-voice.md | codebook usage (VQ anatomy) | — |
| 08 video generation | 7 (00..06) | what-a-video-token-is, when-wrong-tokens-still-reconstruct, when-the-metric-hits-zero | 08-video-generation.md | video token (VQ anatomy) | — |
| 09 bio-pharma | 7 (00..06) | when-width-memorizes, the-split-that-decides, when-the-baseline-holds, when-scarcity-decides | 09-bio-pharma.md | none | — |

## Foundations and infra

Foundations (8 chapters, 3 detours): 00-attention (+ what-it-costs, + rope),
01-first-training-loop, 02-optimization, 03-backpropagation,
04-distributed-training, 05-is-the-difference-real (+ the-two-confounds),
06-significance, 07-moe. These own the mechanism; missions link at the
decision that needs it.

Infra (7 chapters): 01-networking, 02-storage, 03-orchestration,
04-observability, 05-gpu-cluster-concepts, 06-gpu-dedup-at-scale,
07-rollout-concurrency. These name the mission stage they are the substrate
for.

## Reference

Standards (mission-contract, lesson-and-run-contract), research passes
(01-06, dated), mid-training, and the lineage surveys. Reference is the only
place a page may have no run and not be a defect.

## The gap the deep-dive program closes

Mission 01 is the pattern: every stage carries its detours. Missions 02-09
have verified stages and zero detours, so the highest-leverage work is to
give each stage the detour its asserted mechanism is owed, in mission-01
style (a different decision than the stage, README + core/prod + runs, an
interactive when the mechanism is manipulable). The per-stage queues live in
`docs/superpowers/specs/2026-08-05-curriculum-depth-pass.md`; this map is
the state of the whole system as each queue is worked.
