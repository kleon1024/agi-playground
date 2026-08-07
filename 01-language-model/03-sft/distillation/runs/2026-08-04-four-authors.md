# Four teachers, one prompt set: the effect that vanished when seeds were added

Thirty-six held-out prompts, answered by four Claude models and one set of
human annotators. Three independent generations per model arm. The question
was whether teacher choice changes the corpus you get, and whether that
change tracks model capability.

The first pass ran one generation per arm and found a large, clean effect at
p < 0.005. The second pass ran three, and the effect disappeared into
generation-to-generation variance. Both passes are recorded here, because the
gap between them is the finding.

## Commands

```bash
# the fixed prompt set: 4 per category x 9 categories, no_robots test split
python core/build_prompt_set.py --split test --per-category 4 \
    --out fixtures/four-authors/prompts.json

# each arm answers the same 36 prompts; 3 generations per model arm.
# answers were produced by Claude Code subagents, one dispatch per generation,
# each given fixtures/four-authors/prompts.json and no other repository file.
# the human arm is the no_robots reference answer, which cannot be regenerated.

python core/measure_authors.py          # length, structure, spread verdicts
python core/score_predictability.py     # mean NLL under a fixed base scorer
```

## Environment

| | |
|---|---|
| Prompt set | `HuggingFaceH4/no_robots`, test split, single-turn rows only |
| Prompts | 36 — four each from Brainstorm, Classify, Closed QA, Coding, Extract, Generation, Open QA, Rewrite, Summarize |
| Model arms | Claude Haiku 4.5, Sonnet 5, Opus 5, Fable 5 — three generations each |
| Human arm | the dataset's own annotator answers, one generation by construction |
| Generation | Claude Code subagents, identical brief, no temperature control available |
| Scorer | `Qwen/Qwen2.5-0.5B` — a **base** model, not instruct, held fixed across arms |
| Scoring hardware | local lane, one 24GB card, WSL2 kernel 6.18.33.2 |
| Scoring wall-clock | under 2 minutes for all 13 corpora |
| Cost | \$0 for scoring (local hardware); generation billed as normal model usage |

## Pass one: one generation per arm

Answers containing any markdown bullet, bold span, header, or code fence:

| Arm | rate | Fisher exact vs human |
|---|---|---|
| haiku | 13/36 | 0.00058 |
| sonnet | 11/36 | 0.00298 |
| opus | 11/36 | 0.00298 |
| fable | **2/36** | 1.00000 |
| human | 1/36 | — |

McNemar on the paired prompts put Fable against its siblings at 0/11, 0/9 and
0/9 discordant — perfectly one-directional, p = 0.001 to 0.004. Every result
survived a Bonferroni threshold of p < 0.0071 across the seven tests run. The
reading at the time: Fable patterns with the human corpus, its three siblings
do not, and the split is by model family rather than capability tier.

## Pass two: three generations per arm

| Arm | g1 | g2 | g3 | mean | spread |
|---|---|---|---|---|---|
| haiku | 13 | 11 | 7 | 10.3 | 6.0 |
| sonnet | 11 | 12 | 6 | 9.7 | 6.0 |
| opus | 11 | 5 | 5 | 7.0 | 6.0 |
| fable | **2** | **8** | **13** | 7.7 | **11.0** |
| human | 1 | — | — | — | (one generation) |

**Fable's rate went 2, then 8, then 13.** Its third generation scaffolds more
than Haiku's third. The 2/36 that anchored pass one was one draw from an arm
whose own spread is 11 — wider than any gap between arms.

Applying the margin-over-spread rule this repository uses for seeded results:

| Comparison | margin | spread | verdict |
|---|---|---|---|
| haiku vs sonnet | 0.7 | 6.0 | does not clear |
| haiku vs opus | 3.3 | 6.0 | does not clear |
| opus vs sonnet | 2.7 | 6.0 | does not clear |
| fable vs haiku | 2.7 | 11.0 | does not clear |
| fable vs sonnet | 2.0 | 11.0 | does not clear |
| fable vs opus | 0.7 | 11.0 | does not clear |

Median answer length behaves the same way — within-arm spread 11 to 24 words,
between-arm margins 1.2 to 9.2, nothing clears:

