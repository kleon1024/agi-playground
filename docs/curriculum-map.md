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
| 01 language-model system | 8 (00-corpus..07-eval) | 39 detours across every stage, at least two each | 01-language-model-system.md | attention-variants (KV anatomy), the-kl-leash, the-gate-that-beats-relu | — |
| 02 personalized discovery | 31 (00..30) | 72 detours, every stage at least two | 02-personalized-discovery.md | value-tree (strategy anatomy) | — |
| 03 quantitative research | 6 (00..05) | 12 detours, two per stage | 03-quantitative-research.md | rank-to-position (sizing anatomy) | no-gap |
| 04 code agent | 7 (00..06) | 14 detours, two per stage | 04-code-agent.md | agent loop (harness anatomy) | — |
| 05 vision-language | 7 (00..06) | 14 detours, two per stage | 05-vision-language.md | fused attention (VLM anatomy) | — |
| 06 game AI | 7 (00..06) | 14 detours, two per stage | 06-game-ai.md | policy+reward (RL anatomy) | — |
| 07 realtime voice | 7 (00..06) | 14 detours, two per stage | 07-realtime-voice.md | codebook usage (VQ anatomy) | — |
| 08 video generation | 7 (00..06) | 14 detours, two per stage | 08-video-generation.md | video token (VQ anatomy) | — |
| 09 bio-pharma | 7 (00..06) | 14 detours, two per stage | 09-bio-pharma.md | two representations (molecule anatomy) | — |

## Foundations and infra

Foundations (8 chapters, 9 detours): 00-attention (+ what-it-costs, + rope),
01-first-training-loop (+ the-curve-that-takes-34-seconds),
02-optimization (+ the-flips-that-separate-optimizers),
03-backpropagation (+ the-backward-pass-three-ways),
04-distributed-training (+ when-the-ranks-agree),
05-is-the-difference-real (+ the-two-confounds),
06-significance (+ when-the-interval-decides),
07-moe (+ when-the-expert-goes-dead). These own the mechanism; missions
link at the decision that needs it.

Infra (7 chapters, 7 detours): 01-networking (+ when-the-ring-beats-the-star),
02-storage (+ when-a-node-joins), 03-orchestration (+ when-the-scheduler-chooses),
04-observability (+ when-the-tail-waits), 05-gpu-cluster-concepts
(+ when-the-topology-costs), 06-gpu-dedup-at-scale
(+ when-verification-goes-quadratic), 07-rollout-concurrency
(+ when-the-heavy-tail-waits). These name the mission stage they are the
substrate for.

## Reference

Standards (mission-contract, lesson-and-run-contract), research passes
(01-06, dated), mid-training, and the lineage surveys. Reference is the only
place a page may have no run and not be a defect.

## The gap the deep-dive program closes

Mission 01 is the pattern: every stage carries its detours. Missions 02-09,
foundations, and infra now have every chapter covered with at least two
detours (audited 2026-08-06): each detour answers a different decision than
its parent, in mission-01 style (README + core + runs, an interactive when
the mechanism is manipulable), and every number traces to the recorded run.
197 detour chapters across the nine missions, plus 9 foundations and 7 infra
detours. The per-model anatomy series is complete: one structure chapter per
mission (KV/attention for 01, value-tree for 02, rank-to-position for 03,
agent loop for 04, fused attention for 05, policy+reward for 06, VQ codebook
for 07, video token for 08, molecule representations for 09). The per-stage
queues live in `docs/superpowers/specs/2026-08-05-curriculum-depth-pass.md`;
this map is the state of the whole system as each queue is worked.
