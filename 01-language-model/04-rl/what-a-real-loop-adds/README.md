---
status: draft
level: applied
base: none
label: What a real loop adds
---

# Your toy loop runs. What does a real one have that it does not?

[The previous chapter](../) built GRPO against a Python function that checks
`13 * 17`. That loop is complete in the sense that every part of the mechanism
is there and none of it is hidden — and it is missing most of what a production
RL run spends its engineering on. This chapter is that gap, named part by part,
so that the next time you read a paper's method section you can tell which
failure each acronym was built for.

**Before this:** [how do you improve a model with no correct answer to
copy?](../), through the group-relative advantage, and
[the reward went up — did the model get better?](../reward-went-up/), for the
KL leash and reward hacking. Everything here assumes both.

Nothing on this page is run. Mission 01's GRPO run produced zero gradient steps
because every group came back degenerate, so the material below is mechanism and
published result, not measurement — restated at the end.

## The clip GRPO inherited without deriving

Stage 04 said the clipped surrogate is "copied from PPO unchanged" and moved on.
It is worth one derivation, because the asymmetry in it is the whole design:

$$
L^{\text{clip}}
=
\mathbb{E}
\left[
\min\left(
r_tA_t,
\operatorname{clip}(r_t,1-\epsilon,1+\epsilon)A_t
\right)
\right]
$$

**Worked, at the usual $\epsilon = 0.2$.** Take a good action, $A_t = +1$, on
which the update raised the probability by half, so $r_t = 1.5$. The two terms
are $1.5$ and $\operatorname{clip}(1.5, 0.8, 1.2) = 1.2$, and $\min$ takes
**1.2**. The last 0.3 of that improvement contributes nothing, so there is no
gradient rewarding a further push — the objective simply stops paying past 20%.
Now take $r_t = 0.9$ on the same good action: $\min(0.9, 0.9) = 0.9$, unclipped,
because the clip only ever binds in the direction of the *large* move.

That asymmetry is the point. An update that overshoots is capped; an update that
undershoots is left free to recover. PPO paid for it with a learned critic, a
frozen reference, and often a reward model — four models resident at once. GRPO
removed the critic and kept the clip, which is why the clip is the part every
later method still answers to.

## Which knob are you actually turning?

RL acronyms are only useful tied to the failure they were built for:

| Method | Main change | Failure it targets |
|---|---|---|
| PPO | learned critic, clipped ratio | high-variance destructive updates |
| GRPO | group-relative baseline | critic memory and training cost |
| GSPO | sequence-level probability ratio | token-ratio instability on sequence rewards |
| DAPO | sampling, clipping, length handling | low diversity, biased long responses |

Do not select a method by publication date. Identify first whether the failure
you are seeing comes from reward sparsity, advantage estimation, importance
ratios, clipping, length bias, or data generation — those have different fixes,
and three of the four rows above change something other than the objective.

## The verifier is the task

RL with verifiable rewards works when a deterministic procedure scores the
outcome: an exact numeric answer, a program that passes tests, a proof a checker
accepts, a tool task with an explicit success state. Stage 04's `compute_reward`
is the smallest possible instance of this.

The consequence is sharper than it first sounds. **The verifier does not measure
the task; it defines the task the policy optimizes.** If a math reward checks
only the final string, formatting shortcuts are a valid solution. If a coding
reward runs weak tests, the test gaps are what the policy learns. So a verifier
is a published artifact, not an implementation detail, and what gets published
with it is:

1. the accepted output grammar;
2. the verifier implementation and its version;
3. positive *and* adversarial examples;
4. the reward distribution by prompt slice;
5. manual audits of the high-reward failures.

Reward-model scores can supplement a verifier. They do not become ground truth
by being continuous.

Sampling, scoring, group-relative advantage, the clipped update, and the KL check
against the reference are now all in view — the loop as one object:

<!-- interactive: RLTrainingLoop -->

## The sampler is part of the training loop now

This is the structural difference from every earlier stage. Pretraining and SFT
read a dataset that exists before the run starts. RL *produces* its data online,
so temperature, top-p, maximum length, stop rules, group size, and rollout
concurrency all decide which trajectories reach the update.

Too little diversity gives identical rewards and zero advantage — stage 04's run
is that failure at its limit, 200 steps of degenerate groups. Too much diversity
spends compute on invalid trajectories. Truncation is the subtle one: cutting a
rollout at the length limit can make a correct reasoning path score as wrong, or
reward a short guess over a nearly complete solution.

