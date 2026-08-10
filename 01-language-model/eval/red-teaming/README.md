---
status: draft
level: applied
base: none
label: Red-teaming
---

# Where do the test cases that make a gate meaningful actually come from?

**Question:** [eval gates](../eval-gates/) answers "given a candidate's
scores on a fixed eval suite, how does a pass/fail decision get computed" —
and takes the scores as given. This chapter takes a step back to the question
the gate never asks: where did the test cases that produced those scores come
from, and why can't a fixed, one-time-authored test set alone establish that a
system resists a class of failures?

**Before this:** [eval gates](../eval-gates/), for the gate-decision
mechanism this chapter does not re-derive — a gate computes a decision from
scores; this chapter is about how you find the inputs that produce scores
worth gating on in the first place.

You will finish able to run a from-scratch adversarial search against a toy
content filter, see a real case where a search budget alone cannot substitute
for perturbation coverage, and read why "we tried N variants and found none"
is a bounded, dated claim about a search process rather than a safety proof.

## The problem a fixed test set cannot solve

A test set authored once, by people who could only think of the failures they
already imagined, tests exactly those failures and nothing past their
boundary. A system can pass every case in that set while a nearby,
undiscovered variant still breaks it — the same generalization gap
[the metric-gaming chapter](../metric-gaming/)
already names for metrics that get optimized against directly, applied here
to the test *cases* themselves rather than the score they produce.

Two distinct mechanisms close part of that gap: **manual red-teaming**, a
human adversarially probing the system with their own judgment and creativity,
and **automated red-teaming**, a search or generation process that produces
adversarial candidates programmatically — sometimes one model probing another.
Neither closes the gap completely; each only tells you what its own process
found within the time or budget it ran.

## The mechanism: search, not enumeration

[`core/adversarial_search.py`](core/adversarial_search.py) defines a toy
system under test — a keyword content filter that blocks any text containing
one of four banned substrings, case-insensitive — and a from-scratch bounded
random search: given a case the filter originally blocks correctly, try up to
`budget` independent perturbations of the banned keyword (case-flip, homoglyph
substitution, separator insertion, character duplication) and stop at the
first one that flips the filter's decision to PASS.

```
case: case-0000  keyword=forbidden_delta
original (BLOCK): Attach the forbidden_delta file to this week's summary.
flipped after 1 attempt(s): Attach the forbidden_delt4 file to this week's summary.
re-check: is_blocked=False
```

One substitution — `a` to `4` inside the banned word — is enough. The filter's
substring check never sees the banned keyword at all once one character is
swapped for a visually similar one.

## Manipulate the search budget and the perturbation space

Two different knobs control how much the search finds: how many attempts it
gets, and how many distinct perturbation operators it may draw from.

<!-- interactive: AdversarialSearchSweep -->

## The observed consequence: budget and coverage are not substitutes

Over 500 synthetic cases (all four operators available):

```
  budget  flip_rate   mean_attempts_when_flipped
       1      0.706                         1.00
       2      0.924                         1.24
       5      0.996                         1.38
      10      1.000                         1.40
      20      1.000                         1.40
      50      1.000                         1.40
     100      1.000                         1.40
```

Flip rate saturates at 100% by budget 10, and the mean number of attempts
needed when a flip happens barely moves past budget 2 — this toy filter is
trivially easy to evade once *any* effective perturbation is tried.

Now hold budget fixed at 20 and vary how many operators the search may use:

```
n_operators  flip_rate
          1      0.000
          2      1.000
          3      1.000
          4      1.000
```

Operator-space size 1 means only `op_case_flip` is available. Its flip rate is
exactly zero — not low, zero — and stays zero even at a budget of 1000, fifty
times the budget where the full operator set already saturates:

```
budget=    1 case-flip-only flip_rate=0.000
budget=   10 case-flip-only flip_rate=0.000
budget=  100 case-flip-only flip_rate=0.000
budget= 1000 case-flip-only flip_rate=0.000
```

