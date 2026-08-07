---
status: verified
level: applied
base: none
label: When the tool errors
verified: 2026-08-07
---

# When the tool errors, who teaches the recovery turn?

**Question:** the parent chapter's real run ended at 0/6 rollouts producing a
single parseable tool call — a checkpoint that never saw a ReAct trajectory
could not even express an action. This detour asks the question that failure
leaves open: once a model can call a tool, what happens when the tool answers
with an error? Which failure modes do the three tools actually return, which
of them a blind retry can fix, and what does training data have to contain
for a model to learn the recovery turn rather than the loop?

**Before this:** [what turns a model into something that acts?](../) — the
harness loop, the grounding rule, and the claim that "retrying is only free
before something executed." This chapter turns that claim into a measured
taxonomy.

## The failure classes are the syllabus

The audit ([run record](runs/2026-08-07-recovery-audit.md)) injects every way
the three real tools can fail and records the actual observation. There are
seven classes, in two kinds:

| Failure class | Kind | First line of the observation | Blind retry resolves |
|---|---|---|---|
| missing file | raised | `ToolError: not a file: 'no-such-file.md'` | no |
| wrong directory | raised | `ToolError: not a directory: 'no-such-dir/'` | no |
| metacharacter refused | raised | `ToolError: command contains a shell metacharacter, refused` | no |
| command not allowlisted | raised | `ToolError: 'rm' is not in the command allowlist [...]` | no |
| timeout | raised | `ToolError: command timed out after 1.0s` | no |
| non-zero exit | returned | `exit=1` + traceback | no |
| output truncated | returned | first 8,000 bytes + truncation marker | no |

Two of the seven come back **returned**, not raised: `run_command` does not
throw on `exit=1` (it returns `exit=1` plus the traceback as an ordinary
observation), and `read_file` does not throw on a big file (it returns the
first 8,000 bytes with a truncation marker). The harness only raises
`ToolError` for the other five. That split is itself part of the syllabus: a
model has to notice the returned failures on its own — nothing points at
them.

## Zero of seven classes resolve by blind retry

The audit plays a blind-retry policy — on any failure, re-issue the exact
same call. Result: **0/7** classes resolve; every retry returns the identical
failing observation. A loop with a retry counter is not a recovery mechanism;
it is a mechanism for paying the same failed turn again, which is the parent
chapter's "retrying is only free before something executed" made quantitative.

That is the gap the clean-success trajectory leaves open. A corpus filtered
to "tool calls that worked" contains zero of the turns above, so a model
trained on it has no imitation target for what to do when the observation
starts with `ToolError:` or `exit=1`. The parent's real run measured the
prerequisite failure — 0/6 rollouts never produced the shape of a tool call —
and this audit measures the next one: even a model that can express a call
has seven failure classes to recover from, and the training data has to
contain examples of each.

## The recovery families: inspect, re-scope, make it safe to redo

The recovery planner in the audit is a fixed per-class map, and every action
is executed for real: **7/7** classes resolve. The seven actions fall into
three families, and naming the family is what makes the pattern transfer to a
tool set that is not this one.

**Inspect** — the failure says something is *not where you thought*, so the
next turn gathers information before choosing the next action. Missing file,
wrong directory, and the non-allowlisted command are all this: the error
names what does not exist (or what does), and the recovery is a `list_dir` or
a `read_file`, not another attempt at the same guess. The user's failing-test
example is this family: `pytest` fails with a traceback, the agent reads the
function, sees `text.strip()` crash on `None`, and only then edits.

**Re-scope** — the failure says the *call* was wrong-sized, not the world.
The metacharacter refusal and the truncated read are this: the observation
tells you to express the command differently (a single allowlisted command
instead of a shell chain; a `grep` or `head` slice instead of a full read).
The timeout sits here too: re-running `slow.py` pays the same 1.0s and times
out again, while `ls` tells you what exists.

**Make it safe to redo** — the failure says *something may already have
happened*, and the correct recovery is idempotency or state inspection, not a
retry. This is the class blind retry is actively dangerous on, and it gets
its own measurement below.

## The already-executed trap

The audit runs `python3 slow_write.py` — a command that writes `marker.txt`
and then sleeps — against the 1.0s timeout. The observation is
`ToolError: command timed out after 1.0s`, and yet **`marker.txt` exists with
content `done`**: the timeout killed the process after its side effect
landed. The observation cannot tell you that, because the observation is
about *time*, not *state*.

Blind retry on this class is not merely useless, it is destructive: the
command runs its side effect again. The recovery is to make the command
idempotent (a write keyed on something stable, an append guard) or to inspect
state before re-running — `list_dir`/`read_file` to check whether the write
already landed. This is exactly the boundary the parent chapter drew: retry
is free only before something executed, and "did it execute?" is a question
the retry counter cannot answer.

## What the training data has to contain

