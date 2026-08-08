# Design — Repo-wide depth pass: new chapters first, verification second

## Context

The user's asks across sessions, in order of appearance: "每个mission的每个
章节的深度都不够，差的远" (every mission's chapters are not deep enough);
"各种实际样本数据都没有体现，需要大规模下钻丰富" (none of the actual sample
data is reflected — needs large-scale deep-dive enrichment); "sft在模型大小上
的区别也没有" (the SFT model-size distinction is missing); "验证是一方面，
内容深度也是，需要下加更多章节" (verification is one thing, content depth is
another — we need to ADD more chapters); "通过实践上来" (ground it in
practice).

This spec replaces the earlier 04-09-only widget-parity spec
(`2026-07-31-mission-04-09-depth-pass-design.md`) as the governing plan. The
earlier spec's error was treating widgets as the depth deliverable; widgets
are a teaching instrument, not the depth. The depth deliverable is **new
chapters that answer a decision the main stage asserts without showing**, each
backed by a run executed here.

On 2026-08-06 the user added a second, parallel requirement: every mission
gets the **evolution of the historical open-source models behind it** — the
lineage, the tradeoffs each successor made, and the paper interpretations —
in the style of [Su Jianlin's K3 post](https://kexue.fm/archives/11848)
(2026-08-04): model iteration as inheritance-and-upgrade rather than
reinvention, with the effect/efficiency/stability axis explicit at every
step. The first instance (mission 01) ships with this revision; the other
eight are queued below.

## The method (applied to every chapter in the repo)

1. Read the chapter's causal spine. Mark every place a mechanism is asserted
   rather than shown — a formula stated, a number cited, a failure mode named
   with no worked example.
2. For each such place, decide by the central-question test:
   - **New detour chapter** when the missing depth answers a different
     decision than the main stage (e.g., "does SFT's effect change with model
     size?" is not the main stage's question, which is "how does SFT work?").
   - **Deepen in place** when the mechanism belongs to the main path and only
     needs a worked example or real sample data.
3. Practice first: write the run before the prose. A claim with no `runs/`
   entry stays out of the README (the repo's own invariant).
4. Sample data comes from the run's own output, not from a generic example —
   the agentic-format run (2026-08-05) is the pattern: the chapter shows the
   rendered trajectories, and the `runs/` record holds the full output and
   metrics.
5. External results are allowed and must be dated and attributed, and may
   never sit beside this repo's measured numbers as if measured the same way.

## The new-chapter queue (audited 2026-08-05)

The audit counted headings per chapter: mission 02 stages 06-09 and mission 03
stages 03-05 are the thinnest (3-6 headings), and every mission has at least
one stage that asserts a mechanism with no worked practice. The queue below
is the "add more chapters" list; each entry names the central question and
the practice run that answers it.

| Mission | Where | New chapter / deepening | Central question | Practice run | Status (checked 2026-08-08) |
|---|---|---|---|---|---|
| 01 | 03-sft | `what-model-size-changes` | Does SFT's effect scale with model size? | 5M pretrained-SFT vs 5M random-init-SFT vs recorded 88M SFT (this spec's pilot) | shipped |
| 01 | 00-corpus | mixture + agentic component | Where does agentic data enter the mix, and at what share? | agentic-format render run (2026-08-05) | shipped: `02-pretrain/mid-training` + agentic-formats + mix-seesaw runs |
| 01 | 02-pretrain | `when-the-curve-goes-wrong` (deepen, draft) | What can a loss curve tell you, and what can it not? | a seeded bad-run sweep | shipped |
| 01 | 07-eval | `why-believe-the-number` (deepen, draft) | What is one number from a harness worth? | variance re-runs across seeds | shipped |
| 02 | 06-mixing | mixing-weight chapter | What does a mixing weight actually trade off? | a two-weight ablation on the recall stage | shipped: `shared/06-mixing/when-the-trade-weight-moves` |
| 02 | 01-content-understanding | cold-start / sparse-interaction chapter | What can you recommend before a user has history? | popularity baseline vs the fine-rank stage | shipped as sibling surfaces: `shared/51-new-user-experience/when-the-user-is-new`, `search/23-personalized-search/when-the-new-user-is-the-majority` |
| 03 | 01-signal-research | false-discovery chapter | Why does a search over 1,000 signals find losers? | permutation-null run at higher trial counts | shipped: `when-breadth-inflates-the-winner` |
| 03 | 03-walk-forward | fold-fit chapter (deepen) | Why is fold-specific fit not strategy fit? | the existing runs' per-fold curves | shipped: `03-walk-forward-validation/when-purge-matters` |
| 04 | 04-how-it-fails | failure taxonomy (deepen) | Which failure modes are structural vs fixable? | re-run the agent at three temperatures | shipped: `the-zero-failure-taxonomy` |
| 04 | 03-cheap-or-expensive | cost curve (deepen) | Where is the cost-quality knee? | token-count curve from the recorded runs | shipped: `the-cost-quality-knee` |
| 05 | 01-vision-fusion | fusion mechanism | What does cross-attention actually fuse? | a weight/ablation study on the small VLM | superseded: mission 05 restructured to gridworld + GRPO; no vision-fusion stage remains |
| 06 | 01-grpo | advantage normalization (deepen) | What does GRPO's advantage normalization change? | the recorded GRPO run, recomputed by hand | shipped: `05-game-ai/01-grpo/the-policy-anatomy` |
| 07 | 00-audio-codec | codebook math (deepen) | Why does a VQ codebook collapse? | the recorded codec run's codebook statistics | shipped: `voice/00-audio-codec/why-codebooks-collapse` + `when-silence-is-a-local-minimum` |
| 08 | 01-video-tokenizer | codebook collapse (deepen) | What are the three failure modes, mechanistically? | the recorded codec run's three failure stats | shipped: `video/01-video-tokenizer/when-the-dead-codes-revive` + `what-a-video-token-is` |
| 09 | 01-descriptor-baseline | descriptor semantics | What does a fingerprint measure, and what does it miss? | the recorded grid's RDKit agreement | shipped: `08-bio-pharma-modeling/01-descriptor-baseline-and-model/two-ways-to-read-a-molecule` |
| foundations | 01-first-training-loop | worked backward pass | What does one backward pass compute, line by line? | a hand-traced backward pass vs autograd | shipped: `03-backpropagation/the-backward-pass-three-ways` (verified 2026-08-06, run recorded) |

## Mission 09 deep-dive slice (shipped 2026-08-08)

Mission 09 (autonomous driving) is the newest topic: 7 stages, zero detours
at the start of this pass. The first three detours landed 2026-08-08,
each with an executed CPU run and the fix/trade/ownership structure, mapped
to the mission's industrial failure modes.

| Where | New chapter | Central question | Practice run | Status |
|---|---|---|---|---|
| 04-closed-loop-eval | `when-the-open-loop-lies` | Where does the 0.77-to-0.28 gap live, and why do the errors compound? | per-class imitation error + closed-loop divergence run | shipped |
| 05-harder-scenarios | `when-the-policy-stalls` | What is a 72% timeout made of, and why is a stall a safety failure? | stall-profile run (creep, progress, safe state) | shipped |
| 05-harder-scenarios | `when-the-aggregate-hides-the-corner` | Does the OOD boundary hold uniformly across the declared ODD? | per-cell split + coverage/n math | shipped |

Remaining mission-09 queue: stages 00-scenario-simulator, 01-perception,
02-expert, 03-cloning, and 06-report carry no detour yet; the next slice
can run the perception-latency, expert-trust, and report-evidence questions
through the same audit.

Audit notes from the 2026-08-08 pass:

- The failure-mode ownership audit is complete repo-wide: every tutorial
  chapter README now carries `## The fix and its trade` (and, where the loop
  crosses teams, `## Who owns the loop`), with numbers taken from the
  chapter's own `runs/` record. The only READMEs without it are index pages
  (mission roots, surface roots, `prod/` code readmes).
- `docs/curriculum-map.md` was regenerated 2026-08-08 from the tree: mission
  02 now counts 67 stages and 186 when-* detours, the mission list matches
  the current eight topics, and a mission-09 row exists with its three new
  detours counted.
- Mission 09 (autonomous driving) went from 7 stages and zero detour
  chapters to three detours under stages 04-05 (this pass, above); stages
  00-03 and 06 remain bare and are the next queue slice.

Not in this queue: chapters already deep (missions 01's corpus/tokenizer/
pretrain, 07-eval's metric-gaming, mid-training), which only get deepened if
a real gap shows up during the pass.

## Per-mission model lineage, in the repo's own style

The lineage content follows the existing tutorial conventions (English,
first-viewport contract, causal spine, evidence boundary, no emoji, no
unrun numbers), not the blog voice of the source that inspired it. Two
surfaces, both dated and attributed:

- **One lineage survey per mission** under `reference/research/lineages/`
  (reference: the line, the tradeoffs, the paper interpretations). Mission 01
  shipped 2026-08-06 in the repo's teaching voice.
- **Per-model anatomy chapters** for the structure itself: one chapter per
  model or family, describing the mechanism, comparing it against its
  predecessor and successor, with a drawn structure — an interactive widget
  on the `learning-widget` contract or the shared `ProcessDiagram` grammar,
  never new Mermaid. The first is the attention-variants detour under
  mission 01 stage 02 (MHA/GQA/MQA/MLA with a KV-cache anatomy widget). The
  queue below lists the rest, owned by the mission whose stage makes the
  choice.

The 2026-08-06 correction that produced this: the lineage is context, and
context must not be written as a blog post. A learner reaches it from a
mission decision, reads the line, and returns with the tradeoff named.

## Every chapter gets deep-dive chapters

Mission 01 is the pattern, not the exception: a stage states a decision, and
one or more detour chapters under it answer the decisions the main path
asserts without showing. The rule going forward: **a stage that asserts a
mechanism or a tradeoff without a detour that walks it has a gap.** The
16-chapter queue above is the audit's start, not its extent; each mission
fork re-runs the audit against its own stages as it deepens them.

| Mission | Lineage chapter | Line it traces |
|---|---|---|
| 01 | `01-language-model-system.md` (shipped 2026-08-06) + attention-variants anatomy | data/scale, BPE vocab, architecture (RoPE/GQA/MLA/KDA/MoE), SFT, RL, serving, agents |
| 02 | `02-personalized-discovery.md` (shipped 2026-08-06) | recommenders: collaborative filtering, matrix factorization, two-tower, retrieval-cascade, reranking |
| 03 | `03-quantitative-research.md` (shipped 2026-08-06) | signal search, multiple testing, walk-forward, cross-validation, backtest-overfit literature |
| 04 | `04-code-agent.md` (shipped 2026-08-06) | code LMs (Codex/CodeLlama/DeepSeek-Coder), agent loops, SWE-bench, verifier/RL for code |
| 05 | `05-vision-language.md` (shipped 2026-08-06) | CLIP/SigLIP, LLaVA-style fusion, Qwen2-VL, captioning-to-VQA |
| 06 | `06-game-ai.md` (shipped 2026-08-06) | value/policy RL: DQN, PPO, GRPO, R1-Zero's verifiable-reward games |
| 07 | `07-realtime-voice.md` (shipped 2026-08-06) | VQ-VAE, SoundStream, EnCodec, DAC, streaming decode, codebook-reset line |
| 08 | `08-video-generation.md` (shipped 2026-08-06) | VQ-VAE for video, VideoPoet/DiT, W.A.L.T., autoregressive video limits |
| 09 | `09-bio-pharma.md` (shipped 2026-08-06) | molecular fingerprints (ECFP/Murcko), graph nets, SMILES LMs, property prediction |

Each lineage chapter is `level: reference`, dated, and linked from its
mission's detour table and the research index — the mission owns the runs,
the lineage owns the context.

The complete chapter-relationship index — every mission stage, its detours,
its lineage survey, and its deep-dive gap — is the
[curriculum map](../../curriculum-map.md), updated as each queue is
worked.

## Sequencing

One fork per mission, oldest-built first: 01 (this pilot), then 04-09
(upgrading the earlier widget-parity list to run-grounded chapters), then
02-03, then foundations. Each fork proposes its specific new chapter and
practice run before writing anything, then runs the repo gates and commits
per mission.

## Acceptance

For every new or deepened chapter:

- a `runs/` record with command, hardware, wall-clock, cost, and the numbers;
- real sample data rendered from that run's output, not generic examples;
- the mechanism's failure boundary stated, and what the run does not prove;
- a check-your-mental-model question that the chapter's own evidence answers;
- `uv run ruff check .`, `uv run pytest -q`, and the site sync/typecheck/build
  with no broken-link or broken-anchor warnings;
- the generated route and at least one interactive state change checked at
  390px before the chapter is called done.

Verification (`status: verified`) is the floor. A chapter that is verified but
shallow is a defect this pass exists to remove.
