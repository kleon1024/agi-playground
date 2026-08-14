---
level: reference
---

# When the harness moved the score (2026)

> Research pass conducted 2026-07-30; sources linked inline. This is a survey of
> a published external result, not a run. No number below was measured in this
> repository, and the last section says which of them this repo could check.

Mission 01 stages 06 and 07 argue that an agent benchmark score is a function of
the model *and* the harness, and that most published numbers disclose only the
first. That argument had no public case where someone changed the harness alone
and watched the score move. It has one now.

## (a) What OpenAI published

On 2026-07-30 OpenAI posted
["How enabling two settings tripled our scores on the ARC-AGI-3 benchmark"](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/).
The numbers, as published:

| | Score |
|---|---:|
| GPT‑5.5, ARC's headline number | 0.4% |
| GPT‑5.6 Sol, ARC's headline number | 7.8% |
| GPT‑5.6 Sol, official harness, public set | 13.3% |
| GPT‑5.6 Sol, OpenAI's harness, public set | **38.3%** |
| Average human tester (OpenAI's estimate from ARC's gameplay logs) | 48% |

Roughly **3x the score with 6x fewer output tokens**, from two settings, with
the model unchanged. Scores are Relative Human Action Efficiency (RHAE), ARC's
own metric.

[ARC‑AGI‑3](https://arcprize.org/arc-agi/3) launched 2026-03-25: hundreds of
handcrafted interactive 2D games, no instructions, no stated goal, no rules. The
agent has to explore, build a world model, infer what counts as progress, and
plan — and at launch every frontier model scored below 1% while humans solved
every environment.

## (b) The two settings

**Retained reasoning.** The official harness discarded the model's private
reasoning after each game action. The model could still see a record of past
moves and short notes, but not the plans or insights that produced them — so it
re-derived the game from scratch every turn. OpenAI's Responses API retains
reasoning across turns when you pass the previous response ID, which is how the
model is trained and how it is deployed in ChatGPT and Codex. With reasoning
retained, the model thought *less* per action and held a coherent strategy
across a run.

**Compaction instead of rolling truncation.** The official harness drops the
oldest messages once the conversation exceeds 175,000 characters. OpenAI's
[compaction](https://developers.openai.com/api/docs/guides/compaction) returns a
compacted window containing an encrypted compaction item that carries prior
state forward in fewer tokens. Two claimed effects: earlier observations survive,
and the run spends most of its life in a less full context window, which the
post says slightly helps on its own.

Note which of these is which. Discarding reasoning is close to a straight defect
relative to how the model was trained. Truncation versus compaction is a
**policy choice with no universally correct default** — and it is the same
decision mission 01 stage 06 makes in
[what fits in context](../01-language-model/06-agent/what-fits-in-context/),
where the policy collapses a superseded read before discarding any decision.
ARC and OpenAI picked opposite defaults, and both can defend theirs.

## (c) The disagreement the post does not resolve

ARC chose a deliberately generic harness — no tools, no vendor-specific
features — so that model shortcomings would be visible and comparisons between
models would be fair. OpenAI's closing recommendation is the opposite: use the
Responses API, retain reasoning, use compaction, and *"rely on evals that use
the settings above."*

Both positions are coherent because they measure different things.

| | ARC's generic harness | A vendor-tuned harness |
|---|---|---|
| What it measures | the model | the product |
| Comparability across vendors | high | none |
| Resemblance to deployment | low | high |
| Who can reproduce it | anyone | the vendor |

Neither is "the score." A reader who takes only one of these numbers has been
handed a claim about the model when the evidence is about the pair.

## (d) What is left open

- **The compaction item is encrypted.** What survived compaction cannot be
  audited or reproduced by anyone outside OpenAI. That is an awkward property
  for a result published in an argument about harness transparency: the harness
  is now partly proprietary.
- **7.8% and 13.3% are both called the official harness** and are not
  reconciled. One is ARC's headline figure and one is OpenAI's reproduction on
  the public set; the post does not explain the gap, and a reader comparing
  "3x" against the wrong baseline gets a different multiplier.
- **38.3% is still below the 48% human estimate**, which the post states and
  which the "tripled" framing tends to bury.
- **One game is not the benchmark.** The headline video shows a game where no
  frontier model passes level one and GPT‑5.6 Sol solves all six. That is a
  strong anecdote, not the public-set result.

## (e) What this repository can and cannot check

Nothing here is reproducible on this repo's hardware — the model is hosted and
the benchmark is not run here.

What *is* checkable, and worth doing: mission 01 stage 06's harness has the same
two variables. Its `ContextManager` policy is swappable by construction, and its
loop already logs full transcripts. Running the stage-06 agent twice against the
same served model — once with `drop_oldest_tool_results` and once with a
collapse-only policy — would produce this repository's own version of the
compaction result, at a scale where every number is measured rather than cited.
That run does not exist yet, which is why stage 06 is still `draft`.

The generalizable finding needs no run at all, and it is the one
[whose harness produced it](../01-language-model/07-eval/whose-harness/)
now carries: a score is a property of a pair, and the half nobody names is the
half that moved 3x.
