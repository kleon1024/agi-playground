---
status: verified
level: applied
base: scratch
verified: 2026-08-03
label: Tool-use decision (calculator)
---

# Does GRPO learn *when* to pay for a tool, not just what to say?

**Question:** every prior stage in this mission trained a policy to choose
*where to move*. This stage keeps the identical GRPO mechanism and asks it to
learn a different kind of decision: given an arithmetic problem at a stated
difficulty, should the policy answer directly and risk being wrong, or spend
the turn invoking a calculator tool that is always right but costs a fixed
penalty? A well-calibrated policy pays that cost only when it is worth
paying -- on hard problems, not easy ones.

**The artifact this stage produces** is 3 real training runs whose
per-difficulty decision rates turn out to split down the middle: one seed's
greedy policy separates cleanly at exactly the point the reward crosses --
answering below it, invoking the tool above it -- while the other two
collapse to one fixed decision regardless of difficulty, the same
context-independent collapse stage 01 and stage 04 already documented, now
recurring in a two-action decision space instead of a grid or a
partially-observed room.

**Before this:** [stage 05](../05-report/), which closed mission 06's
original grid-world/MiniGrid scope with an honest null result. This stage
does not revisit that result; it extends the same machinery to a new
decision variable the mission's contract did not originally cover.

## The decision, and why a fixed cost makes it a real tradeoff

Each episode is one arithmetic problem -- `a op b` at one of 5 difficulty
levels, 1 to 5 digits per operand. The policy has exactly two moves:

- **Answer directly.** The environment does not grade the policy's actual
  arithmetic (see "Why the reward does not check real arithmetic" below) --
  it draws a fresh correct/incorrect outcome from a stated, difficulty-scaled
  probability, `simulated_accuracy(digit_count)`, standing in for "how good
  this policy's own mental arithmetic already is" at that difficulty.
- **Invoke the calculator.** Always returns the exact right answer, and
  always costs a fixed, stated penalty, `TOOL_COST = 0.30`, taken out of the
  same `+1`/`0` correctness reward the direct-answer path is scored against.

`simulated_accuracy` is linear in digit count -- 0.97, 0.82, 0.67, 0.52, 0.37
for levels 1 through 5 -- and crosses the tool's flat `1 - TOOL_COST = 0.70`
reward between level 2 and level 3. That crossing is the whole task: answer
directly below it, invoke the tool above it. Full model and derivation in
[`core/reward.py`](core/reward.py).

## Why the reward does not check real arithmetic

