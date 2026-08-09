---
status: verified
level: frontier
base: none
label: Harness anatomy
verified: 2026-08-08
---

# What does the software around the model own?

**Question:** every agent score in this mission is a function of the model
*and* the loop around it. When the same model, same tasks, and three tiers
move delivery from 4/18 to 18/18 by changing only the harness, what exactly
is the software around the model doing — and how do you audit that a
production harness is doing it?

**The artifact this chapter follows** is the same recorded arms, read as a
control-plane audit:

```text
arm                    n     delivered   $/delivered   turns   tokens
no-harness            18    4/18         $1.2859        -       45k
harness (private)     18    18/18        $0.5066       10.5     607k
harness (public)       6    6/6          $0.1068        9.8     410k
closing-the-loop      12    2/12         $1.5256        -       50k
```

By the end you will be able to read any production harness (Claude Code,
Codex, Antigravity, this repo's own) as the same two planes — a control plane
that decides and records, and a compute plane that executes — and say which
columns a score must disclose before it means anything.

**Before this:** [the intent-to-delivery chapter](../../05-report/intent-to-delivery/),
whose gap the harness closes, and the harness this mission actually runs,
built in [topic 01 stage 06](../../../01-language-model/06-agent/).

## The failure mode: a score you cannot attribute

The symptom is a benchmark number with the model's name on it. OpenAI's own
ARC-AGI-3 record shows the same model scoring 13.3% on one harness and 38.3%
on another (retained reasoning plus compaction, model unchanged) — roughly
3x with 6x fewer output tokens
([the recorded landscape pass](../../harness-effects-landscape.md)). Epoch
AI's SWE-bench audit found the same: one model moving 62.3% to 70.2% purely
by scaffold
([reported 2026-07-03](https://futureagi.com/blog/coding-agent-harness-benchmark/)).
The cost of ignoring this is a routing decision made on a number that belongs
to the harness, not the model — which is exactly this mission's stage-03
finding inverted: there, every tier resolved everything, so resolve rate told
the routing decision nothing at all.

This mission's own table is the same phenomenon with the variable held in
the repo's control. The harness arm's mean transcript is 607k tokens against
the blind arm's 45k: the loop writes tool observations and scored test
output back into the context, and that transcript is the deliverable's
grounding. Turns average 10.5 in the private harness arm and 9.8 in the
public one — the loop is a retry ladder, not a single call wearing tools.

## The two planes

A harness is two planes, and confusing them is how a control-plane defect
gets misread as a model defect.

**The control plane decides and records.** It owns the loop and its stop
conditions, routing between models and tools, approvals, tracing, and
recovery. In this repo's own harness
([topic 01 stage 06](../../../01-language-model/06-agent/)) that is:

- the ReAct loop with exactly two exits (done, or a hard cap) — the retry
  ladder the audit table counts as `turns`;
- a permission ladder with real tiers: `read_file` and `list_dir`
  auto-allowed and confined to the sandbox root, `run_command` the single
  dangerous tool, checked on the parsed first token, no `shell=True`, a hard
  timeout, output truncation, a working-directory jail, and no network;
- a grounding rule (every decision follows a real observation) and a
  context-management policy that collapses superseded reads instead of
  dropping decisions.

**The compute plane executes.** It is the sandbox and jail that make a
permission decision meaningful — `tools.resolve_in_jail` in this repo, the
container in production harnesses. A permission ladder without a jail is a
policy written in prose; the guardrail check on the diff (a patch touching a
test file is scored as a failure) is enforced programmatically, never asked
for in a system prompt.

## Three production harnesses, read the same way

| Harness | Control plane | Compute plane | Recorded as |
|---|---|---|---|
| Claude Code | TAOR loop, permission model split into `permissionMode`, hooks, and declarative allow-deny rules; `PreToolUse` hooks still run under `bypassPermissions` ([permissions docs](https://code.claude.com/docs/en/security)) | OS-level container; hooks can ask, allow, or deny | a score that depends on the hook and permission configuration, which is why the docs treat them as part of the harness contract |
| Codex | Rust rewrite of the CLI into a multi-entry harness: `codex-cli`, an app-server JSON-RPC layer, sandbox, plugin market, MCP integration, and Cloud Tasks ([source-analysis pass, 2026-05-26](https://xiaonancs.github.io/codex-source-analysis/)) | sandbox per task, plugin permissions | the same architecture this mission's loop implements by hand, at product scale |
| Antigravity | a local Go harness binary with a native tool set (filesystem, shell, subagents, web search, user), co-optimized with the Gemini model it serves ([Google I/O 2026, 2026-05-18](https://antigravity.google/blog/io-2026/)) | native tools compiled into the harness rather than an external agent framework | evidence that harness and model co-design is now a product strategy, not an implementation detail |

The throughline: every one of these is the repo's own five decisions — loop,
tool schemas, sandboxing, context management, permission model — elaborated
for production. None of them adds a sixth decision that the minimal harness
does not already make.

## The fix and its trade

The fix is the audit itself: a score is published with its control-plane
columns — loop shape, tool set, context policy, retry logic, permission
configuration — the way this run's table carries turns, tokens, cost per
delivered, and wall-clock. The trade is that the audit is more expensive
than the number it disciplines: a harness table requires the harness to be
instrumented, which is why published results usually disclose only the model.
The repo's own answer to that trade is mechanical: stage 05's report reads
only committed JSONL and prints `CANNOT DETERMINE` for any acceptance bullet
the recorded columns cannot answer.

The second half of the fix is the separation of planes: the control plane is
the part a governance layer can audit (next chapter), and the compute plane
is the part that limits blast radius when the control plane is wrong. A
harness that cannot state which is which has already failed the audit.

## Who owns the loop

- **The harness owner** owns the control-plane columns and their
  disclosure — the same contract the [eval-gates chapter
  (whose harness produced the number?)](../../../01-language-model/07-eval/whose-harness/)
  demands of every published agent score.
- **The infra owner** owns the compute plane and its blast radius: jail,
  network cut, timeout, and what a runaway loop can actually touch.
- **The product owner** owns the routing consequence: a table like the one
  above is the input to "which tier do I point at which task," and a score
  without its columns is not an input at all.

## Check your mental model

1. The harness arm's mean transcript is 607k tokens; the blind arm's is 45k.
   Why is the transcript itself part of the harness, not an inefficiency?

<details>
<summary>Answer</summary>

Because the loop writes real observations back into context — tool output,
the actual test result — and the next decision is grounded on them. That
grounding is the mechanism that moves delivery from 4/18 to 18/18, and it is
the same mechanism OpenAI's ARC-AGI-3 post is about (retaining the model's
own reasoning and compacting instead of truncating). A transcript is not
overhead; it is the harness's memory, and its policy is a control-plane
decision.

</details>

2. Why is the permission ladder meaningless without the jail?

<details>
<summary>Answer</summary>

A permission decision ("you may run this command") only limits what the
model can touch if the command executes inside a confined root with no
network and a hard timeout. Without the jail, the allowlist is a request,
not a guarantee — the same reason the test-tampering guardrail checks the
diff instead of asking the model to behave.

</details>

## What this does not prove

**The audit table is descriptive, not comparative across vendors.** The
three production harnesses are read as architecture, from dated public
records; this mission did not run any of them, and the table does not rank
them.

**The control-plane columns explain the gap; they do not isolate it.** The
harness differs from the blind arm in retry, grounding, and verification at
once, and the closing-the-loop slice (feedback but no tools: 2/12) shows the
mechanisms act as a set — no single column was ablated here.

**The transcript size is a property of this task set.** Two tasks fit in
context by design; the mission explicitly says nothing about repositories
too large for the model's window, where context management stops being a
policy choice and becomes the binding constraint.

**Next:** [what a governed agent actually does](../../04-how-it-fails/control-plane-governance/)
— the same loop, read as a control plane that must reconcile, gate, and
survive an assumed adversary.
