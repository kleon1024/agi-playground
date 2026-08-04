---
status: draft
level: applied
---

# How does a model improve with no answer to copy?

Only a signal about whether it succeeded. How can a policy improve from its own
attempts without collapsing onto reward shortcuts or drifting away from the
assistant we already trust?

[Stage 04 of the language-model system](../../../missions/01-language-model-agent/04-rl/)
arrives here needing one thing before it spends any compute: the condition
under which the gradient is non-zero at all. Take that back — it decides
whether the stage is worth running on a given base.

The loop is:

```text
prompt -> sample responses -> score outcomes
       -> estimate relative advantage -> update policy
       -> sample again
```

Unlike offline preference optimization, the policy changes the data it will see
next. Reward design, exploration, and stability are now one system.

**Before this:** [post-training](../post-training/). Reinforcement learning
sharpens behavior a model already produces sometimes, so it presupposes a policy
that supervised fine-tuning has already shaped.

Pretraining is a separate, earlier precondition from the SFT one above: it is
what puts a behavior anywhere in the model's distribution at all. RL cannot
install a behavior with zero probability under the current policy — it can
only reweight a behavior that already occurs sometimes under sampling. [Mission
06's stage 03](../../../missions/06-game-ai/03-fixing-collapse/) shows this
precondition in miniature, with a cold-start (`base: scratch`) policy and no
pretrained backbone at all: GRPO training alone produces real board-sensitivity
under sampled decode (14.4-21.0% success across seeds) — the behavior exists in
the distribution, sometimes — yet greedy/argmax decode ignores the board
entirely on every seed, and neither a smaller rollout group nor a direct
entropy bonus moved the argmax toward it. The entropy bonus measurably widened
the distribution (1.3-1.7 nats) without ever changing which token wins the
argmax: the training signal did the one thing it can do, reweight what
sampling already reaches, and reweighting was not enough to make the
board-sensitive behavior the deterministic default. Pretrain-to-RL is about
whether a behavior is present in the distribution at all; SFT-to-RL, above, is
about which present behavior becomes the default RL then sharpens.

## Why can you not just take the gradient of a reward?

For language-model RL:

- state is the prompt plus tokens generated so far;
- action is the next token;
- policy is the language model;
- return is derived from the completed response or trajectory.

REINFORCE increases log-probability of sampled actions in proportion to their
return, but raw return has high variance. Subtracting a baseline produces an
advantage: how much better this action was than the expected outcome.

PPO learns that baseline with a critic and limits update size with a clipped
probability ratio:

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
gradient rewarding a further push — the objective stops paying past 20%. Now
take $r_t = 0.9$ on the same good action: $\min(0.9, 0.9) = 0.9$, unclipped,
because the clip only ever binds in the direction of the *large* move. That
asymmetry is the whole design. An update that overshoots is capped; an update
that undershoots is left free to recover.

A separate reference policy supplies a KL penalty so reward improvement does
not erase the SFT policy. The price is a complex loop with actor, critic,
reference model, and often a reward model.

## What can stand in for a value model?

GRPO samples a group of responses to the same prompt and standardizes reward
within that group:

$$
\hat A_i
=
\frac{r_i-\operatorname{mean}(r_1,\ldots,r_G)}
{\operatorname{std}(r_1,\ldots,r_G)}
$$

**Worked, on a group of 8 with a binary verifiable reward.** Two rollouts solve
the task and six do not: mean 0.25, population standard deviation 0.433. The
two winners get an advantage of $(1-0.25)/0.433 = +1.73$; the six losers get
$(0-0.25)/0.433 = -0.58$. Note that the successes are pushed up three times as
hard as each failure is pushed down — the scarcer the success, the louder it
is. At 4 out of 8 the numbers become $+1.00$ and $-1.00$ and the signal is
symmetric.

Now set the group to 0 out of 8, or 8 out of 8. The standard deviation is zero,
$\hat A_i$ is $0/0$, and the prompt contributes nothing at all. The
implementation adds an epsilon and skips the group; no epsilon rescues the
missing information.

Change the response rewards below. Watch the advantage change relative to the
group rather than the absolute reward scale.

<!-- interactive: GRPOAdvantage -->

If every response receives the same reward, every advantage is zero and the
prompt produces no learning signal. This is the first operational requirement
for the task distribution: prompts must allow meaningful variation within a
sampled group.

GRPO removes the learned critic, not the need for:

- an old-policy ratio;
- a bounded update;
- a reference or equivalent drift control;
- correct token-level masking;
- enough distinct samples per prompt.

## Which knob are you actually turning?

RL acronyms are useful only when tied to a failure:

| Method | Main change | Failure it targets |
|---|---|---|
| PPO | learned critic and clipped ratio | high-variance destructive updates |
| GRPO | group-relative baseline | critic memory and training cost |
| GSPO | sequence-level probability ratio | token-ratio instability for sequence rewards |
| DAPO | sampling, clipping, and length-handling changes | low diversity and biased long responses |

Do not select a method from its publication date. Identify whether the
observed failure comes from reward sparsity, advantage estimation, importance
ratios, clipping, length bias, or data generation.

## What should the reward be measuring?

RL with verifiable rewards works when a deterministic procedure can score the
outcome: an exact numeric answer, a program that passes tests, a proof checked
by a verifier, or a tool task with explicit success state.

The verifier defines the task the policy actually optimizes. If a math reward
checks only the final string, the policy may discover formatting shortcuts. If
a coding reward uses weak tests, the policy learns the test gaps.

For every reward, publish:

1. the accepted output grammar;
2. the verifier implementation and version;
3. positive and adversarial examples;
4. reward distribution by prompt slice;
5. manual audits of high-reward failures.

Reward-model scores can supplement a verifier, but they do not become ground
truth by being continuous.

Sampling, scoring, group-relative advantage, the clipped update, and the KL
check against a reference policy are now all in view — the loop as a whole:

<!-- interactive: RLTrainingLoop -->

## Why is the sampler now part of the training loop?

RL data is produced online. Temperature, top-p, maximum length, stop rules,
group size, and rollout concurrency control which trajectories enter the
update.

Too little diversity gives identical rewards and zero advantage. Too much
diversity spends compute on invalid trajectories. Truncation can make a correct
reasoning path appear wrong or reward a short guess over a nearly complete
solution.

Log rollout policy separately from optimizer configuration. A reward curve
cannot be interpreted if the sampling policy changed silently.

## What changes when the model can act?

A single-turn answer has one terminal reward. An agent trajectory includes tool
selection, arguments, observations, retries, and a final answer. The
environment must now own:

- tool contracts and deterministic state transitions;
- which observations are visible;
- invalid-action handling;
- episode termination;
- task success and policy-adherence rewards.

Credit assignment becomes harder because a successful final state can contain
bad intermediate actions. Record the full trajectory and score both outcome
and process guardrails.

An environment is a software product, not a prompt list. Version it and test it
before attributing a policy change to the RL algorithm.

## Why does generating rollouts get expensive as trajectories grow?

Every rollout step reruns inference over the trajectory so far: the original
prompt plus every tool call, observation, and intermediate response the agent
has already produced. Each new step's forward pass reprocesses that whole
shared prefix again, multiplied by many rollouts per prompt and many prompts
per optimizer step. This is a distinct cost from the paged-KV-cache management
[serving](../../../missions/01-language-model-agent/05-serve/) covers: paging manages GPU memory for the cache
within one serving session, while the cost here is redundant computation
across separate calls that happen to share the same leading tokens.

Two provider APIs price this directly. Anthropic's prompt caching went to
public beta on August 14, 2024. OpenAI's Prompt Caching, announced October 1,
2024, auto-applies to GPT-4o, GPT-4o mini, and o1-preview/o1-mini with
discounted pricing on repeated prefix tokens. Both let a rollout generator pay
full price once for a trajectory's shared prefix and a discount on every later
step that reuses it, instead of repricing the whole prefix at every turn.

## Reward went up. Did anything get better?

Monitor a set of signals that can disagree:

```text
training reward
held-out verifier success
response length and format
KL from reference
diversity within each group
manual high-reward failure rate
baseline capability regressions
```

Rising training reward with flat held-out success is not progress. It is
evidence that the policy found a feature of the training reward that does not
transfer.

Stop conditions belong in the run contract: maximum KL, regression tolerance,
invalid-output rate, and a manual-audit threshold.

## Run the vertical slice

[Mission 01, RL](../../../missions/01-language-model-agent/04-rl/) applies
group-relative optimization to a small verifiable task. The minimum convincing
evidence is:

- reward and verifier success on held-out prompts;
- comparison with the pre-RL policy;
- KL or another drift measurement;
- inspected high-reward failures;
- exact rollout and optimizer configuration.

The run does not establish that the resulting policy is broadly better or safe
outside the verifier's domain.

## Check your mental model

Answer each before opening it.

**1. Why does equal reward within a group create no GRPO learning signal?**

<details>
<summary>Answer</summary>

Because the advantage standardizes each reward against the group's own mean
and standard deviation: $\hat A_i = (r_i - \operatorname{mean})/\operatorname{std}$.
If every response in the group gets the same reward, each $r_i$ equals the
mean exactly, so the numerator is zero for every response and every advantage
is zero — the prompt contributes no gradient at all. The degenerate cases at
the extremes (0 out of 8, or 8 out of 8) make the same failure sharper: the
standard deviation itself is zero, $\hat A_i$ becomes $0/0$, and no epsilon
added to avoid the division recovers information that was never there —
prompts need to allow meaningful variation within a sampled group or they
teach nothing.

</details>

**2. Which part of PPO does GRPO remove, and which safeguards remain?**

<details>
<summary>Answer</summary>

GRPO removes the learned critic — the separate value model PPO trains to
estimate the baseline — replacing it with a baseline computed directly from
the group's own sampled rewards (standardized mean and standard deviation).
What GRPO does not remove: the old-policy importance ratio, a bounded/clipped
update, a reference policy or equivalent drift control (the KL check),
correct token-level masking, and the need for enough distinct samples per
prompt for the group statistics to mean anything. Dropping the critic cuts
training cost and removes one source of critic-memory error; it does not
remove the need for the other stability safeguards PPO established.

</details>

**3. Why is the rollout sampler part of the optimization algorithm?**

<details>
<summary>Answer</summary>

Because RL data is produced online — the policy generates the very
trajectories it will then train on, so sampler settings (temperature, top-p,
maximum length, stop rules, group size, rollout concurrency) directly decide
what enters the update, not just how it's preprocessed. Too little diversity
means every rollout in a group gets the same reward and the advantage is
zero, exactly as in question 1; too much diversity spends compute sampling
invalid trajectories that teach nothing useful. Truncation is not a
harmless efficiency knob either — it can make a correct-but-long reasoning
path look wrong, or reward a short guess over a nearly complete solution.
None of that is separable from "the algorithm"; it is why the chapter insists
on logging rollout policy separately from optimizer configuration, since a
reward curve is uninterpretable if the sampling policy changed silently
underneath it.

</details>

**4. How can a correct verifier still reward the wrong behavior?**

<details>
<summary>Answer</summary>

Because the verifier's specific check *is* the task the policy actually
optimizes, and a verifier can be "correct" on the cases it checks while still
being narrow enough to leave shortcuts open. A math reward that checks only
the final string can be satisfied by a formatting trick that produces the
right string through the wrong reasoning; a coding reward built on weak tests
can be satisfied by code that passes those specific tests without solving
the general problem — the policy learns the gaps in the test suite, not the
task the tests were meant to stand in for. The verifier is not a passive
scorer sitting outside the loop; whatever it fails to check becomes a
shortcut available to the policy.

</details>

**5. Which evidence separates reward improvement from general capability?**

<details>
<summary>Answer</summary>

No single signal does — the chapter's answer is a set of signals that can
disagree with each other: training reward, held-out verifier success,
response length and format, KL from the reference policy, diversity within
each group, manual audit of high-reward failures, and baseline capability
regressions. The diagnostic case named explicitly is training reward rising
while held-out verifier success stays flat — that combination is not
progress, it is direct evidence the policy found a feature of the *training*
reward specifically that does not transfer to prompts it wasn't optimized
against. Trusting training reward alone would miss exactly this failure.

</details>

## Next

The output is a policy checkpoint and the environment that trained it.
Continue to [serving](../../../missions/01-language-model-agent/05-serve/) to expose that policy under a latency and
memory contract, then evaluate the complete system rather than the checkpoint
alone.

Primary references, in the order each fix arrived: Schulman et al., "Proximal
Policy Optimization Algorithms" (2017) is the clipped-ratio objective this
chapter derives above; Shao et al., "DeepSeekMath" (February 2024) introduces
GRPO, removing PPO's learned critic in exchange for the group-relative
baseline this chapter's worked example uses; DAPO (ByteDance Seed, March 2025)
changes sampling, clipping, and length-handling on top of the same group-
relative core; GSPO (Qwen team, July 2025) moves the importance ratio from
per-token to per-sequence to fix instability GRPO shows on long, sparsely-
rewarded sequences. The same instability drew a second, parallel fix the same
month: Zhao et al., "Geometric-Mean Policy Optimization" (submitted July 28,
2025; revised October 2025; accepted ICLR 2026) keeps GRPO's per-token
structure but replaces the arithmetic mean of token-level rewards with their
geometric mean, which is inherently less sensitive to the outlier importance
ratios that motivate GSPO's sequence-level rewrite — two different repairs
to the same GRPO failure mode, not a chronological sequel. Eight years
separate PPO from this pair, and every later method in this line still
answers to the same failure PPO's clip was built to prevent: an update large
enough to destroy the policy in one step. Also
relevant: RLVR work and agent-environment evaluation literature, which this
chapter's later sections on verifiable rewards and agent trajectories draw on
without dating to one paper.

## The layer underneath this one

Every method above assumes the rollouts arrive. [Why an RL update step waits on
its slowest rollout](../../../infra/07-rollout-concurrency/) measures what
lockstep batching costs once trajectory length is heavy-tailed instead of
fixed — the mechanism asynchronous RLHF systems exist to avoid, and the reason
the sampler half of the loop, not the trainer half, is usually what you are
paying for.

[The RL landscape](LANDSCAPE.md) names the production frameworks that own the
sampler-plus-trainer loop this chapter builds by hand, and what each assumes
about who owns the environment.