Holding "change one mechanism at a time" (the same discipline mission 07's
codebook-reset stage and mission 05's warmup-stability stage apply) means
this stage's only new variable is the tool-invocation decision -- not the
policy's arithmetic competence, which mission 01's own `04-rl` stage already
studies on its own terms. If `outcome_reward` graded the policy's own
computed answer, a poor result here could mean either "the policy can't do
arithmetic" or "the policy can't learn when to delegate," with no way to
tell which. `simulated_accuracy` removes the first confound by declaring the
direct-answer accuracy as a stated function of difficulty alone, deterministic
in its *shape* per level but drawn fresh (a real Bernoulli trial) on every
attempt -- not a fixed property of the specific problem instance repeated
identically. This is a synthetic proxy standing in for imperfect arithmetic,
stated plainly as such: it is not a claim about any real LLM's actual
arithmetic error rate.

## The baselines, and the headroom between them

Mission 06's contract requires two fixed baselines, measured the same way
stage 00 measured random and greedy-lookahead: 5,000 real trials each,
against the reward function above.

```
never_tool (always answer):  mean_reward = 0.8654
always_tool (always invoke): mean_reward = 0.9000
calibrated reference*:       mean_reward = 0.9780
```

*Not one of the two required baselines -- an analytic reference that sees
`simulated_accuracy` directly (a real policy cannot; it only sees the
difficulty label) and always takes whichever action has the higher expected
value at each level. It states the real headroom a trained policy has to
close: 0.078 over always-tool, 0.1126 over never-tool. Full numbers in
[`runs/2026-08-03-baselines.md`](runs/2026-08-03-baselines.md).

Neither baseline reads the difficulty label at all. `always_tool` beats
`never_tool` on the mean only because 3 of 5 levels favor the tool -- a
policy that reads the label and answers directly on levels 1-2 while
invoking the tool on levels 3-5 has real room to beat both.

## A design mistake worth keeping visible: the format reward's first version

The completion protocol is deliberately a single character, `A` or `T`, not
the words `ANSWER`/`TOOL`. An earlier version of `core/reward.py` used the
full words, and the first real training run came back with all 200 of 200
steps degenerate: a randomly initialized, character-level policy sampling
from a ~40-symbol vocabulary has almost no chance of ever spelling a specific
4-6 character sequence in the right order, so every one of 8 rollouts per
group scored `format = 0.0`, `std(rewards) == 0`, and GRPO never took a
gradient step. That would have re-measured mission 01's own "a cold start
almost never emits a specific multi-character tag" result under a new name,
not the question this stage actually asks. Switching to a 2-character legal
alphabet -- the same design the grid-world's `ACTIONS = "UDLR"` already uses,
where any of several single characters earns credit -- fixed it: training
escaped degenerate groups from the first logged step onward. Full mechanism
in [`core/reward.py`](core/reward.py)'s `_DECISION_CHARS` comment.

## Result: one seed found the exact calibrated policy, two did not

3 seeds, 200 GRPO steps each -- identical hyperparameters to stage 01's
grid-world run (`group_size=8`, `prompts_per_step=4`, `clip_eps=0.2`,
`kl_beta=0.04`), only the environment and reward substituted:

```
                 greedy mean_reward   level 1   level 2   level 3   level 4   level 5
 seed 0:               0.8838          ANSWER    ANSWER    TOOL      TOOL      TOOL
 seed 1:               0.7430          ANSWER    ANSWER    ANSWER    ANSWER    ANSWER
 seed 2:               0.7590          ANSWER    ANSWER    ANSWER    ANSWER    ANSWER
 oracle (optimal):        --           ANSWER    ANSWER    TOOL      TOOL      TOOL

 3-seed mean: 0.7953   spread: 0.1408   never_tool baseline: 0.8654   always_tool baseline: 0.9000
```

**Seed 0's greedy decision matches the calibrated-oracle reference at every
one of the 5 levels** -- answering directly where `simulated_accuracy`
exceeds the tool's flat reward, invoking the tool where it does not. Seeds
1 and 2 both collapse to answering directly at every level, ignoring the
difficulty label entirely. Because the 3 seeds are not doing the same
thing, the spread (0.1408) is larger than either baseline margin, so by the
same rule stage 02's `report.py` applies (a margin counts as real only if
it exceeds the measured spread), the 3-seed mean neither decisively beats
nor decisively loses to `never_tool` or `always_tool` -- a third, honest
outcome, not stretched into either.

Seed 0's raw reward (0.8838) sits below the calibrated-oracle's 0.9780 for
an orthogonal reason, not a decision-quality one: its completions repeat
the decision character (`AAATTTTT`, `TTTTTTTT`) instead of stopping
immediately after one clean character, capping `format_reward` at 0.5
instead of 1.0 on most trials. Recomputed as if every completion had
scored full format credit, seed 0's per-level rewards reproduce the
oracle's 0.978 almost exactly -- the decision itself is exactly right; the
gap is a separate, unaddressed formatting inefficiency.

This is the first result in this mission where any seed produces a
policy conditioned correctly on the input rather than collapsing to a
constant action -- a materially different outcome from mission 01's
zero-gradient null and stage 04's MiniGrid null, where no seed ever
escaped a degenerate or context-independent policy. It is also not a
reliable result: 2 of 3 seeds show the identical collapse this mission has
now documented in three different environments. Full per-seed numbers,
the failure/success catalogue, and compute in
[`runs/2026-08-03-grpo-training.md`](runs/2026-08-03-grpo-training.md).