The filter lowercases text before matching, so a pure case-flip can never
change its decision on this system, no matter how many times it's tried. A
search budget cannot compensate for a perturbation space that misses the one
operator the system under test is actually vulnerable to — full numbers:
[`runs/2026-08-02-adversarial-search-sweep.md`](runs/2026-08-02-adversarial-search-sweep.md).

## A brief history

Perez et al., "Red Teaming Language Models with Language Models"
(arXiv, February 2022; published EMNLP 2022) is a foundational demonstration
of *automated* red-teaming: one language model generating test inputs to
discover a second model's failures, rather than a human authoring them by
hand. Ganguli et al., "Red Teaming Language Models to Reduce Harms: Methods,
Scaling Behaviors, and Lessons Learned" (Anthropic, arXiv, August 23, 2022) is
the human-red-teaming-at-scale counterpart, studying how manual adversarial
probing scales with model size and what that reveals about the harms found.
This repository's own [AgentDojo citation](../../06-agent/what-stops-it/)
(Debenedetti et al., June 2024) is a concrete instance of the same idea applied
to a different system under test — an agent harness rather than a chat model —
turning "an agent's observations can carry adversarial instructions" into a
benchmark of adversarial test cases rather than a single anecdote.

## The fix and its trade

The failure mode is a fixed test set: authored once, by people who could
only think of the failures they already imagined, it tests exactly those
failures and nothing past their boundary — a system can pass every case
while a nearby, undiscovered variant still breaks it. The measured
demonstration is sharp: over 500 synthetic cases, the toy filter's flip
rate saturates at 100% by budget 10 (mean ~1.4 attempts when a flip
happens), yet a perturbation space of size 1 — case-flip only — flips
*zero* cases at every budget up to 1000, because the filter lowercases
before matching and no case-only perturbation can ever change its decision.
Budget cannot compensate for operator coverage: the binding constraint is
which perturbation operators the search may draw from, not how many attempts
it gets.

The fix is the pair — manual red-teaming (a human adversarially probing the
system) plus automated adversarial search (a bounded search or generation
process producing candidates programmatically) — and the conclusion
discipline that turns a clean sweep into a bounded claim: "we tried N
variants and found none" is a real, dated statement about the search
process that ran, and never a robustness proof, because a search
structurally incapable of the one operator that defeats the system returns
0.000 at any budget. The trade is that each method only tells you what its
own process found within its time and budget — neither closes the
generalization gap completely — and the operator space has to be shaped by
the system under test, which makes every red-teaming result versioned with
the search that produced it. The approaches are dated and external: Perez
et al., automated red-teaming of one model by another (arXiv, February
2022; EMNLP 2022); Ganguli et al., human red-teaming at scale and how it
scales with model size (Anthropic, arXiv, August 23, 2022); and this
repository's own AgentDojo citation (Debenedetti et al., June 2024) applies
the same idea to an agent harness. The production gap is named: real
automated red-teaming generates thousands to millions of candidates, and
this toy's 500 cases and four hand-written operators demonstrate the
mechanism, not the budget a production red-teaming effort requires.

## Who owns the loop

- **The safety-evaluation team** owns the test-case generation process:
  the automated search and the manual red-teaming rounds, and the operator
  coverage that decides whether budget buys anything — the chapter's
  0%-then-100% jump between operator-space sizes 1 and 2 is the
  demonstration of how narrow that boundary can be.
- **The data team** owns the case library and its dating: a clean sweep is
  a bounded, dated claim about a search process, so the case set is
  versioned with the perturbation space and budget that produced it.
- **The model team** owns the response to a discovered failure: a flipped
  case is a training-data or guardrail signal, and the eval gate consumes
  it as a new test case rather than a one-off anecdote.
- **The release team** owns the escalation chain — enforcement point, audit
  record, escalation owner — that turns a discovered failure into a stopped
  deployment, which is the link red-teaming itself does not make.

## What this does not establish

- **Nothing about a real language model's jailbreak resistance.** The system
  under test here is a four-keyword substring filter — smaller and simpler
  than any real content-moderation or safety-classification system by
  construction.
