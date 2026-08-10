---
status: verified
level: frontier
base: none
label: Intent to delivery
verified: 2026-08-08
---

# Where does intent stop being delivered?

**Question:** a maintainer hands an agent a bug report and a failing test.
The agent writes back what looks like a patch. How often does the intent —
the bug is fixed, nothing else breaks — actually arrive, and where does it
stop on the way?

**The artifact this chapter follows** is one table, read from this mission's
own recorded arms:

```text
                    produced   delivered   $/delivered
blind call (18)     5/18       4/18        $1.2859
full harness (18)   18/18      18/18       $0.5066
feedback-only (12)  2/12       2/12        $1.5256
```

By the end you will be able to say which step in the intent-to-delivery path
the loop actually repairs, and which failures it leaves alone.

**Before this:** [stage 01](../../01-no-harness/) and
[stage 03](../../03-cheap-or-expensive/), whose real attempts this reads, and
[stage 04's failure taxonomy](../../04-how-it-fails/), which names the
categories.

## The failure mode: intent translated into words, not into delivery

The blind arm is what "the model writes code" looks like without a loop:
one call, the issue text, the failing test, oracle file location, a diff
applied blind. Of 18 attempts, only 5 produced something `git apply` would
accept, and 4 delivered a resolved task. The intent did not stop at the
reasoning — the model was handed the exact file the fix belongs in, and its
words were patch-shaped. The intent stopped at the *translation*: a patch
that cannot be applied is not a wrong fix, it is a failed delivery, and
[stage 04](../../04-how-it-fails/) showed eleven of the twelve unresolved
attempts failed exactly there, not on the substance of the fix.

This is the failure mode that matters outside coding too. Search, ads, and
commerce are converging on intent-to-delivery as their surface — the
[paradigm survey](../../../reference/research/agentic-paradigm-restructuring.md)
documents Google folding AI Mode into a single conversational loop (1 billion
monthly users at I/O 2026) and OpenAI moving ads inside the answer thread. In
every one of those surfaces the deliverable is not the words; it is the
outcome the words are supposed to cause. A search agent that narrates a
correct itinerary it then cannot book has produced a patch-shaped object.

## How you find the case

The recorded arms make the gap legible because they separate *produced* from
*delivered*. The blind arm produced 5/18 and delivered 4/18; the harness arm
produced 18/18 and delivered 18/18. The per-tier read is sharper: blind haiku
delivered 0/6, sonnet 1/6, opus 3/6, and the harness delivered 6/6 at every
tier. The spread between arms is the case-finding instrument — the same
tasks, the same three models, one variable changed, and the delivery rate
moves from 4/18 to 18/18.

The harness loop closes the gap with three mechanisms, each answering a
specific stop:

| Stop on the path | What the loop adds | Recorded effect |
|---|---|---|
| translate intent to an artifact | tool loop with retries | 11 of 12 blind failures never applied; the loop re-reads and retries until the diff parses |
| act on the world | real tool execution | the model sees the actual tree, not a paraphrase |
| verify the claim | scored test run | `resolved` means the target test passes and nothing that passed before regressed |

## The fix and its trade

The fix is the loop itself, and its price is visible in the same table: the
harness arm spent \$9.119 against the blind arm's \$5.144 — 1.8x the money —
but delivered 18 outcomes instead of 4, which is why cost *per delivered
outcome* (\$0.5066 vs \$1.2859) favors the loop. The trade is that delivery
now depends on the loop's machinery, and the machinery has its own failure
surface: a loop that grounds on a wrong tool result can be confidently wrong
in more steps, and stage 03's own patches showed exactly this — resolve rate
18/18 while generality measured 6/9, three latent defects the given test
cannot see. The loop moves intent to delivery; it does not decide whether the
delivery is *right* outside the shape the test exercises.

Two more limits are structural, not fixable by a longer loop. The intent must
be scoreable in the first place: [stage 00](../../00-task-set/) admitted only
2 of 6 candidate tasks because a task counts only if its test fails before
and passes after the fix — writing that test is usually the hard part of the
job, and this mission hands it to the agent for free. And a different harness
changes the whole table: OpenAI's own ARC-AGI-3 record shows the same model
moving from 13.3% to 38.3% on two harness settings alone
([the recorded landscape pass](../../harness-effects-landscape.md)), and
Epoch AI's SWE-bench audit found scaffold choice moving one model from 62.3%
to 70.2% — a 22-point swing on SWE-bench Pro between basic and optimized
scaffolds
([Epoch AI tracking, reported 2026-07-03](https://futureagi.com/blog/coding-agent-harness-benchmark/)).
An intent-to-delivery number is a property of the pair (model, harness), and
the harness half is the one this mission controls.

## Who owns the loop

- **The task-set owner** owns the scoreability precondition: the intent that
  arrives here already has a failing test, which is the selection that makes
  delivery measurable and is also the largest distortion.
- **The harness owner** owns the three mechanisms above — retry, real tool
  execution, scored verification — and the failure surface they introduce.
- **The product owner** owns the produced-vs-delivered distinction, because
  a demo that narrates but does not deliver is the blind arm wearing a nicer
  interface.

## Check your mental model

1. The blind arm was handed the exact file the fix belongs in. What does that
   make 4/18 a measurement of?

<details>
<summary>Answer</summary>

It measures the *delivery* step only: given oracle file location, how often
does a single call produce a diff that applies and makes the test pass. It
does not measure whether the agent can find the bug — that step was handed
over for free, which is what isolates translation-and-apply as the failure
surface. The 11-of-12 non-applying finding says that surface is mostly
mechanical: the model miscounted its own patch, not mis-reasoned about the
bug.

</details>

2. The harness arm spent 1.8x the money and delivered 4.5x the outcomes. Why
   is cost per delivered outcome the number, not cost per attempt?

<details>
<summary>Answer</summary>

Cost per attempt flatters whichever arm fails fastest: the blind arm's cheap
attempts are mostly failures that still cost money and deliver nothing.
Dividing total spend by delivered outcomes counts the failures in the
denominator's price, which is the number a stakeholder's decision turns on —
the same distinction `mission.yaml` declares and stage 01 repeats.

</details>

## What this does not prove

**The loop's delivery rate is a property of this task set.** Two tasks,
three tiers, three runs; a harder or more ambiguous intent could widen or
narrow the gap. The feedback-only slice (2/12) shows the same tasks with
outcome feedback but no tools deliver far less than the loop does — the
mechanisms work as a set, and this read does not isolate which one carries
the weight.

**The harness does not decide whether the delivery is right.** Resolve 18/18
with generality 6/9 means the loop delivers what the test asserts, and what
the test does not assert can be wrong in three of nine patches. Delivery is
not correctness.

**Every external number above is a dated snapshot.** The AI Mode user count,
the ARC-AGI-3 harness settings, and the Epoch AI scaffold audit are 2026
records; the [paradigm survey](../../../reference/research/agentic-paradigm-restructuring.md)
states which claims it could not verify.

**Next:** [what the software around the model owns](../../02-agent-loop/harness-anatomy/) —
the same recorded arms, read as a control-plane audit: loop, routing,
approvals, tracing, recovery, and the sandbox underneath.
