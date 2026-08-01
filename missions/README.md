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

## The four built missions, and what each one is actually testing

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

## Five more missions, contract declared and stages not yet built

Per [the mission contract](../reference/standards/mission-contract.md), no mission is
built before its `mission.yaml` and stage table exist — so these five are
listed here in that declared-only state, not because their pages are
finished. Each reuses code from the four missions above rather than
reimplementing it; each names exactly what it does and does not claim before
a single stage has run.

**[Vision-language model](05-vision-language-model/)** grafts a real
patch-embedding and vision-token fusion path onto mission 01's decoder,
importing its RoPE/RMSNorm/SwiGLU/training loop unchanged, and asks whether
the result beats a hosted VLM API and a text-only decoder answering blind.

**[Game AI](06-game-ai/)** points mission 01's GRPO loop at a game's
win/score signal instead of arithmetic correctness, and watches for the same
zero-gradient wall a cold-start policy can hit — a null result here is as
real an outcome as a win.

**[Real-time voice](07-realtime-voice/)** asks whether platform/serving's
KV-cache and continuous-batching mechanics, built and measured against text,
transfer unchanged to a from-scratch audio codec's token stream, or whether
audio demands new serving mechanism the text case never needed.

**[Video generation](08-video-generation/)** asks a feasibility question
before a quality one: does this repository's real-run, declared-compute-lane
discipline survive contact with video at all, given a clip is dozens of
frames each costing what one image does. Sequenced last among the new
systems tracks because it needs the most new code and may need the Modal
lane rather than the local GPU lane every other mission has used so far.

**[Molecular property prediction](09-bio-pharma-modeling/)** is the narrow,
runnable question underneath a much larger ask for "anti-aging/pharma"
coverage: does a small trained model beat a descriptor-based baseline on one
public, checkable toxicity label. It says nothing about aging biology or
drug discovery, on purpose — see its `does_not_prove` section before reading
any number out of it as more than that.

## Reading order

Mission 01 first — its stages are what the other three built missions cite.
After that, 02, 03, and 04 do not depend on each other and can be read in any
order; each names exactly which platform chapters and capabilities it reuses
in its own "What this reuses" section, so you can tell what is new to that
mission and what is the same architecture wearing a different domain.
Missions 05 through 09 are declared but not yet built; read their
`mission.yaml` files to see what each one will and will not claim once it is.

## Where a mission sends you

A mission stage links out to
[foundations](../foundations/), [platform](../platform/), or
[capabilities](../capabilities/) only at the point a decision needs the
mechanism there, and the linked chapter hands back an artifact or a
measurement the next stage consumes — never a parallel course to finish
first.
