---
status: draft
level: reference
label: Reading Claude Code
---

# The terminal harness, read as five decisions

> Dated survey, 2026-08-14. Sources cited inline; behavior is read from
> official documentation, not re-measured here.

**Question:** the stage's claim is that every production harness is the
same five decisions — loop, tools, sandbox, context, permission — filled
in differently. What are Claude Code's five answers?

**The artifact this chapter follows** is a filled-in table: Claude Code as
five decisions, each with its documented mechanism and the failure it
exists to close.

## The five decisions

**Loop.** A terminal agent loop: read, plan, act, verify, with a default
approval-before-edit posture and subagents that run scoped tasks with
their own context ([Anthropic docs](https://code.claude.com/docs)).

**Tools.** Read/write files, bash, and MCP servers — the harness extends
by protocol, not by hard-coding.

**Sandbox.** Native sandboxing since v2.1.0: filesystem read scope plus a
SOCKS5 network proxy with a domain allowlist
([sandboxing docs](https://code.claude.com/docs/en/sandboxing)). Missing
either layer leaves a bypass, which is the same three-layer independence
the execution-environment stage demonstrates mechanically.

**Context.** Four CLAUDE.md scopes read at session start (enterprise,
project, local, user) plus auto-captured session memory — the static and
generated layers the context-and-memory stage names.

**Permission.** A permission ladder from "ask before every edit" to
pre-approved scopes, with hooks that gate specific commands or events.

## Why reading it this way matters

A harness read as five decisions can be compared, audited, and rebuilt.
The mission's own harness is the same five decisions at smaller scale; the
difference between it and Claude Code is scope and polish, not kind. The
"stop comparing agents without disclosing the harness" warning from the
stage becomes an executable reading skill instead of a slogan.

## What this does not say

It does not claim any of the five decisions is uniquely right — each is a
default, and the mission's runs show defaults have costs (the cheapest
tier's resolve-rate blindness). It maps the territory; the stage's
surveys and the mission's runs price the choices.
