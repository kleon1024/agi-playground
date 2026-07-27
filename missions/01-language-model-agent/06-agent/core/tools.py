"""Tool definitions for the stage-06 agent harness: schemas, risk tiers, and
sandboxed execution.

Three tools, each declared the way a tool-calling API expects: a name, a
description the model actually reads to decide *when* to call the tool (not
decoration -- a vague description produces a model that calls the wrong tool
or the right tool with the wrong arguments), a JSON-Schema-shaped parameter
spec, and a risk tier the harness uses to decide whether the call needs
confirmation before it runs.

`read_file` and `list_dir` are read-only and auto-allowed. `run_command` is
the one tool that can do real damage, so it is the one with real sandboxing:
an allowlist, a timeout, output truncation, and a working-directory jail --
implemented as code below, not asserted in a comment.
"""

from __future__ import annotations

import dataclasses
import re
import shlex
import subprocess
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any


class RiskTier(str, Enum):
    """How much trust a tool call requires before the harness executes it.

    AUTO    - read-only, always allowed. Reading a file or listing a
              directory cannot itself change anything, so there is nothing
              for a human to approve.
    CONFIRM - can change state (here: run a subprocess). Requires explicit
              sign-off from whoever is running the harness before it executes.
    DENY    - refused unconditionally, regardless of confirmation. Nothing in
              this stage's 3-tool set needs this tier, but the permission
              ladder in harness.py supports it because a real tool set
              eventually grows one (a `send_email`, a `deploy`).
    """

    AUTO = "auto"
    CONFIRM = "confirm"
    DENY = "deny"


class ToolError(Exception):
    """A tool-call failure that should become an Observation, not a crash.

    The harness catches this and feeds the message back to the model as the
    next observation -- the malformed-call/failed-call recovery path, rather
    than raising through the agent loop and ending the run on the first bad
    argument or missing file.
    """


@dataclasses.dataclass(frozen=True)
class Tool:
    name: str
    description: str
    # JSON-Schema-shaped: {"type": "object", "properties": {...}, "required": [...]}
    parameters: dict[str, Any]
    risk: RiskTier
    fn: Callable[[dict[str, Any]], str]

    def schema(self) -> dict[str, Any]:
        """The wire format a model sees, in the shape most tool-calling APIs use."""
        return {"name": self.name, "description": self.description, "parameters": self.parameters}


# ---------------------------------------------------------------------------
# JIT-loading tools: read_file, list_dir. Both auto-allow, both confined to a
# sandbox root by resolve_in_jail().
# ---------------------------------------------------------------------------


def resolve_in_jail(root: Path, relative: str) -> Path:
    """Resolve `relative` against `root` and refuse anything that escapes it.

    Three ways out, and this closes all three:

    1. An absolute path. `pathlib` has a sharp edge here: `Path("/a") /
       "/etc/passwd"` silently discards the left side and returns
       `Path("/etc/passwd")`, because joining with an absolute path replaces
       rather than extends. Checking `Path(relative).is_absolute()` before
       ever joining is what stops that gotcha from turning into a sandbox
       escape.
    2. A `..` walk (`"../../etc/passwd"`). Resolving the joined path and
       checking its ancestry catches this; checking the *string* for `..`
       would not (`"a/../../b"` normalizes in ways a substring check misses).
    3. A symlink whose target lands outside root. `Path.resolve()` follows
       symlinks before the containment check runs, so a symlink planted
       inside the sandbox that points outside it is caught too.

    A jail that only string-matches for `..` is not a jail; `resolve()` plus
    an ancestry check is what actually makes containment real.
    """
    root = root.resolve()
    if Path(relative).is_absolute():
        raise ToolError(f"absolute paths are not allowed: {relative!r}")
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise ToolError(f"path escapes sandbox root: {relative!r}")
    return candidate


MAX_READ_BYTES = 8_000


def read_file(root: Path, path: str) -> str:
    target = resolve_in_jail(root, path)
    if not target.is_file():
        raise ToolError(f"not a file: {path!r}")
    data = target.read_bytes()
    truncated = len(data) > MAX_READ_BYTES
    text = data[:MAX_READ_BYTES].decode("utf-8", errors="replace")
    if truncated:
        text += f"\n...[truncated, {len(data):,} bytes total, showing first {MAX_READ_BYTES:,}]"
    return text


def list_dir(root: Path, path: str = ".") -> str:
    target = resolve_in_jail(root, path)
    if not target.is_dir():
        raise ToolError(f"not a directory: {path!r}")
    entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
    lines = [
        f"{'f' if e.is_file() else 'd'}  {e.stat().st_size if e.is_file() else 0:>8}  {e.name}"
        for e in entries
    ]
    return "\n".join(lines) or "(empty directory)"


# ---------------------------------------------------------------------------
# run_command: allowlist, no shell, a timeout, output truncation, a cwd jail.
# ---------------------------------------------------------------------------

DEFAULT_ALLOWLIST = frozenset(
    {"ls", "cat", "grep", "find", "wc", "echo", "pwd", "head", "tail", "python3", "pytest"}
)

# Rejected outright even though we never pass shell=True: a saved transcript
# containing one of these should not be replayable against a real shell by
# anyone who copy-pastes it without rereading this file.
_SHELL_METACHARACTERS = re.compile(r"[;&|`$<>\n]")

COMMAND_TIMEOUT_S = 10.0
MAX_OUTPUT_CHARS = 4_000


