---
status: draft
level: applied
---

# Which stakeholder problem do you want to solve?

Start here, not in `foundations/`, `platform/`, or `capabilities/`. Those three
are support libraries: a mission sends you to one only at the exact point a
decision needs it, and you come back with an artifact, not a grade.

Every mission below is the same underlying claim tested against a different
domain: build one working system end to end, on real data or a disclosed
proxy for it, and refuse to claim more than the evidence supports.

## The four missions, and what each one is actually testing

**[Language-model system](01-language-model-agent/)** builds the platform
layers for the first time — corpus, tokenizer, pretraining, SFT, RL, serving,
an agent harness, evaluation — against one model, end to end. Read this one
first. Every later mission cites a chapter this mission built rather than
re-deriving it, so its stages are what "platform" means concretely before you
read the reference layer in the abstract.

**[Personalized discovery](02-personalized-discovery/)** asks whether those
layers generalize to a domain where the objective is not next-token
likelihood: ranking, with logged data confounded by the policy that produced
it, and every ad displacing an organic result. It reuses the data discipline,
training engineering, serving concerns, and evaluation discipline mission 01
built, unchanged.

**[Quantitative research](03-quantitative-research/)** is the harder version
of the same question: a domain where the data does not just sit there
confounded, it actively fights back, because a pattern a strategy finds
changes the moment enough capital trades on it. It reuses mission 01's
point-in-time data discipline and mission 02's evaluation-observability
harness, and adds purge, embargo, and multiple-testing correction because
financial evaluation needs strictly more discipline than i.i.d. held-out data,
not less.

**[Code agent](04-code-agent/)** turns the question around: instead of asking
whether a system does its job, it asks what makes an *agent's own claim* that
it did the job trustworthy — reusing mission 01's agent-loop capability
verbatim as its second consumer, which is what promotes that loop from
mission-local code to [a capability](../capabilities/act-coordinate/).

## Reading order

Mission 01 first — its stages are what the other three missions cite. After
that, 02, 03, and 04 do not depend on each other and can be read in any order;
each names exactly which platform chapters and capabilities it reuses in its
own "What this reuses" section, so you can tell what is new to that mission
and what is the same architecture wearing a different domain.

## Where a mission sends you

A mission stage links out to
[foundations](../foundations/), [platform](../platform/), or
[capabilities](../capabilities/) only at the point a decision needs the
mechanism there, and the linked chapter hands back an artifact or a
measurement the next stage consumes — never a parallel course to finish
first.
