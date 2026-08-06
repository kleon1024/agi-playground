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
| 01 language-model system | 8 (00-corpus..07-eval) | 38 detours across every stage | 01-language-model-system.md | attention-variants (KV anatomy), the-kl-leash, the-gate-that-beats-relu | stages already detoured; deepen on audit findings |
| 02 personalized discovery | 10 (00..09) | when-the-trade-weight-moves, when-the-cut-bites, when-you-lose-a-queue, when-the-weight-moves, when-the-cheap-cut-fails, when-the-rules-collide, when-sharing-hurts, when-the-split-leaks, when-the-threshold-rescues-the-tail, when-the-guardrail-vetoes | 02-personalized-discovery.md | value-tree (strategy anatomy) | — |
| 03 quantitative research | 6 (00..05) | when-breadth-inflates-the-winner, when-purge-matters, when-the-cap-bites, asof-vs-naive, when-the-book-stops-making-money, when-the-refusal-names-everything, the-rank-that-becomes-a-position | 03-quantitative-research.md | rank-to-position (sizing anatomy) | no-gap |
| 04 code agent | 7 (00..06) | when-the-patch-cannot-apply, the-tier-that-won, what-the-task-set-contains, when-the-guardrail-refuses, does-feedback-help, when-the-blind-call-fails, when-the-partial-verdict, the-loop-that-scores-a-patch | 04-code-agent.md | agent loop (harness anatomy) | — |
| 05 vision-language | 7 (00..06) | where-the-decoder-looks, seed-vs-pixels, when-warmup-closed-the-collapse, when-the-margin-is-narrow, the-real-photo-guardrail, when-the-api-still-wins, when-the-category-breaks-down, the-fused-attention-anatomy | 05-vision-language.md | fused attention (VLM anatomy) | — |
| 06 game AI | 7 (00..06) | the-diversity-direction, when-two-seeds-stopped-paying, when-the-cold-start-is-total, when-the-verdict-is-not-met, when-the-null-is-elevated, when-random-gets-22-percent, when-the-policy-collapses, the-policy-anatomy | 06-game-ai.md | policy+reward (RL anatomy) | fixing-collapse (deepen) |
| 07 realtime voice | 7 (00..06) | why-codebooks-collapse, when-the-reset-never-stops, when-the-fix-did-not-generalize, when-the-cache-pays, the-half-that-did-the-work, when-the-network-is-the-tail, when-the-transfer-is-clean | 07-realtime-voice.md | codebook usage (VQ anatomy) | — |
| 08 video generation | 7 (00..06) | what-a-video-token-is, when-wrong-tokens-still-reconstruct, when-the-metric-hits-zero, when-the-cost-ceiling-is-roomy, when-the-seed-is-the-answer, when-the-frames-double, when-two-shapes-share-a-token | 08-video-generation.md | video token (VQ anatomy) | — |
| 09 bio-pharma | 7 (00..06) | when-width-memorizes, the-split-that-decides, when-the-baseline-holds, when-scarcity-decides, when-the-baseline-refuses-to-lose, when-the-verdict-is-inconclusive, when-the-mid-range-point-lands, two-ways-to-read-a-molecule | 09-bio-pharma.md | two representations (molecule anatomy) | — |

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
foundations, and infra now have every chapter covered with at least one
detour (audited 2026-08-06): each detour answers a different decision than
its parent, in mission-01 style (README + core + runs, an interactive when
the mechanism is manipulable), and every number traces to the recorded run.
The per-model anatomy series is complete: one structure chapter per mission
(KV/attention for 01, value-tree for 02, rank-to-position for 03, agent
loop for 04, fused attention for 05, policy+reward for 06, VQ codebook for
07, video token for 08, molecule representations for 09). The per-stage
queues live in `docs/superpowers/specs/2026-08-05-curriculum-depth-pass.md`;
this map is the state of the whole system as each queue is worked.