def run_command(
    root: Path,
    command: str,
    allowlist: frozenset[str] = DEFAULT_ALLOWLIST,
    timeout: float = COMMAND_TIMEOUT_S,
) -> str:
    """Run `command` inside `root`: allowlisted, un-shelled, timed, truncated.

    Four independent controls, each closing a different hole:

    1. **Allowlist, checked on argv[0] after tokenizing.** `shlex.split`
       parses the string the way a shell would; we look at the first token
       only. A denylist ("no rm -rf") is a losing game -- there is no bound
       on the ways to spell "delete everything." An allowlist inverts the
       burden: the command runs only if it names something already decided
       to be safe.
    2. **No `shell=True`, ever.** `subprocess.run` gets an argv list, not a
       string. This is what makes the allowlist check meaningful: under
       `shell=True`, `"echo hi; rm -rf /"` is one command as far as the OS is
       concerned, and checking argv[0] against an allowlist would only ever
       see `echo`. Shell metacharacters are rejected outright too, so a
       command like that fails fast with a clear message instead of quietly
       doing something the allowlist never anticipated.
    3. **A hard timeout.** A hung process -- an accidental read on stdin, an
       infinite loop -- would otherwise block the whole agent loop forever.
    4. **Output truncation.** An agent that runs `cat` on a multi-gigabyte
       file should not feed gigabytes back into the model's context.

    The working-directory jail is `cwd=root`: whatever the command does, it
    does from inside the sandbox root, not the harness's own working
    directory.

    Known gap, left honest rather than hidden: only argv[0] is allowlisted.
    `cat /etc/passwd` would still run `cat` from an allowed name while
    reading a path outside the jail, because arguments aren't validated
    against `resolve_in_jail`. Hardening that is exercise 3 in the README.
    """
    if _SHELL_METACHARACTERS.search(command):
        raise ToolError(f"command contains a shell metacharacter, refused: {command!r}")
    try:
        argv = shlex.split(command)
    except ValueError as e:
        raise ToolError(f"could not parse command: {e}") from e
    if not argv:
        raise ToolError("empty command")
    if argv[0] not in allowlist:
        raise ToolError(f"{argv[0]!r} is not in the command allowlist {sorted(allowlist)}")

    try:
        proc = subprocess.run(
            argv,
            cwd=root.resolve(),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise ToolError(f"command timed out after {timeout}s: {command!r}") from None

    out = proc.stdout + (f"\n[stderr]\n{proc.stderr}" if proc.stderr else "")
    if len(out) > MAX_OUTPUT_CHARS:
        out = out[:MAX_OUTPUT_CHARS] + f"\n...[truncated, {len(out):,} chars total]"
    return f"exit={proc.returncode}\n{out}"


# ---------------------------------------------------------------------------
# A deliberately small JSON-Schema-subset validator, and the tool registry.
# ---------------------------------------------------------------------------

_JSON_TYPES: dict[str, Any] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


def validate_arguments(schema: dict[str, Any], arguments: dict[str, Any]) -> str | None:
    """object/properties/required/type only -- enough to catch the malformed
    calls a model actually produces (a missing required field, a string where
    a number was asked for) without pulling in a full JSON Schema
    implementation for a 3-tool harness. Returns an error message, or None if
    the arguments are acceptable.
    """
    if schema.get("type") != "object":
        return None
    for field in schema.get("required", []):
        if field not in arguments:
            return f"missing required argument {field!r}"
    properties = schema.get("properties", {})
    for key, value in arguments.items():
        prop_schema = properties.get(key)
        if prop_schema is None:
            return f"unexpected argument {key!r}"
        expected = _JSON_TYPES.get(prop_schema.get("type"))
        if expected is not None and not isinstance(value, expected):
            got = type(value).__name__
            return f"argument {key!r} should be {prop_schema['type']}, got {got}"
    return None


def execute_tool(tools: dict[str, Tool], name: str, arguments: dict[str, Any]) -> str:
    tool = tools.get(name)
    if tool is None:
        raise ToolError(f"no such tool {name!r}; available: {sorted(tools)}")
    error = validate_arguments(tool.parameters, arguments)
    if error is not None:
        raise ToolError(f"invalid arguments for {name!r}: {error}")
    return tool.fn(arguments)


def build_tools(root: Path) -> dict[str, Tool]:
    """Bind all three tools to one sandbox root and return them by name."""
    return {
        "read_file": Tool(
            name="read_file",
            description=(
                "Read a UTF-8 text file and return its contents. Path is relative to "
                "the sandbox root. Call this before reasoning about any file's "
                "contents -- never assume what a file contains."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "file path, relative to root"}
                },
                "required": ["path"],
            },
            risk=RiskTier.AUTO,
            fn=lambda args, _root=root: read_file(_root, args["path"]),
        ),
        "list_dir": Tool(
            name="list_dir",
            description=(
                "List a directory's immediate contents as kind, size, and name. Use "
                "this to find out what's there before guessing a path for read_file."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "directory path relative to root, default '.'",
                    }
                },
                "required": [],
            },
            risk=RiskTier.AUTO,
            fn=lambda args, _root=root: list_dir(_root, args.get("path", ".")),
        ),
        "run_command": Tool(
            name="run_command",
            description=(
                "Run a single allowlisted command inside the sandbox root (no pipes, "
                "redirects, or chaining) and return its stdout/stderr and exit code. "
                "Allowlisted: " + ", ".join(sorted(DEFAULT_ALLOWLIST)) + ". Use this for "
                "anything read_file/list_dir can't do, e.g. `grep -rn TODO .` or "
                "running a test with `pytest -q`."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "a single command, e.g. 'grep -rn TODO src'",
                    }
                },
                "required": ["command"],
            },
            risk=RiskTier.CONFIRM,
            fn=lambda args, _root=root: run_command(_root, args["command"]),
        ),
    }
