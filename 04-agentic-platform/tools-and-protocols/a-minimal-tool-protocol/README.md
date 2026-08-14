---
status: verified
level: applied
base: scratch
label: A minimal tool protocol
verified: 2026-08-14
---

# Discover, invoke, error: a tool protocol in its smallest honest form

**Question:** the stage claims a tool protocol buys discoverability — an
agent can ask what tools exist, invoke one, and get a structured error
back, the same three primitives MCP formalizes on JSON-RPC 2.0. What does
that contract look like when the tools are real and the implementation is
small enough to read?

**The artifact this chapter follows** is the transcript: discovery, two
successful invocations on the mission's real task records, and two error
paths — an unknown parameter and a method outside the protocol.

By the end you will be able to read any tool integration (a function call,
an MCP server, an SDK agent) as the same contract, and say which layer of
the platform owns it.

**Before this:** the stage's contract claim. This chapter is its working
instance.

## The transcript, read

```text
== discovery ==
{"tools": {"list_tasks": {...}, "get_task": {...}, "target_tests": {...}}}

== get_task ==
{"task_id": "private-b81c414", "subject": "fix(serve): attend past the
first token in every cached decode step"}

== error path ==
{"error": {"code": -32602, "message": "unknown task_id"}}
{"error": {"code": -32601, "message": "method not found: no_such_method"}}
{"error": {"code": -32601, "message": "method not found: delete_task"}}
```

Three properties matter. **Discovery is a first-class operation**: the
client does not hard-code tools, it asks. **Errors are structured**: a
protocol distinguishes "bad parameter" (-32602) from "no such method"
(-32601), which a raw function call cannot. **The protocol is closed**:
`delete_task` fails because it is not in the protocol — the same boundary
that makes MCP servers auditable surfaces.

## What this proves and what it does not

It proves the contract mechanics on real task data with zero model calls.
It does not prove MCP's transport, auth, or ecosystem value — the stage's
surveys cover those. This is the floor the protocol question starts from.

**Next:** [from-function-calling-to-mcp](../) — the evolution that turned
this floor into a standard.
