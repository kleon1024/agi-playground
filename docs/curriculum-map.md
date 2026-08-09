# Curriculum map — how every chapter relates

> Dated 2026-08-08. Regenerated from the repository tree (not from memory):
> stage counts are numbered chapter directories at the topic's stage depth,
> detour counts are `when-*` sub-chapter directories, and every gap note was
> re-checked against the tree this pass. This is the authoritative index of
> the tutorial system: what each topic owns, which stage each detour belongs
> to, where the lineage and model-anatomy content lives, and which stages
> still lack the deep-dive chapters the program requires.

## The spine and the four sections

Topics are the only curriculum spine: a learner starts from a stakeholder
problem and stays on the topic until it links to the mechanism or
engineering reference the next decision needs. Foundations and reference are
support libraries reached at that point, never read front to back.

Reading order is decided by the reader's decision, indexed in
`site/topics.mdx`. The level field encodes what each chapter assumes:
foundation (a mechanism later chapters assume), applied (a decision with a
measured tradeoff), frontier (an edge-of-evidence claim), reference
(contributor surface). The beginner-to-frontier path is topic-first; each
detour returns an artifact the stage consumes.

## Topic map

Counts verified 2026-08-09. "Stages" are the numbered main-path chapters;
"when-* detours" are the deep-dive sub-chapters that answer a decision the
main path asserts without showing. Some stages also carry non-`when-`
sub-chapters (for example mission 01's `is-it-the-same-tokenizer` and
`why-believe-the-number`), which the detour counts below do not include.

| Topic | Stages | when-* detours | Lineage survey | Anatomy chapters | Deep-dive gap |
|---|---|---|---|---|---|
| 01 language-model system | 8 (00-corpus..07-eval) | 18 | `01-language-model/lineage.md` + `vision/lineage.md` | attention-variants (KV anatomy), the-kl-leash, the-gate-that-beats-relu | stage 07-eval carries no when-* detour (its depth lives in `why-believe-the-number`); stages 01 and 06 have one each |
| 02 personalized discovery | 67 (00..65 across recommendation/search/ads, plus shared/) | 190 | `02-personalized-discovery/lineage.md` | value-tree (strategy anatomy) | — |
| 03 quantitative research | 6 (00..05) | 6 | `03-quantitative-research/lineage.md` | the-rank-that-becomes-a-position (sizing anatomy) | stage 00-market-data carries no when-* detour |
| 04 agentic platform | 7 (00..06) | 5 | `04-agentic-platform/lineage.md` | agent loop (harness anatomy) | stages 00, 05, 06 carry no when-* detour |
| 05 game AI | 7 (00..06) | 9 | `05-game-ai/lineage.md` | the-policy-anatomy (GRPO anatomy) | stages 02, 03, 05 carry no when-* detour |
| 07 multimodal generation | 14 (voice 00..06 + video 00..06) | 22 | `voice/lineage.md` + `video/lineage.md` | voice codebook usage + video-token (VQ anatomy, both surfaces) | — |
| 08 bio-pharma modeling | 7 (00..06) | 6 | `08-bio-pharma-modeling/lineage.md` | two-ways-to-read-a-molecule (representation anatomy) | stages 02, 04, 06 carry no when-* detour |
| 09 autonomous driving | 7 (00..06) | 8 | `09-autonomous-driving/lineage.md` | none yet | eight detours landed 2026-08-08, one or more per stage (see the depth-pass spec) |

## Foundations

Foundations (8 chapters, 9 `when-*` detours): 00-attention (+ what-it-costs,
+ rope), 01-first-training-loop (+ the-curve-that-takes-34-seconds),
02-optimization (+ the-flips-that-separate-optimizers),
03-backpropagation (+ the-backward-pass-three-ways, shipped and verified),
04-distributed-training (+ when-the-ranks-agree, with the four machine
chapters networking/storage/orchestration/gpu-cluster-concepts each carrying
one detour), 05-is-the-difference-real (+ when-the-comparisons-multiply),
06-significance (+ when-the-interval-decides), 07-moe
(+ when-the-expert-goes-dead). These own the mechanism; topics link at the
decision that needs it.

## Reference

Standards (mission-contract, lesson-and-run-contract), the model-lineages
index (`reference/research/lineages/`), and the dated research material in
each topic's own directory. Reference is the only place a page may have no
run and not be a defect.

## The gap the deep-dive program closes

Mission 01 is the pattern: a stage states a decision, and one or more detours
under it answer the decisions the main path asserts without showing, each
backed by a run recorded in `runs/`. 264 `when-*` detour chapters across the
eight topics, plus 9 foundations detours, as of 2026-08-08. The per-topic
anatomy series is complete: mission 09, the newest topic, now carries eight
detours covering all seven of its stages.

The active queue: the remaining depth-pass spec items are tracked in
`docs/superpowers/specs/2026-08-05-curriculum-depth-pass.md`. The per-stage
queues live there; this map is the state of the whole system as each queue
is worked.