<!-- interactive: ToolUseDecision -->

## The fix and its trade

The fix that unblocked this stage was a design change, not a training
signal: the completion protocol moved from the words `ANSWER`/`TOOL` to
the single characters `A`/`T`. The first real run with the word-based
protocol returned all 200 of 200 degenerate steps -- a character-level
policy over a ~40-symbol vocabulary almost never spells a specific 4-6
character sequence in order, so every rollout scored `format = 0.0` and
GRPO never took a gradient step. The trade is expressiveness for
learnability: a 2-character legal alphabet (the same design the grid
world's `ACTIONS = "UDLR"` uses) lets any of several single characters
earn credit, at the cost of a narrower surface -- the policy can no longer
"say" which tool or argument it wants, only that it wants one. That is the
correct trade for this stage's single-tool question and a real limitation
to name before a multi-tool extension.

The second fix-and-trade is the format credit itself. `format_reward`
rewards emitting a legal decision character without checking the
arithmetic, which is what lets the policy learn *that* it should decide
without first learning arithmetic -- but it is also the mechanism behind
seed 0's capped 0.5 format credit (repeated `AAATTTTT` completions) and
behind the format-credit trap detour, where reward can be earned without
the outcome. The trade is a standing one: dense credit for the action
shape, sparse credit for the outcome, and the two must be reported
separately or a policy that exploits the format half looks better than it
is.

## Who owns this loop

- **The task/reward owner** owns the protocol design (single-character
  decisions) and the format-vs-outcome split. The word-protocol
  degeneration was a reward-design bug, caught only because the stage
  holds "change one mechanism at a time" and the reward is kept visible.
- **The RL team** owns the per-seed spread as the acceptance rule. Seed 0
  matches the oracle at all 5 levels; seeds 1-2 collapse to always-answer.
  Because the spread (0.1408) exceeds both baseline margins, the 3-seed
  mean is a third, honest outcome -- and the team that reports it has to
  name that 2 of 3 seeds reproduce the mission's documented collapse.
- **The evaluation owner** owns the baselines that make the headroom
  visible: never-tool 0.8654, always-tool 0.9000, calibrated reference
  0.9780 -- the reference is what a real policy cannot see (it only reads
  the difficulty label), which is the honest definition of the headroom.

## What this stage does not establish

This is a single-step, single-tool decision: one arithmetic problem, one
calculator, one choice per episode. It says nothing about multi-tool
selection, multi-step tool chains, real tool-call latency or failure modes
(the "tool" is a Python function, not a network request), or a real LLM's
actual arithmetic error rate -- `simulated_accuracy` is a stated, synthetic
function of digit count, not a measurement of any model. It does not use
mission 04's hosted-API agent harness, which is deliberate: mission 04's
\$30 budget is nearly exhausted and it is not a training mission, so this
stage stays inside mission 06's own \$0-marginal-cost, verifiable-reward
frame instead. Full boundary in [`mission.yaml`](../mission.yaml) under
`does_not_prove`.

Nor does this result establish reliability: no intervention (learning
rate, KL budget, group size) was tried to make seed 0's outcome the
typical one rather than the exception, the same kind of search stage 03
ran for a different collapse and is not repeated here.

**Next question:** whether a calibrated tool-invocation policy, once (or if)
one is found, survives a difficulty distribution it was not trained on --
not attempted here.

A detour from here: [why did two seeds stop paying for the
tool?](when-two-seeds-stopped-paying/) — the recorded tool-rate
trajectories: the calibrated seed's rate oscillates, the collapsed seeds'
rates die to zero, and the divergence shows up by mid-training.

Another detour: [the reward half that can be earned without the outcome](the-format-credit-trap/) — the recorded seeds read: the policy answers easy levels directly in every seed, but only seed 0 pays for the tool at the hard level.
