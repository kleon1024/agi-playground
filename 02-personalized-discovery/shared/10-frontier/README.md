---
status: verified
level: frontier
verified: 2026-08-08
label: The frontier
---

# When the loop becomes the surface?

**Question:** stages 00–55 measured the discovery loop — recall, rank, mix,
serve, measure — on recorded data. This stage asks the question the loop's
existence implies: recommendation, search, and advertising are converging on
intent-to-delivery as their decision surface, and the convergence changes
which mechanisms are load-bearing. The
[paradigm survey](../../../reference/research/agentic-paradigm-restructuring.md)
documents Google folding search into a conversational loop (AI Mode passed 1
billion monthly users at I/O 2026) and OpenAI moving ads inside the answer
thread; the three chapters below are the frontier reading of this mission's
own recorded runs against that claim.

**Before this:** [stage 09](../09-report/) closes the measured arc, and the
frontier tracks — [31-llm-ranking](../../recommendation/31-llm-ranking/),
[36-conversational-search](../../search/36-conversational-search/), and
[18-ad-externality](../../ads/18-ad-externality/) — recorded the runs these
chapters read. The three chapters here are the decision-oriented reading of
everything those stages recorded.

## The frontier, as one causal chain

| Chapter | The question it answers | What it returns |
|---|---|---|
| [When does the result page become a conversation?](the-conversational-surface/) | what the session actually changes as the unit of search | the per-query-versus-session verdict (46.6% per-query failures, 19.9% recovered), read from the recorded AOL query-log and resolution audit |
| [What replaces the score?](verification-replaces-score/) | which mechanisms persist when generation replaces ranking | the reorder-without-a-check fact (4/5 positions changed) and the calibration-break reorder (1.6x inflation), read from the recorded ranking and value-tree runs |
| [What survives of the auction?](ads-inside-the-loop/) | what an ad becomes when it sits inside the answer thread | the displacement table and the pacing contrast (naive exhausts at hour 3 vs paced 88.4/11.6), read from the recorded ads runs |

Each chapter follows the same contract the [depth audit](../../../reference/standards/depth-audit.md)
applies to every stage: the failure mode is named before the fix, the case is
found in recorded data, the fix's trade is measured, the whole loop (not just
the model) is covered, nothing is written from memory, and the reader leaves
able to answer the operational version of the question. Every number in the
three chapters traces to a `runs/` entry in this mission or to a dated
external source; no model was called and no new run was executed to produce
them.

## What this stage does not prove

The frontier reading is an analysis of recorded and published evidence, not a
new run: the tables above reuse this mission's own runs (the AOL session read,
the resolution audit, the LLM ranking and value-tree sweeps, the ads
displacement and pacing simulations) and do not add a model call or a dollar
of spend. The external claims — AI Mode's user count, the ChatGPT ad pricing
shift, the four generative-recommendation papers — are 2026 snapshots with
dates attached, and each chapter's evidence boundary says which of them this
repo could check. The chapters also do not prove the convergence is durable:
the surface could move again, and the measurement discipline that survives
(latency and cost budgets, attribution, the multi-target decision) is the
stable part of the reading.
