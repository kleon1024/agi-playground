---
status: draft
level: applied
---

# Which lifecycle decision do you actually need?

Six areas, not a course. `platform/` is reference material for the choices
that recur no matter which mission you are running, and you arrive here from
a mission stage that named exactly which decision it needs — read that
chapter, take the artifact or measurement back, and return to the mission.
Reading all six front to back before starting a mission answers questions you
do not have yet.

If you know the decision but not which of the six owns it, the
[read-by-topic index](https://rehearse.maestro.onl/playground/topics/) lists
every chapter in this repository — platform, missions, foundations,
infrastructure — under the question it answers.

## The lifecycle order, when you are tracing one model

Four of the six sit on one line, because each produces the input the next one
needs:

```text
data -> training -> adaptation -> serving
```

**[Data](data/)** turns a raw crawl into a corpus with a manifest and
disclosed rejection reasons. **[Training](training/)** turns that corpus and a
token budget into a base checkpoint. **[Adaptation](adaptation/)** — four
chapters, not one, entered by question rather than in sequence — closes the
gap between a checkpoint that predicts text and one that follows instructions,
has preferences, or has learned a new capability by exposure. **[Serving](serving/)**
turns an adapted checkpoint into a service with a request lifecycle and a
latency budget.

## The two that are not on that line

**[Evaluation and observability](evaluation-observability/)** is not the
final stage of the chain above — every mission's own report stage
(`missions/01-language-model-agent/07-eval/`,
`missions/02-personalized-discovery/09-report/`,
`missions/03-quantitative-research/05-report/`) needs the same variance and
disclosure discipline this chapter teaches, at whatever point that mission
is ready to make a claim. **[Safety and governance](safety-governance/)** is
the same shape of cross-cutting: it is what turns a `mission.yaml` guardrail
from a sentence into something enforced, and a mission reaches for it the
moment a guardrail needs a real enforcement point, not only at the end of a
build.

[Mission 01's agent harness](../missions/01-language-model-agent/06-agent/) sits adjacent to both, for the
same reason: it is what a model needs around it before it can act at all, and
it is entered from serving (a model that cannot be called cannot act) on the
way to evaluation (which then has to judge the harness, not only the model).
It stays in the mission that built and measured it; two other missions reuse
it from there.

## Before this, and where this returns to

[Foundations](../foundations/) is the prerequisite mechanism underneath the
first two areas — the decoder block underneath training, nothing underneath
data. Every one of the six areas above is entered from, and returns to, a
[mission](../missions/) stage; none of them is a stakeholder outcome on its
own.