Putting recovery in the data is the same decision [mid-training section 7]
(../../02-pretrain/mid-training/#7-length-noise-and-the-mix) names: noise is
what teaches recovery. A trajectory that resolves through error, inspect,
correct, re-run teaches three turns a clean-success trajectory never shows —
and the measured scale of the effect is external, not this toy: PALADIN
([arXiv:2509.25238](https://arxiv.org/abs/2509.25238), Sep 2025) injects
failures into 50,000+ recovery-annotated ToolBench trajectories and trains
with LoRA, lifting LLaMA-8B's tool-success rate from 17.5% to 78.7% — "more
than fourfold" — over a model trained on success-only trajectories. Chen et
al., [Teaching Large Language Models to Self-Debug](https://arxiv.org/abs/2304.05128)
(ICLR 2024), is the mechanism at a smaller scale: a model that explains its
own failed execution and re-runs resolves a class of errors a retry-only
policy cannot. Both are cited, dated, and outside this repository's runs; the
shape they agree on is the shape this chapter measures: the failure classes
are enumerable, none resolve by retry alone, and the recovery turns have to
be in the imitation data.

## Who owns it

- **The trace-construction team** owns error injection: the mix must contain
  real failures (timeouts, `exit=1`, truncation, empty results), not only
  clean successes, and the placement — error early, recover, resolve — is
  part of the format. Filtering to successful trajectories is the pipeline
  decision that silently removes the recovery syllabus.
- **The eval team** owns a per-failure-class recovery rate, not just task
  success: success can be reached by luck or by recovery, and the two are
  different capabilities. The audit's 7-class table is the shape of that
  eval surface.
- **The harness team** owns the idempotency surface that makes retry safe:
  stable command keys, state-inspection tools, and the rule that a
  possibly-executed call is never re-run without checking.
- **The model team** owns the data-composition consequence: this stage's
  0/6 real run showed the format gap, and the recovery taxonomy shows the
  next one — both are fixed in the data, not by a stronger prompt.

When nobody owns the failure classes, the symptom shows up as a model that
"sometimes gets stuck": it retries a failing command, re-reads the same
missing path, or times out repeatedly — behavior that looks like model
capability and is a training-data composition failure wearing a different
label.

## What this chapter does not prove

This is a mechanism demo. The recovery planner is a fixed scripted policy,
not a trained model, so the audit proves the failure classes exist, what
their observations look like, and that blind retry resolves none of them; it
does not train a model and therefore does not measure whether recovery
trajectories would teach the planner's actions. That magnitude is cited to
PALADIN and Chen et al. above rather than reproduced here. The audit also
shortens the command timeout to 1.0s for wall-clock reasons; the production
default in `tools.py` is 10.0s, and the mechanism is identical.

## Check your mental model

Answer each before opening it.

**1. Two of the seven failures are returned, not raised. Why does that
distinction matter for training data?**

<details>
<summary>Answer</summary>

A raised `ToolError` is pointed at by the harness — the observation begins
"tool error". A returned failure (`exit=1`, truncated read) arrives as an
ordinary observation with the signal embedded in the text; the model has to
notice the failure before it can recover from it. Training data that only
contains raised failures teaches the recovery but not the detection; a
production trace contains both, and a model that cannot tell `exit=1` from a
successful result will try to "recover" from output that is not failing.

</details>

**2. Why is blind retry destructive for the timeout class but merely useless
for the missing-file class?**

<details>
<summary>Answer</summary>

For a missing file, nothing executed — re-running the read changes nothing
and resolves nothing; it is wasted turns. For a timeout, the command may have
executed part or all of its side effect before being killed (the audit's
`slow_write.py` leaves `marker.txt` behind despite the timeout error), so
re-running can duplicate a write or a request that already landed. The
difference is whether the call crossed the "something executed" boundary,
which is exactly the parent chapter's retry rule; the timeout class is where
that boundary is invisible from the observation.

</details>

**3. The recovery planner is scripted. What does it still prove that a model
run would not?**

<details>
<summary>Answer</summary>

It isolates the failure taxonomy from model quality: the seven classes, their
observations, and the 0/7-versus-7/7 contrast are measured against the real
tools with the model held out of the picture, so a later model run that fails
can be attributed to the model not having learned the recovery turns rather
than to the failure classes being unenumerable or unresolvable. A model run
alone cannot separate "the data never taught it" from "the failure is
unrecoverable"; the audit pins the second claim first.

</details>

## Next

Return to [what turns a model into something that acts?](../README.md) with
the failure taxonomy in hand — the recovery path the parent chapter stopped
at "return the error as an observation" is the syllabus a training-data
pipeline has to populate. The composition half of the answer is [mid-training
section 7](../../02-pretrain/mid-training/#7-length-noise-and-the-mix), and
[stage 07 — eval](../../07-eval/) is where a per-class recovery rate becomes a
measured gate.
