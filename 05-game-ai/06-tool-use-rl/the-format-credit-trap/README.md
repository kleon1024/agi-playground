---
status: verified
level: applied
base: scratch
label: The format-credit trap
verified: 2026-08-06
---

# The reward half that can be earned without the outcome

**Question:** [stage 06's tool-use RL](../) rewards format credit for legal
A/T characters and outcome credit for correct counts. This chapter reads
the recorded seeds and asks what the reward split produced.

**Before this:** [stage 06's tool-use RL](../) and its recorded seeds.

## The per-level behavior, read

The run ([record](runs/2026-08-06-format-trap-read.md)) reads the recorded
seeds:

| seed | mean reward | level-1 answer_rate | level-5 tool_rate |
|---|---:|---:|---:|
| 0 | 0.884 | 1.00 | 1.00 |
| 1 | 0.743 | 1.00 | 0.00 |
| 2 | 0.759 | 1.00 | 0.00 |

## Two readings

**The policy answers easy levels directly — that is the format credit
working as intended.** At level 1, every seed produces an answer with
answer_rate 1.00: the policy has learned the format and answers without
calling the tool, exactly what the reward's format half is for. The
format credit is not a bug; it is the scaffold that gets the policy to
produce well-formed output at all.

**The trap is at the hard level: only seed 0 pays for the tool.** At level
5, seed 0's tool_rate is 1.00 — it calls the tool when counting gets hard
— but seeds 1 and 2 stop at 0.00. Two of three seeds learned to answer
easily and then refused to pay the tool cost on hard items. The reward
split is what makes that legible: format credit rewards the answer shape,
not the decision to use the tool, and the seeds differ in whether the
outcome credit outweighed it.

## Evidence boundary

The recorded seed JSONs (200 steps each, 1,000-trial eval, one reward
function). It reads those artifacts; it does not re-train.

## Check your mental model

Answer each before opening it.

**1. Why is the format half necessary if it can be gamed?**

<details>
<summary>Answer</summary>

Because a format-free reward gives no gradient on the way to a
well-formed completion. The same reason mission 01's arithmetic reward
keeps a format component: a 0/1-only reward on the raw outcome leaves the
policy with nothing to optimize until it randomly emits the full correct
shape. The format credit gets it there; the trap is that it can then be
earned without the outcome, which is why the mission tracks both halves
separately.

</details>

**2. What does the seed split say about the training, not the task?**

<details>
<summary>Answer</summary>

That the tool-use decision is not reliably learned — seed 0 pays for the
tool at the hard level, seeds 1-2 do not, from the same reward and
budget. The outcome credit did not consistently outweigh the format
credit's pull, so the "when to use a tool" behavior is seed-dependent
rather than learned. The recorded split is the evidence that the
decision, not the mechanics, is where the training falls short.

</details>

## Next

Back to [stage 06](../), or to
[why two seeds stopped paying for the tool](../when-two-seeds-stopped-paying/)
which reads the same run's collapse side.