- **Nothing about adversarial robustness in general.** A "0 successful flips"
  result in this toy, or in any real red-teaming exercise, is a claim bounded
  to the specific perturbation space and search budget actually tried — it is
  never a general robustness proof, and this chapter's own 0%-then-100% jump
  between operator-space sizes 1 and 2 is the demonstration of exactly how
  narrow that boundary can be.
- **Nothing about a filter that defends against this exact attack.** A system
  that normalized homoglyphs or checked edit distance instead of exact
  substrings would need a different search entirely — this script's operators
  are shaped around the one toy filter it targets, not a general adversarial
  toolkit.
- **Nothing about coverage or cost at production scale.** Real automated
  red-teaming (as in Perez et al.) generates thousands to millions of
  candidates against a genuinely large model; this toy's 500 cases and four
  hand-written operators are for demonstrating the mechanism, not measuring
  what a production red-teaming budget requires.

## Check your mental model

**1. Why does "the filter passed every test in our test set" not establish that it resists this class of failure?**

<details>
<summary>Answer</summary>

Because a fixed test set only ever contains the failures its authors already
thought to write down. This chapter's own toy filter passes every case in its
original, correctly-blocked test set by construction — the gap only becomes
visible once an adversarial search actively looks for a *nearby* variant the
authors didn't enumerate. At operator-space size 2 and budget 10, 100% of
those originally-blocked cases flip to PASS under a one-character
substitution the original test set never tried. Passing a fixed set proves
the system handles exactly those cases; it says nothing about the neighbor
one perturbation away.

</details>

**2. Why does flip rate jump from 0% to 100% between operator-space size 1 and size 2, rather than rising gradually?**

<details>
<summary>Answer</summary>

Because the filter is invariant to the one operator available at size 1
(`op_case_flip`) for a structural reason — it lowercases text before matching,
so no case-only perturbation can ever change its decision, at any budget.
Adding the second operator (homoglyph substitution) introduces the first
perturbation the filter is *not* invariant to, and once that operator is
available the search finds a flip almost immediately (mean ~1.4 attempts).
The jump isn't gradual because the underlying capability isn't gradual: either
the search has access to an operator that can actually defeat the filter's
specific check, or it doesn't.

</details>

**3. A red-teaming process runs and finds zero successful attacks. What can and can't you conclude?**

<details>
<summary>Answer</summary>

You can conclude the system withstood every case that specific process
generated, within the specific perturbation space and budget it used — a
real, dated, bounded result. You cannot conclude the system is robust in
general: this chapter's own case-flip-only sweep is exactly that scenario —
0.000 flip rate at every budget up to 1000 — and that result says nothing
about robustness, because the search was structurally incapable of finding
the one perturbation (homoglyph substitution) that defeats the filter
completely. A clean sweep is a claim about the search that ran, not a proof
about the system searched.

</details>

**4. What is the actual difference between what this chapter tests and what an eval gate ([eval gates](../eval-gates/)) tests?**

<details>
<summary>Answer</summary>

An eval gate takes candidate scores as given and computes a pass/fail
decision from a declared threshold rule — its entire mechanism assumes the
scores it's gating on already exist. This chapter is about how those scores
get produced in the first place: which test cases were run against the
system to generate them. A gate can be computed perfectly correctly and still
gate on a test suite that never included the adversarial variant that
actually breaks the system — the two chapters answer different questions in
the same pipeline, one downstream of the other, and neither substitutes for
the other.

</details>

## Next

Automated red-teaming at real scale needs its own generation model (as in
Perez et al.) or its own scaling study (as in Ganguli et al.) — neither has a
from-scratch `core/` chapter here yet. [The release chain](../who-decides-to-ship/)
names the remaining links — `enforcement point -> audit record -> escalation
owner` — that turn a discovered failure into a stopped deployment, which is
also outside this chapter's scope.

Primary references: Perez et al., *Red Teaming Language Models with Language
Models* (arXiv, February 2022; EMNLP 2022); Ganguli et al., *Red Teaming
Language Models to Reduce Harms: Methods, Scaling Behaviors, and Lessons
Learned* (Anthropic, August 23, 2022); Debenedetti et al., *AgentDojo* (June
2024), cited here via [what stops it?](../../06-agent/what-stops-it/).
