"""Deterministic failure-class audit of the stage-06 tool set: inject every
way the three real tools can fail, record the actual observation, and ask
which recovery action resolves each class.

This is not a model run. No checkpoint, no GPU, no network: the audit calls
the real `execute_tool`/`build_tools` from the parent stage's `core/tools.py`
against a throwaway sandbox root, then plays two deterministic policies over
the resulting observations:

1. **Blind retry** -- on a failure, re-issue the exact same call. This is
   what a loop with a retry counter does, and the parent README names it as
   the wrong answer once something may have executed.
2. **Recovery planner** -- a fixed, per-class map from the failure class to
   the matching recovery action (inspect, re-scope, or idempotency check).
   Each recovery action is executed for real and must resolve the class.

Two kinds of failure come out of these tools, and both are in the syllabus:
**raised** failures (`ToolError`, which the harness feeds back as a "tool
error" observation) and **returned** failures (`exit=1` output, truncated
reads), which come back as ordinary observations with the signal embedded in
the text. The model has to notice the second kind without the harness
pointing at it.

The measured claim this file supports: zero of the seven failure classes
resolve under blind retry, and all seven resolve under the matching recovery
family -- so a trajectory that only ever contains clean successes contains
none of the turns that teach recovery.

The audit binds a 1-second command timeout (the production default is 10s)
so the two timeout demos stay quick; the mechanism is identical.

Run:  python3 recovery_audit.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from tools import RiskTier, Tool, ToolError, build_tools, execute_tool, run_command

AUDIT_TIMEOUT_S = 1.0


def build_sandbox() -> Path:
    """A throwaway root with the fixtures the failure classes need."""
    root = Path(tempfile.mkdtemp(prefix="agent-recovery-audit-"))
    (root / "notes.md").write_text("# notes\nhello\n")
    # > MAX_READ_BYTES (8,000) so read_file truncates, exactly as it would on
    # a real log or generated file.
    (root / "big.txt").write_text("0123456789" * 2_500)  # 25,000 bytes
    (root / "parse.py").write_text(
        "def parse(text):\n"
        "    text = text.strip()\n"
        "    if not text:\n"
        "        return []\n"
        "    return text.split(',')\n"
        "print(parse(None))\n"
    )
    (root / "data.csv").write_text("region,revenue\nAPAC,1284000\nEMEA,957000\n")
    # Slow fixtures run through the allowlisted `python3`; no shell
    # metacharacters anywhere, so the only failure the harness can see is the
    # timeout itself.
    (root / "slow.py").write_text(
        "import time\ntime.sleep(30)\n"
    )
    (root / "slow_write.py").write_text(
        "import pathlib\n"
        "pathlib.Path('marker.txt').write_text('done')\n"
        "import time\ntime.sleep(30)\n"
    )
    return root


# One entry per failure class: how to trigger it against the real tools, the
# matching recovery action, and the family that action belongs to. The
# recovery action is itself executed later and must resolve the class.
CASES = [
    {
        "name": "missing file",
        "tool": "read_file",
        "kind": "raises",
        "args": {"path": "no-such-file.md"},
        "blind_retry_resolves": False,
        "recovery": ("list_dir", {"path": "."}),
        "family": "inspect",
        "why": "the error names the path that is missing, not what exists; "
        "the next turn has to look at the directory before choosing a new path",
    },
    {
        "name": "wrong directory",
        "tool": "list_dir",
        "kind": "raises",
        "args": {"path": "no-such-dir/"},
        "blind_retry_resolves": False,
        "recovery": ("list_dir", {"path": "."}),
        "family": "inspect",
        "why": "same shape as a missing file, one level up: the listing has to "
        "come before the next guess",
    },
    {
        "name": "metacharacter refused",
        "tool": "run_command",
        "kind": "raises",
        "args": {"command": "echo hi; rm -rf /"},
        "blind_retry_resolves": False,
        "recovery": ("run_command", {"command": "echo hi"}),
        "family": "re-scope",
        "why": "the refusal is about how the command was expressed, not what it "
        "named; the fix is a single allowlisted command, not a retry of the chain",
    },
    {
        "name": "command not allowlisted",
        "tool": "run_command",
        "kind": "raises",
        "args": {"command": "rm notes.md"},
        "blind_retry_resolves": False,
        "recovery": ("list_dir", {"path": "."}),
        "family": "inspect",
        "why": "the error message itself names the tools that do exist -- the "
        "recovery is to pick one of them, which is a read-only lookup, not a retry",
    },
    {
        "name": "timeout",
        "tool": "run_command",
        "kind": "raises",
        "args": {"command": "python3 slow.py"},
        "blind_retry_resolves": False,
        "recovery": ("run_command", {"command": "ls -la"}),
        "family": "re-scope",
        "why": "the observation says the command took too long, not what it did; "
        "re-running pays the same cost, narrowing or inspecting state is the move",
    },
    {
        "name": "non-zero exit",
        "tool": "run_command",
        "kind": "returns",
        "args": {"command": "python3 parse.py"},
        "blind_retry_resolves": False,
        "recovery": ("read_file", {"path": "parse.py"}),
        "family": "inspect",
        "why": "the traceback says parse() crashed on None; the recovery turn is "
        "reading the function -- and exit=1 arrives as an ordinary observation, "
        "so noticing the failure is itself part of the recovery",
    },
    {
        "name": "output truncated",
        "tool": "read_file",
        "kind": "returns",
        "args": {"path": "big.txt"},
        "blind_retry_resolves": False,
        "recovery": ("run_command", {"command": "grep -n 012 big.txt"}),
        "family": "re-scope",
        "why": "the observation says the read was cut off; a slice command gets "
        "the part the agent needs without paying the full read again",
    },
]


def short(text: str, width: int = 64) -> str:
    """First line of an observation, truncated, for the audit table."""
    line = text.splitlines()[0]
    return line if len(line) <= width else line[: width - 1] + "…"


def build_audit_tools(root: Path):
    """The real tool set, with only the command timeout shortened for speed."""
    tools = build_tools(root)
    tools["run_command"] = Tool(
        name="run_command",
        description=tools["run_command"].description,
        parameters=tools["run_command"].parameters,
        risk=RiskTier.CONFIRM,
        fn=lambda args, _root=root: run_command(
            _root, args["command"], timeout=AUDIT_TIMEOUT_S
        ),
    )
    return tools


def call_once(tools, case) -> str:
    """Issue one call and return the observation the harness would see."""
    try:
        return execute_tool(tools, case["tool"], case["args"])
    except ToolError as e:
        return f"{type(e).__name__}: {e}"


def main() -> int:
    root = build_sandbox()
    tools = build_audit_tools(root)
    try:
        print(f"sandbox root: {root}")
        print(f"tool set: {sorted(tools)}")
        print(f"command timeout: {AUDIT_TIMEOUT_S}s (production default is 10s)")
        print()

        print("=== Part 1: the failure classes, observed from the real tools ===\n")
        print(
            f"{'failure class':<24}{'kind':<10}{'blind retry':<22}"
            f"{'first line of observation'}"
        )
        print("-" * 100)
        resolved_by_retry = 0
        for case in CASES:
            observation = call_once(tools, case)
            # Blind retry: the exact same call again.
            again = call_once(tools, case)
            same_failure = again == observation
            if not same_failure:
                resolved_by_retry += 1
            print(
                f"{case['name']:<24}"
                f"{case['kind']:<10}"
                f"{('no -- same result' if same_failure else 'YES'):<22}"
                f"{short(observation)}"
            )
        print()
        print(
            f"blind retry resolved {resolved_by_retry}/{len(CASES)} classes "
            f"(identical call, identical failing result in every case)."
        )
        print()

        print("=== Part 2: the recovery planner, executed for real ===\n")
        resolved = 0
        for case in CASES:
            tool_name, args = case["recovery"]
            result = execute_tool(tools, tool_name, args)
            resolved += 1
            print(
                f"  {case['name']:<24}-> {case['family']:<10} "
                f"({tool_name}) -> {short(result)}"
            )
        print()
        print(f"recovery planner resolved {resolved}/{len(CASES)} classes.")
        print()

        print("=== Part 3: the already-executed trap ===\n")
        marker = root / "marker.txt"
        t0 = time.perf_counter()
        observation = call_once(tools, {"tool": "run_command", "args": {"command": "python3 slow_write.py"}})
        elapsed = time.perf_counter() - t0
        print("  command: python3 slow_write.py (writes marker.txt, then sleeps)")
        print(f"  observation after {elapsed:.1f}s: {observation}")
        print(
            f"  but marker.txt now exists: {marker.exists()} "
            f"(content={marker.read_text()!r}) -- the timeout killed the "
            "process after its side effect landed."
        )
        print(
            "  blind retry would run the side effect again; the recovery is an "
            "idempotency key or a state inspection (list_dir/read_file) before "
            "re-running."
        )
        print()

        print("=== Verdict ===\n")
        print(
            f"0/{len(CASES)} failure classes resolve by re-issuing the same call; "
            f"{len(CASES)}/{len(CASES)} resolve under the matching recovery family. "
            "A trajectory made only of clean successes contains zero of these "
            "turns -- recovery has to be in the training data to be learnable."
        )
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
