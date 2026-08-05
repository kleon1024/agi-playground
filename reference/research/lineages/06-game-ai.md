---
level: reference
---

# The open-source line behind game AI

> Dated survey, 2026-08-06. Sources cited inline. External claims are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** this mission reuses mission 01's GRPO loop against a game's
verifiable reward and reports an honest null at cold-start scale. Where did
that loop come from, and what did each step of the line trade to get there?

## Value-based to policy-based

**DQN** (Mnih et al., 2015) learned a Q-value over Atari frames with
experience replay and a target network — the line's value-based start.
**A3C/A2C** (Mnih et al., 2016) moved to policy gradients with an advantage
estimate, and **PPO** (Schulman et al., 2017) stabilized the policy-gradient
update with a clipped surrogate objective, which became the default because
it is robust across environments with one hyperparameter set. **MuZero**
(Schlag et al., 2019) closed the loop by learning the model too — planning
without a known transition function.

The tradeoff along this line is the critic. Value-based methods need a
learned value function and pay its bias and instability; policy methods with
an advantage term need it as a baseline. **GRPO** (Shao et al., 2024,
DeepSeekMath) dropped the critic entirely: the advantage is the group
normalization of rewards sampled for the same prompt, so no value network
exists to drift. **RLVR** with verifiable rewards (R1 line, 2025) completed
the move by removing the learned reward model where the answer is checkable
— a game's win condition is exactly such a rule.

## The cold-start wall

The line's practical lesson is the one this mission inherits: GRPO sharpens
behavior a policy already produces sometimes; it cannot install behavior
that is absent. If every completion in a group scores identically, the group
advantage is 0/0 and no gradient moves. Mission 01 hit this on 200 of 200
steps; this mission's grid-world did not (1 of 200 per seed), because legal
moves plus a terminal goal give the policy variance to exploit — and the
stages after it report the rest of the story: neither a bigger group nor an
entropy bonus fixed the greedy-decode collapse, MiniGrid's cold start took
zero gradient steps, and the tool-use stage calibrated 1 of 3 seeds with 2
collapsed.

## Evidence boundary

Dated and attributed, not measured. The repo anchors — the 22.2% random
versus 82.4% greedy baselines, the 1/200 degeneracy count, the zero-gradient
MiniGrid run, the 1/3 tool-use calibration — cite their runs. The line does
not settle whether RL "works"; it says the honest null is a real result, and
this mission's report is MET for exactly that.
