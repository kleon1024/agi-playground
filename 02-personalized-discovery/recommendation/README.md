---
status: draft
level: applied
---

# The recommendation track

Recommendation is the shared loop with no query and no paid item: the system
decides, from the user's history alone, what is worth showing next. The
frontier stages ask whether a language model can reorder the top of a cascade,
whether pairwise preference data can replace click labels, whether a VLM can
bridge the cold start, and whether a slate is worth more than the sum of its
item scores.

## The frontier track (stages 31-34)

| Stage | What it decides | Evidence |
|---|---|---|
| [`31-llm-ranking`](31-llm-ranking/) | The LLM listwise reorder over the cascade top | [verified](31-llm-ranking/runs/) |
| [`32-recommendation-rlhf`](32-recommendation-rlhf/) | Preference optimization over click labels | [verified](32-recommendation-rlhf/runs/) |
| [`33-multimodal-recall`](33-multimodal-recall/) | VLM content vectors as the cold-start bridge | [verified](33-multimodal-recall/runs/) |
| [`34-slate-vs-item-evaluation`](34-slate-vs-item-evaluation/) | The metric that sees the page, not the item | [verified](34-slate-vs-item-evaluation/runs/) |

## The label and objective track (stages 56-63)

Ranking is only as honest as the target it fits. These stages take one way the
observed label diverges from the decision the model is supposed to make and
measure what the fix costs: the sparse target learned on the wrong population,
the conversion labeled a negative before it happened, the downsampled negative
that breaks calibration, the model that only sees what the old model showed,
the whale that dominates the objective, the multi-task conflict, the funnel
the ranker scores one stage at a time, and the cascade whose top-k the
distillation blurs.

| Stage | What it decides | Evidence |
|---|---|---|
| [`56-entire-space-funnel`](56-entire-space-funnel/) | Whether the sparse target is learned on the wrong population | [verified](56-entire-space-funnel/runs/) |
| [`57-delayed-feedback`](57-delayed-feedback/) | The label window versus the conversion time | [verified](57-delayed-feedback/runs/) |
| [`58-negative-sampling`](58-negative-sampling/) | Downsampling negatives and the calibration cost | [verified](58-negative-sampling/runs/) |
| [`59-exposure-bias`](59-exposure-bias/) | Learning only from what the old model showed | [verified](59-exposure-bias/runs/) |
| [`60-heavy-tail-objective`](60-heavy-tail-objective/) | When one whale dominates the objective | [verified](60-heavy-tail-objective/runs/) |
| [`61-multi-task-conflict`](61-multi-task-conflict/) | When the tasks pull the shared trunk apart | [verified](61-multi-task-conflict/runs/) |
| [`62-funnel-consistency`](62-funnel-consistency/) | When the funnel stages disagree about the slate | [verified](62-funnel-consistency/runs/) |
| [`63-cascade-consistency`](63-cascade-consistency/) | When the cheaper model reorders what the expensive model chose | [verified](63-cascade-consistency/runs/) |

The [`shared/`](../shared/) track owns the spine these stages extend, and the
[`search/`](../search/) and [`ads/`](../ads/) tracks are its specializations.
