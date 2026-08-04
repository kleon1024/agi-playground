---
status: draft
level: applied
---

# Which stakeholder problem do you want to solve?

Start here, not in `foundations/` or `platform/`. Those two are support
libraries: a mission sends you to one only at the exact point a decision needs
it, and you come back with an artifact, not a grade.

Every mission below is the same underlying claim tested against a different
domain: build one working system end to end, on real data or a disclosed
proxy for it, and refuse to claim more than the evidence supports. All nine
are built and have run their own report stage. **Several end in a result their
author would rather not have had** — a `NOT MET`, a `PARTIAL`, a null result —
which is what declaring the acceptance bar before the work is for.

## Read mission 01 first

**[Language-model system](01-language-model-agent/)** builds the platform
layers for the first time — corpus, tokenizer, pretraining, SFT, RL, serving,
an agent harness, evaluation — against one model, end to end. Every later
mission cites a chapter this mission built rather than re-deriving it, so its
stages are what "platform" means concretely before you read the reference layer
in the abstract.

## The other eight, and what each one is actually testing

**[Personalized discovery](02-personalized-discovery/)** asks whether those
layers generalize to a domain where the objective is not next-token
likelihood: ranking, with logged data confounded by the policy that produced
it, and every ad displacing an organic result. It reuses mission 01's data
discipline, training engineering, serving concerns, and evaluation discipline
unchanged. Verdict in [stage 09](02-personalized-discovery/09-report/).

**[Quantitative research](03-quantitative-research/)** is the harder version
of the same question: a domain where the data does not just sit there
confounded, it actively fights back, because a pattern a strategy finds
changes the moment enough capital trades on it. It adds purge, embargo, and
multiple-testing correction, because financial evaluation needs strictly more
discipline than i.i.d. held-out data, not less. Verdict in
[stage 05](03-quantitative-research/05-report/).

**[Code agent](04-code-agent/)** turns the question around: instead of asking
whether a system does its job, it asks what makes an *agent's own claim* that
it did the job trustworthy — reusing mission 01's agent-loop capability
verbatim as its second consumer, which is what promotes that loop from
mission-local code to [an agent harness](01-language-model-agent/06-agent/) two other missions reuse. Its
[report](04-code-agent/05-report/) returns a `PARTIAL`, and says exactly which
comparison was never run.

**[Vision-language model](05-vision-language-model/)** grafts a real
patch-embedding and vision-token fusion path onto mission 01's decoder,
importing its RoPE/RMSNorm/SwiGLU/training loop unchanged, and asks whether
the result beats a hosted VLM API and a text-only decoder answering blind. On
synthetic shapes the vision pathway separates from the blind baseline
([stage 02](05-vision-language-model/02-report/)); repeated on real
photographs against a hosted model it comes back `NOT MET`
([stage 05](05-vision-language-model/05-real-photo-report/)), and the mission
keeps both.

**[Game AI](06-game-ai/)** points mission 01's GRPO loop at a game's
win/score signal instead of arithmetic correctness, and hits the same
zero-gradient wall a cold-start policy can hit. Its
[full-chain report](06-game-ai/05-report/) records the acceptance bar as
**"MET, as an honest null result extended across two environments and one fix
attempt"** — the collapse resists the two most obvious training-signal fixes,
one of which makes it worse, and nothing was rescaled or warm-started to
manufacture a positive number.

**[Real-time voice](07-realtime-voice/)** asks whether platform/serving's
KV-cache and continuous-batching mechanics, built and measured against text,
transfer unchanged to a from-scratch audio codec's token stream. They do, with
zero quality gap between offline and streaming decode, and no change to the
reused serving code ([stage 02](07-realtime-voice/02-report/)) — then
[stage 03](07-realtime-voice/03-real-speech-and-network/) re-runs it on real
speech over a real network.

**[Video generation](08-video-generation/)** asks a feasibility question
before a quality one: does this repository's real-run, declared-compute-lane
discipline survive contact with video at all. [Stage 03](08-video-generation/03-report/)
answers yes against the frame-repeat baseline and by how much, then names the
codec ceiling the same model does *not* clear.

**[Molecular property prediction](09-bio-pharma-modeling/)** is the narrow,
runnable question underneath a much larger ask for "anti-aging/pharma"
coverage: does a small trained model beat a descriptor-based baseline on one
public toxicity label. [Stage 02](09-bio-pharma-modeling/02-report/) is
`NOT MET` — the descriptor baseline wins clearly and repeatably — and
[stage 05](09-bio-pharma-modeling/05-cross-endpoint-analysis/) takes three
endpoints and asks what the pattern across them does and does not support. It
says nothing about aging biology or drug discovery, on purpose; read its
`does_not_prove` section before reading any number out of it as more than
that.

## Reading order

Mission 01 first — its stages are what every other mission cites. After that,
02 through 09 do not depend on each other and can be read in any order; each
names exactly which platform chapters and mission-01 stages it reuses in its own
"What this reuses" section, so you can tell what is new to that mission and
what is the same architecture wearing a different domain.

If you would rather enter by decision than by domain — "how do I know the
split held", "why is my loss flat", "what does the harness owe me" — the
[read-by-topic index](https://rehearse.maestro.onl/playground/topics/) lists
every chapter in this repository under the question it answers, missions and
support libraries together.

## Where a mission sends you

A mission stage links out to [foundations](../foundations/), to
[platform](../platform/), or to an earlier mission's stage only at the point a
decision needs the mechanism there, and the linked chapter hands back an
artifact or a
measurement the next stage consumes — never a parallel course to finish
first. [Infrastructure](../infra/) sits one layer below platform: it is where
the wiring, the scheduler, and the storage layout that score those decisions
get measured.