Log the rollout policy separately from the optimizer configuration. A reward
curve cannot be interpreted at all if the sampling policy changed silently
underneath it.

## What changes when the model can act

A single-turn answer has one terminal reward. An agent trajectory has tool
selection, arguments, observations, retries, and a final answer — so the
environment now owns the tool contracts and their state transitions, which
observations are visible, how invalid actions are handled, when an episode
terminates, and both the task-success and the policy-adherence reward.

Credit assignment gets harder in a specific way: a successful final state can
contain bad intermediate actions, and an outcome-only reward will reinforce
them. Record the whole trajectory and score process guardrails alongside the
outcome. The harness this needs is
[stage 06's](../../06-agent/) — an environment is a software product, versioned
and tested, and a policy change attributed to "the RL algorithm" while the
environment also changed is not attributed at all.

## Why rollouts get expensive faster than you expect

Every rollout step reruns inference over the trajectory so far: the original
prompt plus every tool call, observation, and intermediate response already
produced. Each new step reprocesses that whole shared prefix again, multiplied
by the group size and by prompts per optimizer step.

This is a different cost from the paged-KV-cache management
[stage 05](../../05-serve/paging-the-cache/) covers. Paging manages GPU memory
for a cache within one serving session; the cost here is redundant *computation*
across separate calls that happen to share leading tokens. Two provider APIs
price it directly: Anthropic's prompt caching reached public beta on 14 August
2024, and OpenAI's Prompt Caching, announced 1 October 2024, auto-applies to
GPT-4o, GPT-4o mini, and o1-preview/o1-mini with discounted pricing on repeated
prefix tokens. Both let a rollout generator pay full price once for a
trajectory's shared prefix and a discount on every later step that reuses it,
instead of repricing the whole prefix every turn.

## The fix and its trade

The fixes on this page are the mechanisms a production loop adds, each
keyed to the failure it exists for, and each is a named trade:

- **The clipped objective** is the fix for destructive single-step updates.
  The asymmetry is the whole design: at epsilon 0.2 a good action whose
  probability rose to 1.5x pays only 1.2 (the last 0.3 of the improvement
  earns no gradient), while an action that undershot to 0.9x is left free.
  The trade is a ceiling on per-step learning in exchange for the guarantee
  that no single update destroys the policy — the guarantee every method in
  the line, from PPO (Schulman et al., 2017) to GSPO (Qwen team, July 2025)
  and GMPO (Zhao et al., July 2025; ICLR 2026), still answers to.
- **The verifier-as-published-artifact** is the fix for reward
  misdirection: the verifier does not measure the task, it defines it, so
  the accepted grammar, verifier version, adversarial examples, per-slice
  reward distribution, and manual audits of high-reward failures are all
  part of the fix. The trade is that a stricter verifier costs design and
  review time, and a looser one silently redefines the task — the failure
  this mission's own reward-gaming chapter measures.
- **The sampler as part of the training loop** is the fix for
  uninterpretable curves: temperature, top-p, max length, stop rules, group
  size, and rollout concurrency all decide which trajectories reach the
  update, so the rollout policy is logged separately from the optimizer
  config. The trade is a logging and versioning burden; the cost of not
  paying it is a reward curve that is not comparable to itself.
- **Prompt caching** is the fix for the rollout cost that grows with
  trajectory length: every rollout step re-encodes the whole shared prefix,
  and the group size multiplies it, so both providers priced the shared
  prefix explicitly — Anthropic's public beta on 14 August 2024, OpenAI's
  Prompt Caching on 1 October 2024. The trade is a cache-invalidation
  contract: a trajectory step that changes the prefix must invalidate what
  depended on it, or the discount is bought with stale context.

## Who owns the loop

- **The RL training team** owns the objective and its guards: the clip
  epsilon, the KL leash and beta, the group-size and sampling decisions —
  and the run log that records the rollout policy separately from the
  optimizer config, without which the reward curve cannot be read.
- **The reward and verifier team** owns the verifier as a published,
  versioned artifact: grammar, tests, adversarial examples, per-slice
  reward distribution, and the audit of high-reward failures — the fix for
  the task-definition failure, owned by the same team that builds the
  reward.
- **The evaluation team** owns the divergence read: held-out verifier
  success beside training reward, the KL trajectory, and the per-group
  advantage distribution — the numbers that tell a team which of the four
  fixes above is actually binding.
- **The serving and infrastructure team** owns the rollout cost layer:
  the paged-KV-cache for in-session memory, and prompt caching for the
  cross-call shared-prefix redundancy, with the cache-invalidation
  contract that keeps the discount honest.

## What this chapter does not establish

No run. Mission 01's GRPO attempt never reached a gradient step, so nothing here
is measured on this repository's hardware — the clip arithmetic is worked from
the definition, the method table is a reading of published work, and the
provider-caching dates are attributed to the vendors' own announcements. What
this chapter can do is tell you which failure each mechanism addresses; what it
cannot do is tell you which failure you have.

Primary references, in the order each fix arrived: Schulman et al., *Proximal
Policy Optimization Algorithms* (2017) is the clipped-ratio objective derived
above. Shao et al., *DeepSeekMath* (February 2024) introduces GRPO, trading
PPO's learned critic for the group-relative baseline. DAPO (ByteDance Seed,
March 2025) changes sampling, clipping, and length handling on top of the same
group-relative core. GSPO (Qwen team, July 2025) moves the importance ratio from
per-token to per-sequence to fix an instability GRPO shows on long, sparsely
rewarded sequences — and the same instability drew a second, parallel fix the
same month: Zhao et al., *Geometric-Mean Policy Optimization* (submitted 28 July
2025; revised October 2025; accepted ICLR 2026) keeps GRPO's per-token structure
and replaces the arithmetic mean of token-level rewards with their geometric
mean, which is inherently less sensitive to the outlier importance ratios GSPO's
rewrite targets. Two different repairs to one GRPO failure mode, not a
chronological sequel. Eight years separate PPO from that pair, and every method
in the line still answers the failure PPO's clip was built to prevent: an update
large enough to destroy the policy in a single step.

