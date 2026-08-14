---
status: draft
level: reference
label: LLM-as-judge reliability
---

# When a judge can be trusted, and when it is part of the problem

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the a-minimal-judge demo showed a signal-reading judge
accepting a tampered patch. The industry has quantified how unreliable
judges can be — and how to make them reliable enough to use. What is the
evidence, and what are the fixes?

## The unreliability record

LLM-as-judge evaluations can be gamed, and benchmark gaming is
systematic: a 2026 UC Berkeley study showed all eight major agent
benchmarks could be gamed to near-perfect scores without solving the
tasks ([TokenJam evaluation layer](https://tokenjam.dev/blog/2026-05-26-the-9-layer-agent-ecosystem-map)).
Judge-specific studies (RuVerBench and related work) measure judge
reliability against human agreement and find systematic biases — judges
that prefer their own output, reward verbosity, or miss structural
failures.

## The fixes

**Rule verifiers for structural properties** — a patch touching a test
file is verifiable by rule, not by judgment (the mission's guardrail).

**Judge-with-rubric and reference answers** — Spotify's Honk used an
LLM-as-judge verification loop successfully, and its early experience
showed rigid judging blocked valid changes before the rubric improved
([QCon coverage](https://www.infoq.com/news/2026/03/spotify-honk-rewrite/)).

**Measured corpora** — review agents need a corpus of misses, expected
findings, and difficult examples, with precision, recall, override rate,
and downstream escapes tracked (Cursor's Bugbot).

## What this means for this topic

The stage's verified core is the rule-verifier end; this chapter prices
the judge end. The mission's honesty contract — never-firing is not proof
of safety — is the same skepticism applied to judge scores.

## What this does not say

It does not claim judges are unusable — it claims they need rubrics,
measurement, and rule verification beside them. It maps when each is
trustworthy.
