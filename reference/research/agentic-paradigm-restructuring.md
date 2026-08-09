---
level: reference
---

# The agentic paradigm restructuring (2026)

> Research pass conducted 2026-08-08; sources linked inline and dated. This is
> a survey of published external results, not a run. No number below was
> measured in this repository, and the last section says which of these claims
> the repo could check.

## What the pass was asked to find

The question behind this pass: when an agent can transact, does the agentic
turn *restructure* the decision-loop industries — risk control, search, ads,
recommendation — or only add a layer on top of the loops they already run?
The answer the evidence supports is a split:

- **Restructuring where the loop can absorb the agent.** Search, ads, and
  commerce are moving their decision surface from a ranked list into a
  conversational loop, and the loop changes which mechanisms are load-bearing.
- **Layering where the incumbent discipline is the constraint.** Risk control
  keeps its rules and its reconciliation; the agentic turn adds an agent layer
  *inside* that discipline. Recommendation keeps its ranking machinery and
  adds reasoning and verification around it.

The rest of this survey goes surface by surface, starting with risk control,
because the agentic risk-control literature is the clearest statement of the
pattern every other surface needs: **an agent that acts must be reconciled**.

## (a) Risk control: the pattern to copy

Risk control is where the agentic turn is least forgiving, because the agent
does not recommend an action — it *is* the action, and the cost of a wrong one
is a real loss. Three 2026 results show the same architecture emerging from
three independent groups.

