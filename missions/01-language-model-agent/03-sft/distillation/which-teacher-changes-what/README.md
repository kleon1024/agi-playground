---
status: verified
level: frontier
base: none
verified: 2026-08-04
label: Which teacher changes what
---

# If you swap the teacher, what actually changes in the corpus?

You have decided to generate SFT data with a model instead of paying
annotators. The next question looks easy: which model? A stronger teacher
costs more per token, so you would like to know what the extra money buys in
the corpus itself, before any student is trained on it.

**Before this:** [what you can copy from a better model](../README.md). You
need its central result — that held-out loss ranks corpora by author, not by
quality — because this chapter measures the corpora directly to avoid exactly
that trap.

The experiment is the same shape as that chapter's: hold the prompts fixed,
vary only who writes the answer. Thirty-six prompts from `no_robots`, four
from each of its nine task categories, all from the test split. Five authors:
Claude Haiku 4.5, Sonnet 5, Opus 5, Fable 5, and the dataset's own human
annotators. Nothing is trained. The corpora are measured as text.

## What one generation per arm appears to show

Count the answers containing any markdown bullet, bold span, header, or code
fence, and a clean picture arrives:

| Arm | scaffolded |
|---|---|
| haiku | 13/36 |
| sonnet | 11/36 |
| opus | 11/36 |
| fable | **2/36** |
| human | 1/36 |

Fisher exact puts each of the first three against the human arm at p ≤ 0.003.
McNemar on the paired prompts puts Fable against its siblings at 0/11, 0/9 and
0/9 discordant — there is not one prompt where Fable adds scaffolding and the
sibling does not. All of it survives a Bonferroni threshold across the seven
tests run.

The story writes itself: three Claude models share a house style, Fable does
not, and the split follows model family rather than capability tier. It is a
tidy result, it is properly computed, and it is wrong.

## What three generations per arm show

Re-run each model arm twice more, changing nothing but the dispatch:

| Arm | g1 | g2 | g3 | mean | spread |
|---|---|---|---|---|---|
| haiku | 13 | 11 | 7 | 10.3 | 6.0 |
| sonnet | 11 | 12 | 6 | 9.7 | 6.0 |
| opus | 11 | 5 | 5 | 7.0 | 6.0 |
| fable | **2** | **8** | **13** | 7.7 | **11.0** |

**Fable's rate goes 2, 8, 13.** Its third generation scaffolds more than
Haiku's third. The 2/36 that the whole story rested on was one draw from an
arm whose own generation-to-generation spread is 11 answers — wider than every
gap between arms in the table.

Apply the rule this repository uses whenever a result has seeds: a difference
counts only when the margin between arms exceeds the spread within an arm.
Largest between-arm margin, 3.3. Smallest within-arm spread, 6.0. Nothing
clears. Median answer length behaves identically — spreads of 11 to 24 words
against margins of 1.2 to 9.2.

The tests in the previous section were not miscalculated. They assumed the
within-arm variance was zero, because a design with one generation per arm
cannot see that variance at all. Correcting for multiple comparisons does not
help: no threshold repairs a variance model that is wrong by an order of
magnitude.

## The two differences that do survive

**Human answers are much shorter.** Median 58 words against 106.7 to 115.8
across the model arms. That margin of 48 to 58 words beats the largest
within-model spread of 24, on every arm, in the same direction. Concretely, on
one Classify prompt asking which genre a string of emoji suggests, the human
wrote "The category would be horror." Every model answered with the same
verdict plus a justification nobody requested, at 23 to 45 words.

**Opus text is more predictable than human text.** Scoring each corpus under a
fixed `Qwen2.5-0.5B` *base* model — not an instruct model, so it is not
aligned to any arm's chat style — Opus averages 2.7765 nats per token against
the human arm's 2.8998. The margin of 0.1234 is 3.5x Opus's own spread of
0.0351. Opus is also the steadiest arm in the run; Sonnet's mean sits close
behind but its spread is nearly five times larger, so Sonnet's gap does not
clear while Opus's does.

That is the entire list. No scaffolding difference, no between-model length
difference, no other predictability comparison, and nothing that orders by
capability tier.

## What that means for choosing a teacher

At this scale and on this prompt distribution, **teacher choice among these
four models does not measurably change the corpus.** The differences that
looked like house style were sampling noise. The one axis where a model
separates from humans by more than its own noise is verbosity, and it
separates in the same direction for all four.

This does not say a stronger teacher is worthless. It says the argument for
one cannot be made from these distribution statistics, and that anyone
choosing a teacher on the strength of a single generated corpus is reading
noise. If a teacher-choice decision matters to you, it has to be settled
downstream — by training students on each corpus and scoring them on an
author-neutral task, which is the harness the [neighbouring
chapter](../README.md) explains and still lacks.

## What the evidence does not cover

Every model answer here came from a Claude Code subagent carrying a
coding-assistant system prompt. That confound runs common-mode across the four
model arms, so the between-model comparisons stay meaningful, but it inflates
every comparison against the human arm — the scaffolding may be the harness
showing through rather than the model. The generation path also exposes no
temperature control, so the within-arm spread mixes sampling variance with
whatever else differs between dispatches.

Three generations is enough to prove the one-generation variance model wrong.
It is not enough to put a tight interval on any arm, and a spread computed
from three points is itself noisy. Nothing here judges answer quality, because
nothing judged the answers at all.

Full numbers, commands, and boundary in
[`runs/2026-08-04-four-authors.md`](../runs/2026-08-04-four-authors.md).

## Check your mental model

**1. The first pass reported p < 0.005 and survived Bonferroni correction. Why
was it still wrong?**

<details>
<summary>Answer</summary>

Because a p-value answers "how surprising is this gap, given the variance I
modelled?" and the model of variance was that there is none within an arm. One
generation per arm cannot observe generation-to-generation spread, so the test
implicitly set it to zero. Fable's own spread turned out to be 11 answers out
of 36, larger than any between-arm gap being tested. Multiple-comparison
correction adjusts for how many times you ask the question; it cannot fix
asking it against the wrong noise floor.

</details>

**2. Sonnet's mean predictability (2.7922) is closer to Opus's (2.7765) than
to the human arm's (2.8998), yet only Opus's gap against humans is reported.
Why?**

<details>
<summary>Answer</summary>

Because the margin is judged against each arm's own spread, not against the
raw distance. Opus varies by 0.0351 across its three generations, so a 0.1234
gap is 3.5x its noise. Sonnet varies by 0.1676 — larger than its own 0.1077
gap to the human arm — so Sonnet's next generation could plausibly land on the
other side of the human mean. A mean without a spread beside it cannot
distinguish these two cases, which is why the run reports both columns.

</details>

**3. You need 50,000 SFT examples and are choosing between two teachers at
different prices. What does this chapter license you to conclude?**

<details>
<summary>Answer</summary>

Nothing about which to pick. It rules out one bad way of deciding — generating
a sample corpus from each, measuring length, formatting, or entropy, and
choosing the one that looks different — because at this scale those statistics
are dominated by generation noise. The decision has to be made downstream on
an author-neutral outcome: train on each corpus and measure students on a task
with a checkable answer. What this chapter does license is skepticism toward a
teacher comparison that rests on a single generated corpus per arm.

</details>

## Next

[What path two requires](../what-path-two-requires/) prices the other route —
copying the teacher's distribution rather than its words — and explains why it
is closed to most students.
