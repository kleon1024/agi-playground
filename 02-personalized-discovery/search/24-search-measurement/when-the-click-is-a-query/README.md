---
status: verified
level: applied
base: scratch
label: When the click is a query
verified: 2026-08-07
---

# A failed query can be a recovered session

**Question:** [stage 24's search measurement](../) reads the query log.
This chapter reads the executed session case and asks whether a
zero-click query is a failure or a step in a recovery.

**Before this:** [stage 24 — search measurement](../) and its executed
zero-result model.

## The session, executed

The run ([record](runs/2026-08-07-query-session-read.md)) reads a
two-query session:

| query | outcome |
|---|---|
| heaphones | no click |
| headphones | click on d2 |

## The reading

Judged alone, the first query is a failure: zero clicks, zero results.
Judged as a session, it is the intent that the second query satisfied —
the user reformulated, and the reformulation is itself the correction
signal. Session metrics catch the recovery that per-query metrics call
a miss. The search report that counts only per-query success is
measuring the system at its worst moment, before the user fixed the
query for it.

## The fix and its trade

The fix is session metrics that catch the recovery that per-query
metrics call a miss. The executed two-query session prices the framing:
`heaphones` returns no click, then `headphones` clicks d2 — judged
alone the first query is a failure, and judged as a session it is the
intent the second query satisfied. The user reformulated, and the
reformulation is itself the correction signal; a report that counts
only per-query success measures the system at its worst moment, before
the user fixed the query for it.

The trade, named: session metrics depend on a session boundary
definition, and the reformulation signal is strongest when the second
query's success can be tied to the first query's intent — tying them
costs a session-attribution model and the risk of crediting a different
intent. The alternative, per-query verdicts, is simpler and
systematically pessimistic on exactly the recovered sessions that
measurement should reward.

## Who owns the loop

- **The analytics team** owns the session metric and its attribution
  between reformulated queries.
- **The product owner** owns the session definition the numbers are read
  against.
- **The data team** owns the reformulation evidence in the query log
  that ties the second query's success to the first query's intent.

## Evidence boundary

The executed two-query session (illustrative, deterministic). It
demonstrates the framing; real session metrics need a session
boundary definition, and the reformulation signal is strongest when the
second query's success can be tied to the first query's intent.

## Check your mental model

Answer each before opening it.

**1. Why is the first query not simply a miss?**

<details>
<summary>Answer</summary>

Because the session continued and succeeded. The user's intent was
stable across both queries; the first query failed to express it, the
second succeeded. Per-query measurement credits the second query alone
and counts the first as a failure — but the recovery is a property of
the session, and the system's job includes surviving the misspelling.

</details>

**2. What signal does the reformulation itself carry?**

<details>
<summary>Answer</summary>

It is free supervision: the user just told the system the first query
was wrong and what the right one is. Query-session data is how search
systems learn corrections (stage 19) and measure recovery — the
reformulation pair is an implicit labeled example, and counting it as a
failure throws that signal away.

</details>

## Next

Back to [stage 24](../), which measures the search funnel. The
[zero-matters detour](../when-the-zero-result-rate-matters/) prices
the queries that never recover.