## Check your mental model

1. At $\epsilon = 0.2$, why does the clip bind on $r_t = 1.5$ but not on
   $r_t = 0.9$, for the same positive advantage?

<details>
<summary>Answer</summary>

Because $\min$ picks the *smaller* of the raw and clipped terms, and with
$A_t > 0$ that only ever penalizes the large move. At $r_t = 1.5$ the two
candidates are $1.5$ and $\operatorname{clip}(1.5, 0.8, 1.2) = 1.2$, so $\min$
takes 1.2 and the last 0.3 of improvement earns no gradient. At $r_t = 0.9$ both
candidates are $0.9$ — the clip range $[0.8, 1.2]$ does not bind — so the update
is unpenalized. The asymmetry is deliberate: overshooting is capped,
undershooting is left free to recover, which is the whole reason the clip exists
rather than a symmetric trust region.

</details>

2. Your reward curve is rising and held-out verifier success is flat. Which of
   the mechanisms on this page is the first place to look?

<details>
<summary>Answer</summary>

The verifier. Rising training reward with flat held-out success is the signature
of the policy finding a feature of *the reward* that does not transfer — and the
verifier defines the task the policy actually optimizes, so a formatting
shortcut or a test gap is a correct solution to the problem as posed. Look at the
adversarial examples and the manual audit of high-reward failures before touching
the algorithm; the second place to look is the sampler, in case the rollout
policy changed and the curve is not comparable to itself.

</details>

3. Stage 04 recomputes attention over the whole sequence at every generated
   token, and stage 05 fixes that with a KV cache. Why does prompt caching
   remain a separate problem from paging?

<details>
<summary>Answer</summary>

They fix redundancy at different boundaries. Paging manages *memory* for a cache
that lives inside one serving session — it decides where a sequence's keys and
values sit while that sequence is being generated. Prompt caching is about
redundant *computation across separate calls*: each rollout step is a fresh
request whose prompt is the whole trajectory so far, so the shared prefix is
re-encoded from scratch every turn even though a within-session cache is working
perfectly. Group size multiplies it, and the trajectory grows every step, which
is why both providers priced the shared prefix explicitly rather than leaving it
to the serving layer.

</details>

## Next

Return to [stage 04](../) for the reproduction commands, or continue the mission
at [stage 05 — serve](../../05-serve/): the rollout cost above is the reason a
real GRPO loop needs the KV cache and batched decoding built there, before it
needs a better objective.
