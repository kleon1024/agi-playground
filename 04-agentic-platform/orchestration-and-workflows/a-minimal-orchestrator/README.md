---
status: verified
level: applied
base: scratch
label: A minimal orchestrator
verified: 2026-08-14
---

# The skeleton first, the model second

**Question:** the stage claims structured work belongs in a deterministic
skeleton with LLM cells — every step has an owner, an input, an output,
and a place in the record — and that free multi-agent coordination is what
fails in production. What is the skeleton, mechanically?

**The artifact this chapter follows** is the dispatch record: two real
tasks, two deterministic workers each, and the summary that says 2/2
passed. No model was called, which is the point — the skeleton is shown
before any cell is filled.

By the end you will be able to take any orchestration claim and ask the
one question this chapter makes concrete: is there a skeleton, or is the
coordination left to conversation?

**Before this:** the stage's orchestrator-vs-free-agent argument, with its
production failure record. This chapter is the deterministic contrast.

## The record, read

```text
[PASS] private-b81c414: task-record=True; verification-contract=True
[PASS] private-354c352: task-record=True; verification-contract=True

2/2 tasks passed all deterministic gates; no model called.
```

Two workers, each owning one bounded check. The orchestrator does not
negotiate with the workers; it dispatches, collects, and records. That is
the opposite of the free multi-agent failure mode the stage documents —
where agents negotiate until a parent steps in with a termination
condition. Here termination is structural: the dispatch plan is fixed and
the record is complete by construction.

## What this proves and what it does not

It proves the skeleton mechanics on the mission's real task set. It does
not prove the skeleton improves quality — the model cells are absent by
design, and the stage's surveys attribute the quality claim to the
production record (Anthropic's guidance, AutoGen's failures). The skeleton
is the substrate the stage argues every production workflow needs; this
chapter shows it, it does not measure it.

**Next:** [spec-driven-orchestration](../) — how the skeleton gets written
down before execution, from an issue tracker.
