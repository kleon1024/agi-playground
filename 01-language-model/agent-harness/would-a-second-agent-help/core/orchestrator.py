"""A supervisor-and-workers orchestrator against a fake, deterministic backend.

The single-agent harness in `01-language-model/agent-harness/core/`
has one loop, one context, one backend. This file asks what changes the
moment a parent delegates to more than one child, and answers with code
instead of a diagram:

1. **The parallel-safety rule, checked, not asserted.** `independent()` and
   `schedule()` decide which tasks may share a batch: neither may depend on
   the other, and neither's writes may collide with the other's reads or
   writes. The demo task graph below includes a pair that *looks*
   independent -- nothing declares a dependency between them -- but shares a
   write, and the scheduler still forces it into its own batch. That is the
   rule from the capability README doing real work: two subtasks run in
   parallel only when they share no output and have no data dependency,
   whether or not anyone remembered to write the dependency down.

2. **The structured-return contract.** A worker's raw text must parse into a
   fixed `STATUS: / ARTIFACT:` shape before the supervisor acts on it.
   `parse_structured_return` raises on anything else -- including
   perfectly clear English a human would have no trouble reading -- because
   the parent here is a program, not a person, and prose is not something a
   program can safely branch on.

3. **Total token cost, not just task count.** Every delegated task pays a
   fixed dispatch-and-return tax (`SUPERVISOR_OVERHEAD_TOKENS`,
   `HANDOFF_TAX_TOKENS`) on top of the same raw work a single agent would
   have done directly. `single_agent_equivalent_cost` computes what the
   identical work costs one agent with no delegation at all, so the two
   totals can be compared at the end -- the equal-budget comparison the
   capability README insists on, computed rather than asserted.

No GPU, no API key, no network: the "backend" is a plain dict of scripted
worker responses, keyed by task id, in the same spirit as the `FakeBackend`
in the stage-06 harness lesson this capability builds on.

Run:
    python orchestrator.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# ---------------------------------------------------------------------------
# Token accounting: the same chars/4 stand-in `ContextManager` uses in the
# stage-06 harness lesson. Reproduced locally rather than imported -- this
# file demonstrates one capability in isolation and should not reach across
# lessons for a one-line helper.
# ---------------------------------------------------------------------------


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# The task graph. reads/writes/depends_on are what make the parallel-safety
# rule checkable instead of asserted.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Task:
    id: str
    description: str
    reads: frozenset[str] = frozenset()
    writes: frozenset[str] = frozenset()
    depends_on: frozenset[str] = frozenset()


def independent(a: Task, b: Task) -> bool:
    """Two tasks may share a batch only if neither depends on the other and
    neither's writes collide with the other's reads or writes.

    A shared write, or a read of what the other writes, is a data dependency
    whether or not anyone declared it as one in `depends_on` -- this function
    catches that case rather than trusting the task list to have named it.
    """
    if a.id in b.depends_on or b.id in a.depends_on:
        return False
    if a.writes & b.writes:
        return False
    return not ((a.writes & b.reads) or (b.writes & a.reads))


def schedule(tasks: list[Task]) -> list[list[str]]:
    """Greedily batch tasks whose dependencies are already satisfied and
    which are pairwise independent of everything already placed in the
    current batch. A batch is what "ran in parallel" means here; batch order
    is deterministic because ties break on input order, never on anything
    resembling randomness.
    """
    remaining = list(tasks)
    done: set[str] = set()
    batches: list[list[str]] = []
    while remaining:
        batch: list[Task] = []
        for t in remaining:
            if not t.depends_on <= done:
                continue
            if all(independent(t, placed) for placed in batch):
                batch.append(t)
        if not batch:
            raise RuntimeError(
                "no schedulable task remains -- a cyclic or unsatisfiable "
                "dependency exists in this task graph"
            )
        batches.append([t.id for t in batch])
        placed_ids = {t.id for t in batch}
        done.update(placed_ids)
        remaining = [t for t in remaining if t.id not in placed_ids]
    return batches


# ---------------------------------------------------------------------------
# The structured-return contract.
# ---------------------------------------------------------------------------


class MalformedReturn(Exception):
    """A worker's raw text did not parse into the STATUS:/ARTIFACT: contract.

    The supervisor catches this rather than crashing -- the same
    recovery-not-crash discipline the stage-06 harness applies to a malformed
    tool call -- but unlike a malformed tool call, there is no cheap retry
    here: the tokens were already spent producing text the parent cannot act
    on.
    """


@dataclass
class StructuredReturn:
    status: Literal["ok", "error"]
    artifact: str


def parse_structured_return(raw: str) -> StructuredReturn:
    fields: dict[str, str] = {}
    for line in raw.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip().upper()] = value.strip()
    if "STATUS" not in fields or "ARTIFACT" not in fields:
        raise MalformedReturn(
            f"expected STATUS: and ARTIFACT: lines, the parent cannot act on: {raw!r}"
        )
    if fields["STATUS"] not in ("ok", "error"):
        raise MalformedReturn(f"unknown STATUS {fields['STATUS']!r}")
    return StructuredReturn(status=fields["STATUS"], artifact=fields["ARTIFACT"])


# ---------------------------------------------------------------------------
# The supervisor: schedules, dispatches to the fake backend, parses returns,
# and accounts for every token spent along the way.
# ---------------------------------------------------------------------------

WorkerBackend = dict[str, str]  # task id -> the worker's scripted raw response

HANDOFF_TAX_TOKENS = 60  # cost of one lossy parent<->child serialization boundary
SUPERVISOR_OVERHEAD_TOKENS = 40  # dispatch instructions the supervisor writes per task


@dataclass
class TaskResult:
    task_id: str
    tokens: int
    handoffs: int
    parsed: StructuredReturn | None
    error: str | None = None


def run_supervisor(
    tasks: list[Task], worker_backend: WorkerBackend
) -> tuple[list[TaskResult], list[list[str]]]:
    """Run every task through the schedule computed above.

    Every delegated task pays two handoffs -- the supervisor's dispatch to
    the worker, and the worker's structured return back -- whether or not
    that particular task benefited from being a separate agent at all. That
    fixed tax, paid regardless of benefit, is what "every handoff is a lossy
    serialization" costs in tokens rather than in prose.
    """
    batches = schedule(tasks)
    by_id = {t.id: t for t in tasks}
    results: list[TaskResult] = []
    for batch in batches:
        for task_id in batch:
            task = by_id[task_id]
            raw = worker_backend[task_id]
            tokens = (
                estimate_tokens(task.description)
                + estimate_tokens(raw)
                + SUPERVISOR_OVERHEAD_TOKENS
                + 2 * HANDOFF_TAX_TOKENS
            )
            try:
                parsed = parse_structured_return(raw)
                results.append(TaskResult(task_id, tokens, handoffs=2, parsed=parsed))
            except MalformedReturn as e:
                # The tokens were spent regardless -- a malformed return is
                # not free just because the parent cannot act on it.
                results.append(
                    TaskResult(task_id, tokens, handoffs=2, parsed=None, error=str(e))
                )
    return results, batches


def single_agent_equivalent_cost(tasks: list[Task], worker_backend: WorkerBackend) -> int:
    """What the identical work costs one agent doing it directly in its own
    running context: no dispatch, no structured-return parsing, no handoff
    tax -- just reading each task description and producing each answer in
    turn. This is the baseline the multi-agent total must be measured
    against at matched cost, not against a single agent given a fraction of
    the budget.
    """
    return sum(
        estimate_tokens(task.description) + estimate_tokens(worker_backend[task.id])
        for task in tasks
    )


# ---------------------------------------------------------------------------
# The demo: four tasks over a shared repository-audit scenario, one pair of
# which conflicts on a write that nothing declares as a dependency.
# ---------------------------------------------------------------------------


def demo_tasks() -> tuple[list[Task], WorkerBackend]:
    tasks = [
        Task(
            id="scan_a",
            description="scan module a for TODO comments and unresolved markers",
            reads=frozenset({"repo"}),
            writes=frozenset({"report_a"}),
        ),
        Task(
            id="scan_b",
            description="scan module b for TODO comments and unresolved markers",
            reads=frozenset({"repo"}),
            writes=frozenset({"report_b"}),
        ),
        Task(
            id="merge",
            description="merge both scan reports into one summary",
            reads=frozenset({"report_a", "report_b"}),
            writes=frozenset({"final_report"}),
            depends_on=frozenset({"scan_a", "scan_b"}),
        ),
        Task(
            id="rescan_a",
            description="re-scan module a under a stricter rule",
            reads=frozenset({"repo"}),
            writes=frozenset({"report_a"}),
            # No depends_on entry names scan_a -- but it writes what scan_a
            # writes, which is exactly the conflict schedule() must catch on
            # its own.
        ),
    ]
    worker_backend: WorkerBackend = {
        "scan_a": "STATUS: ok\nARTIFACT: 3 TODOs found in module_a",
        "scan_b": "STATUS: ok\nARTIFACT: 1 TODO found in module_b",
        "merge": "STATUS: ok\nARTIFACT: report.md written, 4 TODOs total",
        # Deliberately malformed: a human would understand this fine, but it
        # has no STATUS: or ARTIFACT: line, so the parent cannot act on it.
        "rescan_a": "Looks like module a still has a couple of TODOs, seems fine overall.",
    }
    return tasks, worker_backend


def main() -> None:
    tasks, worker_backend = demo_tasks()

    results, batches = run_supervisor(tasks, worker_backend)
    supervisor_total = sum(r.tokens for r in results)
    supervisor_handoffs = sum(r.handoffs for r in results)
    baseline_total = single_agent_equivalent_cost(tasks, worker_backend)

    print("schedule (batches run in order; tasks within a batch run concurrently):")
    for i, batch in enumerate(batches):
        print(f"  batch {i}: {batch}")
    print()

    print("per-task results:")
    for r in results:
        if r.parsed is not None:
            print(f"  {r.task_id}: ok -- {r.parsed.artifact}  ({r.tokens} tokens)")
        else:
            print(f"  {r.task_id}: UNUSABLE RETURN -- {r.error}  ({r.tokens} tokens, spent anyway)")
    print()

    print(f"wall-clock: {len(batches)} batches vs {len(tasks)} sequential single-agent steps")
    print(f"lossy handoffs: {supervisor_handoffs}")
    print(f"supervisor+workers total tokens: {supervisor_total}")
    print(f"single-agent equivalent cost:    {baseline_total}")
    print(
        f"multi-agent cost is {supervisor_total / baseline_total:.2f}x the "
        "single-agent baseline for the identical underlying work"
    )


if __name__ == "__main__":
    main()