**A hybrid multi-agent system for early scam detection in crypto-assets**
([MDPI Applied Sciences 16(7):3122, 2026-03-23](https://www.mdpi.com/2076-3417/16/7/3122))
decomposes the decision into a **Heuristic agent** (fast rules), a
**Compliance agent** (regulatory rules, modeled on the EU MiCA regime), and an
**On-Chain agent** (transaction graph signals), with a **Reconciliator** that
owns the final verdict. Three details are worth copying, and they are the same
three details the harness chapters in this repo need:

| Detail | What it does |
|---|---|
| JSON schema + strict deterministic decoding | the agents can only emit structured output; free text is not a verdict |
| Non-conforming outputs rejected and re-queried | a malformed verdict is a retry, not a pass-through |
| Modular compliance layer | regulatory rules live in a separate component, so a rule change is not a model retrain |

**SAGE** ([arXiv 2606.08146, 2026-06-05](https://arxiv.org/abs/2606.08146)) is
an LLM-driven self-reflective framework for fraud detection: three dedicated
agents (data, analysis, decision) walk a six-layer **Data Diagnostic Tree**,
and the decision process is modeled as a Markov decision process whose
"gradients" are natural-language critiques from a reflection agent. The
transferable idea is not the tree — it is that **the failure cases are named
and enumerated before the model is asked to decide**, which is the same move
the repo's failure-taxonomy detours make for the code-fixing loop.

**When AI agents collude online** ([ICLR 2026](https://iclr.cc/virtual/2026/poster/10008753),
[code](https://github.com/zheng977/MutiAgent4Fraud), 2026-02-05) simulates
financial-fraud agent networks on social platforms (MAFF-Bench) and finds the
adversarial result the other two papers assume away: **malicious agents adapt
to mitigations**. Content-level, agent-level, and societal-level defenses all
get "adapted to". The lesson is that a risk-control agent is a standing
adversary relationship, not a one-time deployment.

What this means for the agentic-platform chapters: the risk-control pattern
*is* the control-plane pattern. Schema-constrained output, rejection and
re-query, a reconciliation owner, named failure modes, and an assumed
adversary are exactly the approval-gate and governance mechanisms the platform
chapters need — the difference is only who sets the guardrails.

## (b) Search: the surface that changed first

Search is the surface where the restructure is furthest along, because the
incumbent loop was already a query-and-answer machine. Google's I/O 2026
([developer keynote](https://developers.googleblog.com/all-the-news-from-the-google-io-2026-developer-keynote/),
[Ars Technica, 2026-05-19](https://arstechnica.com/ai/2026/05/buckle-up-google-is-set-to-remake-search-with-agentic-ai-in-2026/))
folded AI Mode and AI Overviews into one conversational experience powered by
Gemini 3.5 Flash. The published scale, as of that date: AI Mode passed **1
billion monthly users** and AI Overviews **2.5 billion**. The same pass
announced Antigravity as the harness for search agents, which is the repo's
own ARC-AGI-3 finding (a harness change moved a score) applied to a consumer
surface.

What changes structurally:

- The unit of output moves from ten links to a synthesized answer with
  citations; the ranked list survives *behind* the answer as the retrieval
  layer, which is the repo's mission-02 cascade, not a new machine.
- The user's next action moves from clicking a link to asking a follow-up in
  the same thread. Session recovery — the mechanism mission 02's search
  chapters measure on a real query log — becomes the *primary* engagement
  metric, not a diagnostic.
- Measurement moves from click-through on a result page to answer engagement,
  follow-up rate, and task completion. CTR is still measured, but it is no
  longer the thing the loop optimizes.

What persists: relevance, freshness, ranking, and the economics of intent.
The agent did not remove the ranking problem; it moved the ranking inside the
answer-generation loop.

## (c) Ads: intent monetized inside the answer

OpenAI announced sponsored messages in ChatGPT on
[2026-01-16](https://www.cnbctv18.com/technology/openai-to-test-targeted-ads-in-chatgpt-stepping-up-revenue-push-19822755.htm)
(CNBC: targeted ads for logged-in free users and the \$8/month "Go" plan,
with paid tiers ad-free), launched in February 2026. The published numbers, as
reported in May 2026: initial **CPM of \$60** and a **\$250,000 minimum
spend** — a premium surface priced for brand budgets, not the programmatic
tail.

The structural change for the ads chapter: the ad is no longer a separate
object beside the content — it is a step in the same conversational loop the
user is already in. That has three consequences for the auction and
measurement machinery mission 02 documents:

1. The auction still runs, but the surface is a thread; the budget-pacing
   and throttling mechanisms survive, and latency tolerance shrinks.
2. Attribution changes shape. A user who asks for a flight and is shown an
   answer with a booking offer is at a different point in the funnel than a
   user clicking a banner, and the conversion event may now be an
   agent-authorized action (next section).
3. The multi-target seesaw the repo's recommendation chapters analyze — one
   target up, another down, and who decides — reappears as the ad-versus-
   utility trade inside a single answer.

## (d) Payments: the enabling layer

On 2026-06-10 Mastercard launched **AP4M** (Agent Pay for Machines)
([Nasdaq](https://www.nasdaq.com/articles/can-launch-ap4m-strengthen-mas-position-ai-powered-commerce)):
agent-specific credentials ("Agentic Tokens") that let one agent authorize a
payment on behalf of a user across providers. Visa and OpenAI announced
tokenized agent payments the same day. This is the layer that turns a
recommendation or an ad into a completed transaction without a human click —
and it is why the governance problem in (a) stops being theoretical: an agent
with a payment credential is a standing target, which is exactly the
adversary framing MAFF-Bench simulates.

## (e) Recommendation: reasoning over the ranked list

The generative-recommendation literature is where the restructure is most
explicit, because it replaces the ranked list itself. Four 2026 results, all
verified:

| Result | Date | What it does |
|---|---|---|
| [OneRec-Think](https://aclanthology.org/2026.acl-long.123/) (ACL 2026) | 2026 | unifies dialogue, reasoning, and personalized recommendation; adds a recommendation-specific reward that accounts for the multi-validity of user preferences |
| [Verifiable reasoning for LLM-based generative recommendation](https://arxiv.org/abs/2603.07725) | 2026 | reason-verify-recommend: verifiers interleaved with reasoning, so the generated recommendation is checked before it is shown |
| [RAG-LLM-RS / RPRAG-LLM-RS](https://www.sciencedirect.com/science/article/abs/pii/S0957417426001958) (ESWA) | 2026-01-22 | retrieval-generation-feedback modular framework: collaborative signals retrieved into the prompt, generation, then a feedback module that closes the loop |
| [Beyond recency bias](https://proceedings.mlr.press/v318/ghiasi26a.html) (PMLR v318) | 2026-06-28 | combines sequential and global collaborative signals specifically for the sparse-data regime — the regime the repo's new-user detours already diagnose |

The pattern across all four: **generation replaces ranking as the surface,
and verification/further retrieval replaces the score.** The ranked list does
not disappear — it becomes the retrieval input the generator conditions on,
which is again the mission-02 cascade, one layer deeper. And the sparse-data
results arrive at the same failure mode the repo's own detours reach from the
measurement side: cold users are where the loop breaks first.

## (f) What persists: the measurement discipline

The agentic turn changes the surface but not the discipline that made the
incumbent loops work. Three things survive every restructure above:

1. **Latency and cost budgets.** An answer thread that calls a model per turn
   is more expensive than a ranked list; the budget-pacing machinery (the
   repo's mission-02 online-experiment chapters) is *more* load-bearing, not
   less.
2. **Attribution and the offline-online gap.** The repo's mission-02 chapters
   measure how far an offline number is from a live one; the agentic surface
   widens that gap, because the action is now multi-turn and may end in an
   agent-authorized payment.
3. **The multi-target decision.** One target up, another down, and who
   decides — the seesaw the recommendation chapters analyze — is the same
   problem at the answer-thread level, now with the added question of whether
   the agent's own completion metric is a target or a confounder.

## (g) What this means for the repo's chapters

This survey feeds four decision-oriented frontier chapters in
[`04-agentic-platform/`](../../04-agentic-platform/). Each one lives inside
the stage that supplies its evidence — the old `07-frontier/` directory was
dissolved into the stages whose runs the chapter reads, so the loop and its
frontier reading are read in one place:

- **intent-to-delivery**
  ([`05-report/`](../../04-agentic-platform/05-report/intent-to-delivery/)):
  the loop that translates a stakeholder intent into a delivered outcome,
  grounded in the repo's own measured no-harness versus agent-loop runs, with
  the Gartner orchestration framing.
- **harness-anatomy**
  ([`02-agent-loop/`](../../04-agentic-platform/02-agent-loop/harness-anatomy/)):
  the control plane (loop, routing, approvals, tracing, recovery) versus the
  compute plane (sandbox), comparing the harnesses this repo itself runs
  against.
- **control-plane-governance**
  ([`04-how-it-fails/`](../../04-agentic-platform/04-how-it-fails/control-plane-governance/)):
  the protocol and governance layer — MCP/A2A, approval gates, reversal
  rates, the complexity cliff, observability — using the risk-control
  pattern in (a) as the "what a governed agent does" case.
- **what-a-reasonable-agentic-product-is**
  ([`03-cheap-or-expensive/`](../../04-agentic-platform/03-cheap-or-expensive/what-a-reasonable-agentic-product-is/)):
  what to automate versus gate, with the payments rails in (d) as the
  enabling layer and reversal rates as the evidence.

It also sharpens the mission-02 thesis. The topic claims recommendation,
search, and ads are one decision loop; the agentic turn strengthens that claim
— the three surfaces are converging on intent-to-delivery, where the same
agent mediates query, answer, and purchase. The convergence is at the loop
level, not the model level, and the incumbent disciplines in (f) are the
constraint the agent must fit inside.

## What this pass does not prove

No number on this page was measured in this repository; every figure is an
externally published result with its date attached. The pass does not
establish that any of these restructures is durable — the ad CPM, the AI Mode
user count, and the protocol consolidations are all early-2026 snapshots.
What the repo *could* check: the recommendation papers' sparse-data claims
against the repo's own cold-user detours, and the search-session claims
against the AOL query-log runs mission 02 already executes.
