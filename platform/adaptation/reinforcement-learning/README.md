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

1. Why does equal reward within a group create no GRPO learning signal?
2. Which part of PPO does GRPO remove, and which safeguards remain?
3. Why is the rollout sampler part of the optimization algorithm?
4. How can a correct verifier still reward the wrong behavior?
5. Which evidence separates reward improvement from general capability?

## Next

The output is a policy checkpoint and the environment that trained it.
Continue to [serving](../../serving/) to expose that policy under a latency and
memory contract, then evaluate the complete system rather than the checkpoint
alone.

Primary references: PPO, DeepSeekMath and GRPO, GSPO, DAPO, RLVR work, and
agent-environment evaluation literature.

[The RL landscape](LANDSCAPE.md) names the production frameworks that own the
sampler-plus-trainer loop this chapter builds by hand, and what each assumes
about who owns the environment.
