---
status: draft
level: frontier
base: none
label: Agentic infrastructure
---

# Under the platform, what does the machine room look like?

**Question:** the control plane governs a fleet, but the fleet runs on
something physical: machines that serve inference, run sandboxes, hold
memory, and log everything. This stage is the machine room. And this
mission already has one — a 24GB card running the whole loop, from model
serving to sandbox to SQLite memory, at \$0 marginal cost per attempt.
That card is the smallest honest instance of every layer the cloud vendors
now sell as named products. What are those layers, and what breaks when
they are under-provisioned?

**The artifact this stage follows** is the six-layer map, drawn with the
mission's own compute reality as the smallest instance of each layer
([the-compute-reality](the-compute-reality/),
[the-six-layers](the-six-layers/)). The map is the stage's spine: every
cloud offering below is the same six questions, answered at fleet scale.

**Before this:** [stage 12](../control-plane-and-governance/) defined the
policy layer. This stage is the substrate under it.

## The six layers, and the question each one answers

Under a production agent sit six things, and each one answers a question
the platform cannot avoid ([the-six-layers](the-six-layers/)):

| Layer | The question | The mission's miniature |
|---|---|---|
| Inference | where does the model run? | the locally-served open-weights model on the 24GB card |
| Sandbox execution | where does the agent's code run? | the subprocess sandbox from [stage 07](../execution-environment/) |
| Data and memory | where does state live? | the SQLite store from [stage 09](../context-and-memory/) |
| Tool registries | where are tools discovered? | the tool protocol from [stage 10](../tools-and-protocols/) |
| Observability | what happened? | the recorded runs, every one with its command and cost |
| Evaluation | was it right? | the scoring harness from [stage 00](../task-set/) |

The point of drawing the mission's card as all six layers is that the
layers are separable even when they share one machine. The mission did not
build "an agent"; it built inference, a sandbox, a store, a protocol, a
log, and a scorer, and the loop composes them. Production does the same
composition across machines — which is why the cloud vendors can sell each
layer separately.

## The cost model inverts

The industry observation that makes this stage concrete: in the agentic
era, the dominant cost line is not model tokens
([the-compute-reality](the-compute-reality/)). It is orchestration and
sandbox compute — machines sitting idle waiting for an agent to decide,
sandboxes created and destroyed per task, and inference that runs
*between* tool calls rather than once. The mission's own numbers show the
shape: the recorded attempts spend 60–200 seconds of wall-clock on a few
dollars of tokens, and the wall-clock is the throughput constraint — a
maintainer can push through only so many tasks in a working day
([mission.yaml](../mission.yaml)).

## Where the budget goes, and the bottleneck nobody plans for

Two consequences follow ([sandbox-farms](sandbox-farms/),
[agentic-devops](agentic-devops/)).

First, sandbox provisioning becomes a throughput variable. A fleet of
parallel agents needs sandboxes faster than agents need models — E2B's
microVM pools quote 150–200 ms cold starts precisely because that number
is the fleet's clock tick, and the self-hosted-versus-managed decision is
a break-even on that axis.

Second, the bottleneck for parallel agents is often CI, not inference.
OpenAI's own stack reports the same inversion: orchestration and sandbox
compute moved to the dominant cost line, and CI speed became the thing
that limits how many agents can work at once. An agent that finishes a
patch in 60 seconds and waits 10 minutes for the test pipeline is not a
parallel agent. The mission's local lane sidesteps this by running its own
tests on the same machine — a luxury a fleet does not have.

## The gateway, and the honest boundary of the local lane

Two more layers deserve attention. The model gateway
([model-gateways](model-gateways/)) is where model choice becomes a config
change — routing, fallback, caching, key management — which is the
infrastructure version of the mission's tier routing decision in
[stage 05](../cheap-or-expensive/): the same task, the same code, a
different model behind one interface.

And the honest boundary: a 24GB card can run this mission's loop, but it
cannot run everything, and the repository's rule is the same rule that
binds this stage — if a model does not fit the local lane, do not train a
reduced model and present it as evidence; link dated external sources
instead ([the-compute-reality](the-compute-reality/)). The local lane is
the smallest honest machine room, and its boundary is where the industry's
machine rooms take over.

## What this stage does and does not establish

It establishes the map: six separable layers, the cost inversion, and the
CI bottleneck, anchored to the mission's own compute reality as the
smallest instance of each layer. This is a reading stage by design — no
new runs are planned, and the production claims are dated surveys with
sources cited.

It does not claim the 24GB card scales — it is the honest minimum, and
scaling it is exactly what the surveyed platforms sell. And it does not
claim infrastructure is the interesting part of an agent; it claims
infrastructure is the part that decides whether the interesting parts can
run at fleet scale at all.

**Next:** the machine room exists. The question is which industries can
actually stand its cost — [industry impact](../industry-impact/).
