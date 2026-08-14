"""A minimal three-layer sandbox for the mission-04 harness.

Layers, in the order an agent's tool call crosses them:

1. **filesystem** — only the task workdir is writable; anything outside it
   is read-only from the agent's point of view.
2. **network** — commands are checked against a policy before execution;
   no network-bearing command passes unless the policy allows it.
3. **approval** — destructive commands require an explicit `--allow-destructive`
   flag on the sandbox, not on the command.

This is a mechanism demo, not production isolation: on macOS it cannot
enforce kernel-level boundaries (no seccomp, no LSM), so the three layers
are policy checks in front of `subprocess.run`. What it demonstrates is the
shape of the decision — each layer is independent, and a command that skips
one layer still has to cross the next. The industry versions of these layers
are the subject of the parent stage: Claude Code's sandbox (filesystem scope
plus a SOCKS5 network proxy with a domain allowlist), Codex's three-layer
model (process isolation, network policy, approval routing), and E2B's
Firecracker microVMs.

Run:
    python mini_sandbox.py --workdir /tmp/sbx-demo \
        -- python -c "print('hello')"
    python mini_sandbox.py --workdir /tmp/sbx-demo \
        -- rm -rf /tmp/sbx-demo
    python mini_sandbox.py --workdir /tmp/sbx-demo --allow-destructive \
        -- rm -rf /tmp/sbx-demo
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


NETWORK_COMMANDS = {"curl", "wget", "nc", "ssh", "scp", "git", "pip", "npm"}
DESTRUCTIVE_COMMANDS = {"rm", "mv", "dd", "mkfs", "shutdown", "kill"}


@dataclass
class Verdict:
    """One tool call, one verdict — the record a control plane would keep."""

    command: str
    layer: str  # filesystem | network | approval | allowed
    allowed: bool
    wall_clock_s: float = 0.0
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    notes: list[str] = field(default_factory=list)

    def to_record(self) -> dict:
        return asdict(self)


class MiniSandbox:
    """Three policy layers in front of subprocess.run."""

    def __init__(self, workdir: Path, allow_destructive: bool = False) -> None:
        self.workdir = workdir.resolve()
        self.allow_destructive = allow_destructive
        self.verdicts: list[Verdict] = []

    def _check_filesystem(self, argv: list[str]) -> list[str] | None:
        """Layer 1: every path argument must live under the writable workdir."""
        for arg in argv[1:]:
            if arg.startswith("-") or arg.startswith("="):
                continue
            candidate = Path(arg)
            if not candidate.is_absolute():
                candidate = (self.workdir / candidate).resolve()
            try:
                candidate.relative_to(self.workdir)
            except ValueError:
                return [f"path outside workdir: {arg}"]
        return None

    def _check_network(self, argv: list[str]) -> list[str] | None:
        """Layer 2: no network-bearing command unless the policy allows it."""
        base = os.path.basename(argv[0])
        if base in NETWORK_COMMANDS:
            return [f"network command blocked: {base}"]
        return None

    def _check_approval(self, argv: list[str]) -> list[str] | None:
        """Layer 3: destructive commands need the sandbox-level allow flag."""
        base = os.path.basename(argv[0])
        if base in DESTRUCTIVE_COMMANDS and not self.allow_destructive:
            return [f"destructive command needs --allow-destructive: {base}"]
        return None

    def run(self, argv: list[str]) -> Verdict:
        started = time.monotonic()
        for layer, check in (
            ("filesystem", self._check_filesystem),
            ("network", self._check_network),
            ("approval", self._check_approval),
        ):
            problems = check(argv)
            if problems:
                v = Verdict(
                    command=shlex.join(argv),
                    layer=layer,
                    allowed=False,
                    wall_clock_s=round(time.monotonic() - started, 3),
                    notes=problems,
                )
                self.verdicts.append(v)
                return v
        try:
            proc = subprocess.run(
                argv,
                cwd=self.workdir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            v = Verdict(
                command=shlex.join(argv),
                layer="allowed",
                allowed=True,
                wall_clock_s=round(time.monotonic() - started, 3),
                exit_code=proc.returncode,
                stdout=proc.stdout[-400:],
                stderr=proc.stderr[-400:],
            )
        except subprocess.TimeoutExpired:
            v = Verdict(
                command=shlex.join(argv),
                layer="allowed",
                allowed=False,
                wall_clock_s=round(time.monotonic() - started, 3),
                notes=["timeout after 30s"],
            )
        self.verdicts.append(v)
        return v

    def export(self) -> list[dict]:
        return [v.to_record() for v in self.verdicts]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workdir", required=True, help="writable directory")
    ap.add_argument("--allow-destructive", action="store_true")
    ap.add_argument("--out", help="write verdicts as JSONL")
    ap.add_argument("command", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    if not args.command:
        ap.error("no command given after --")
    if args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        ap.error("no command given after --")

    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    sbx = MiniSandbox(workdir, allow_destructive=args.allow_destructive)
    verdict = sbx.run(args.command)

    print(json.dumps(verdict.to_record(), indent=2, ensure_ascii=False))
    if args.out:
        with open(args.out, "a") as fh:
            for record in sbx.export():
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    sys.exit(0 if verdict.allowed else 2)


if __name__ == "__main__":
    main()
