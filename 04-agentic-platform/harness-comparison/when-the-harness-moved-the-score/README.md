---
status: draft
level: reference
label: When the harness moved the score
---

# Two settings, three times the score

> Dated survey, 2026-08-14. Sources cited inline. This chapter replaces the
> earlier `harness-effects-landscape` reference with the case in full.

**Question:** the stage claims an agent benchmark score is a function of
the model *and* the harness. The claim had no public case where someone
changed the harness alone and watched the score move. It has one now.

**The artifact this chapter follows** is OpenAI's published ARC-AGI-3
numbers, read as a harness experiment.

## The published numbers

On 2026-07-30 OpenAI posted
["How enabling two settings tripled our scores on the ARC-AGI-3 benchmark"](https://openai.com/index/how-two-settings-tripled-our-arc-agi-3-scores/):

| Setting | Score |
|---|---:|
| GPT-5.6 Sol, ARC's headline number | 7.8% |
| GPT-5.6 Sol, official harness, public set | 13.3% |
| GPT-5.6 Sol, OpenAI's harness, public set | **38.3%** |

Roughly **3x the score with 6x fewer output tokens**, from two settings,
on the same model. The harness moved the number more than the model
release did.

## What the two settings were

The two settings were harness-level: how the model was prompted and how
its outputs were scored. The official harness left the model to solve the
puzzle in one pass; OpenAI's harness gave it a structured interaction and
scored the trajectory, not the final answer. Same weights, different
software around them.

## What this changes about reading scores

A benchmark score is not a model property; it is a
model-plus-harness property. Two teams reporting different scores for
"the same model" can both be right. This is the same lesson this topic's
mission measured from the other side — the same tasks, the same model
tiers, and the harness moving delivery from 4/18 to 18/18. The external
case and the internal runs agree: the software around the model is the
independent variable.

## What this does not say

It does not say harness is everything — the model sets the ceiling, and
the cheapest tier in the mission's runs resolved 6/6 under the harness
while hiding latent defects. It says the score is a joint product, and a
score without harness disclosure is a claim with no evidence boundary.