| Arm | g1 | g2 | g3 | mean | spread |
|---|---|---|---|---|---|
| haiku | 113 | 114 | 103 | 110.0 | 11.0 |
| sonnet | 122 | 103 | 123 | 115.8 | 20.0 |
| opus | 119 | 95 | 106 | 106.7 | 24.0 |
| fable | 122 | 106 | 105 | 111.2 | 17.5 |
| human | 58 | — | — | — | (one generation) |

## Predictability under a fixed base scorer

Mean per-token NLL of the answer text alone. Lower means more predictable to a
model that never saw any of it — not better.

| Arm | g1 | g2 | g3 | mean | spread |
|---|---|---|---|---|---|
| human | 2.8998 | — | — | 2.8998 | — |
| haiku | 2.8820 | 2.8129 | 2.8121 | 2.8357 | 0.0698 |
| sonnet | 2.8807 | 2.7131 | 2.7827 | 2.7922 | 0.1676 |
| opus | 2.7715 | 2.7614 | 2.7965 | **2.7765** | **0.0351** |
| fable | 2.8910 | 2.8115 | 2.8667 | 2.8564 | 0.0795 |

| Comparison | margin | spread | verdict |
|---|---|---|---|
| opus vs human | 0.1234 | 0.0351 | **CLEARS** |
| haiku vs human | 0.0642 | 0.0698 | does not clear |
| sonnet vs human | 0.1077 | 0.1676 | does not clear |
| fable vs human | 0.0434 | 0.0795 | does not clear |
| fable vs opus | 0.0799 | 0.0795 | clears by 0.0004 — not reportable |
| all other model pairs | 0.016–0.059 | 0.070–0.168 | does not clear |

Opus is both the most predictable arm and the most *consistent* one, with a
spread less than half of any other arm's. That consistency is what lets its
margin clear; Sonnet's mean is close behind but its spread is nearly five
times larger.

The `fable vs opus` row clears by four ten-thousandths. A margin/spread ratio
of 1.005 is not a result, and it is recorded here as not reportable rather
than quietly counted as a sixth finding.

## What clears the bar

**Human answers are shorter than every model arm's.** Median 58 words against
106.7–115.8. The margin of 48–58 words exceeds the largest within-model spread
of 24, on every arm, in the same direction.

**Opus text is more predictable than human text**, by 0.1234 nats against its
own spread of 0.0351 — a margin 3.5x the spread.

Nothing else. No scaffolding difference, no between-model length difference,
no other predictability comparison, and no ordering that tracks capability
tier anywhere in the run.

## What this does not establish

**Nothing about answer quality.** No arm was judged by anything. These are
distribution statistics, and a corpus is not better for being longer, shorter,
or more surprising.

**Nothing about raw model behavior.** Every model answer came from a Claude
Code subagent carrying a coding-assistant system prompt. That confound is
common-mode across the four model arms but inflates every comparison against
the human arm. A direct API run with an empty system prompt would answer a
different question, and was not run.

**No temperature control.** The generation path exposes no temperature knob,
so the within-arm spread reported here mixes sampling variance with whatever
else varies between dispatches. It is a real bound on reproducibility, not a
clean sampling-variance estimate.

**Three generations is few.** A spread computed from three points is itself
noisy. Three is enough to show that pass one's variance model was wrong; it is
not enough to put a tight interval on any arm.

**36 prompts, one prompt distribution, English only.** Four rows per category
across nine categories. A per-category median rests on four answers.

**One scorer.** `Qwen2.5-0.5B` is one 0.5B base model's opinion of what is
predictable. The distillation run next door used the 88M checkpoint and got
different absolute numbers, so nothing here is comparable across the two runs
in absolute terms — only within this run, across rows.

Raw records: [`seeded-results.json`](seeded-results.json) (scaffolding rates
and median lengths per generation), [`ppl-seeded.json`](ppl-seeded.json)
(per-generation mean NLL). The 13 corpora themselves are checked in under
`01-language-model/03-sft/distillation/fixtures/four-authors/`.

## Notes

Two generation arms wrote their JSONL by way of a small Python file holding
their prose as string literals rather than calling Write directly. Inspected
both: the answers are the model's own text and the script is a serialization
step, not a template. No arm was excluded for it.

The single-generation pass is kept above rather than deleted. It was correctly
computed and wrong, which is the more useful thing to be able to point at: the
Fisher and McNemar tests treated within-arm variance as zero, and correcting
for multiple comparisons does not repair a variance model that is wrong by an
order of magnitude.
