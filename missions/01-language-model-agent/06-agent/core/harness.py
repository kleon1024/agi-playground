"""The agent loop: observe -> decide -> act -> observe, with the model's
tool calls parsed out of text, validated, permission-checked, executed in the
sandbox from `tools.py`, and fed back in as the next observation.

Run:  python harness.py                         # fake backend, no GPU/API key
      python harness.py --demo grounding         # watch the grounding rule work
      AGENT_BASE_URL=http://localhost:8000/v1 AGENT_MODEL=... python harness.py

Five things here are load-bearing:

**The grounding rule.** A ReAct-style model is prompted to stop right after
"Action Input: ..." and wait for the harness to supply "Observation: <real
result>". Nothing about sampling stops it from continuing to write its own
"Observation: ..." line and inventing a plausible-looking result --
confidently, and indistinguishably from a real one, until whatever it does
next is grounded in a fact that never happened. `enforce_grounding` closes
this with two layers: ask the backend to stop generating at the boundary
(cheap, and honored by real chat-completions APIs via a `stop` sequence), and
then, regardless of whether it did, truncate anything at or after the stop
token before parsing an action out of the text. The second layer is the one
that matters: it is what keeps a backend that ignores `stop` -- a bug, an
old API version, the FakeBackend below with `honor_stop=False` -- from
slipping a fabricated observation past this harness.

**Tool-call parsing without assuming native function-calling.** Production
tool-calling APIs return a structured call object; this harness instead
parses a textual `Action: <name>\\nAction Input: <json>` protocol so it works
against any model, tool-calling fine-tuned or not. Malformed output (bad
JSON, an unknown tool, a schema mismatch) becomes an Observation describing
the failure and the loop continues, rather than crashing -- the recovery
path a real harness needs, because schema adherence is a probabilistic
property of the model, not a guarantee.

**An explicit, pluggable context-compaction policy.** `ContextManager` keeps
messages under a token budget by collapsing superseded file reads (a stale
read of a path is dropped once a newer read of that same path exists) and,
if still over budget, dropping the oldest non-system turns. Both steps are
named functions, not inline logic, so the policy can be swapped without
touching the loop that calls it.

**A permission ladder with a safe default.** Each tool declares a risk tier
in `tools.py`; `check_permission` enforces it here. `default_confirm` denies
every CONFIRM-tier call unless a real confirm function is supplied -- so a
non-interactive run (a test, this file's own demo) fails closed rather than
silently executing something nobody approved.

**A model-agnostic backend interface.** `Backend` is a two-method protocol.
`FakeBackend` is a fully deterministic, scripted implementation -- the whole
loop, parsing, grounding, permission, and compaction logic below is
exercised by it with no GPU, no API key, and no network. `backend_from_env`
is the one place environment variables are read, pointing at stage 05's
served model or any OpenAI-compatible endpoint when `AGENT_BASE_URL` is set.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol

from tools import RiskTier, Tool, ToolError, build_tools, execute_tool

# ---------------------------------------------------------------------------
# Grounding: the single most important mechanic in this file.
# ---------------------------------------------------------------------------


def enforce_grounding(text: str, stop_token: str = "Observation:") -> tuple[str, bool]:
    """Cut model output at the observation boundary, unconditionally.

    Returns (truncated_text, was_truncated). `was_truncated=True` means the
    backend either wasn't asked to stop there, or was asked and did it
    anyway -- either way, whatever followed the stop token in the raw output
    is discarded before it ever reaches the parser or the context.
    """
    idx = text.find(stop_token)
    if idx == -1:
        return text, False
    return text[:idx], True


# ---------------------------------------------------------------------------
# Parsing a textual ReAct step: Thought / Action / Action Input, or Final Answer.
# ---------------------------------------------------------------------------

_ACTION_RE = re.compile(r"Action:\s*(?P<name>\S+)\s*\nAction Input:\s*(?P<args>\{.*\})", re.DOTALL)
_FINAL_RE = re.compile(r"Final Answer:\s*(?P<answer>.*)", re.DOTALL)


@dataclass
class ParsedStep:
    kind: Literal["action", "final", "unparsed"]
    tool_name: str | None = None
    arguments: dict | None = None
    final_answer: str | None = None
    error: str | None = None


def parse_response(text: str) -> ParsedStep:
    """Extract exactly one action or one final answer from a model turn.

    If a (buggy, or ungrounded-then-truncated) response contains markers for
    both, whichever appears earlier in the text wins -- read in the order the
    model actually wrote things, not in regex-registration order.
    """
    final_match = _FINAL_RE.search(text)
    action_match = _ACTION_RE.search(text)
    if final_match and (action_match is None or final_match.start() < action_match.start()):
        return ParsedStep(kind="final", final_answer=final_match.group("answer").strip())
    if action_match:
        raw_args = action_match.group("args")
        try:
            arguments = json.loads(raw_args)
        except json.JSONDecodeError as e:
            return ParsedStep(kind="unparsed", error=f"Action Input was not valid JSON: {e}")
        return ParsedStep(kind="action", tool_name=action_match.group("name"), arguments=arguments)
    return ParsedStep(kind="unparsed", error="no Action or Final Answer found in the response")


# ---------------------------------------------------------------------------
# Context management: token budget + pluggable compaction.
# ---------------------------------------------------------------------------


def estimate_tokens(text: str) -> int:
    """chars/4 as a model-agnostic stand-in for a real tokenizer. Wiring
    stage 01's `bpe.py` in as the counter instead is exercise 1."""
    return max(1, len(text) // 4)


class ContextManager:
    """Keeps the message list a model sees under a token budget.

    Each message carries an optional `read_file_path`, used only by the
    default compaction policy to know which observations are re-reads of the
    same file. This is metadata alongside the message, not something parsed
    back out of its text.
    """

    def __init__(
        self,
        system_prompt: str,
        token_budget: int = 4000,
        token_counter: Callable[[str], int] = estimate_tokens,
        compaction_policy: Callable[[ContextManager], None] | None = None,
    ) -> None:
        self.messages: list[dict] = [{"role": "system", "content": system_prompt, "meta": {}}]
        self.token_budget = token_budget
        self.token_counter = token_counter
        self.compaction_policy = compaction_policy or drop_oldest_tool_results
        self.compactions = 0

    def add(self, role: str, content: str, *, read_file_path: str | None = None) -> None:
        meta = {"read_file_path": read_file_path} if read_file_path else {}
        self.messages.append({"role": role, "content": content, "meta": meta})
        if self.total_tokens() > self.token_budget:
            self.compaction_policy(self)
            self.compactions += 1

    def total_tokens(self) -> int:
        return sum(self.token_counter(m["content"]) for m in self.messages)

    def wire_messages(self) -> list[dict[str, str]]:
        """What actually gets sent to the backend: role and content only.

        A real chat-completions API has a dedicated "tool" role with a
        tool_call_id linking a result back to the call that produced it; this
        from-scratch harness folds tool observations into plain "user" turns
        to keep the message schema minimal for a 3-tool loop. Swapping this
        for the native tool/tool_call_id shape is a compatibility detail, not
        a change to any of the logic above it.
        """
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]


def drop_oldest_tool_results(ctx: ContextManager) -> None:
    """The default compaction policy, applied in order until under budget:

    1. Collapse a `read_file` observation of some path if a *later* message
       also read that path -- the newest read of any file is kept, older
       ones are replaced by a one-line marker. An agent that read a file
       twice only needs the second read; the first is pure waste once the
       second exists.
    2. If still over budget, drop the oldest non-system message outright,
       one at a time, never touching the system prompt (index 0) or letting
       fewer than 3 messages remain -- the model needs to see, at minimum,
       its own last action and the observation it produced.
    """
    seen_paths: set[str] = set()
    for msg in reversed(ctx.messages):  # newest to oldest: newest read wins
        path = msg["meta"].get("read_file_path")
        if path is None:
            continue
        if path in seen_paths:
            msg["content"] = f"[stale read of {path!r}, superseded by a later read_file call]"
        else:
            seen_paths.add(path)

    while ctx.total_tokens() > ctx.token_budget and len(ctx.messages) > 3:
        del ctx.messages[1]  # oldest non-system message


# ---------------------------------------------------------------------------
# Permission model: the ladder from auto-allow to refuse.
# ---------------------------------------------------------------------------


class PermissionDenied(Exception):
    pass


ConfirmFn = Callable[[str, dict], bool]


def default_confirm(tool_name: str, arguments: dict) -> bool:
    """Fail closed: every CONFIRM-tier call is denied unless the caller
    supplies a real confirm function (a CLI y/n prompt, a policy check
    against an allowlist of tasks, ...). A non-interactive run -- a test,
    this file's own demo -- must not silently execute something nobody
    approved just because nobody was there to say no.
    """
    return False


def check_permission(tool: Tool, confirm: ConfirmFn, arguments: dict) -> None:
    if tool.risk is RiskTier.AUTO:
        return
    if tool.risk is RiskTier.DENY:
        raise PermissionDenied(f"{tool.name!r} is deny-tier and cannot be run by this harness")
    if tool.risk is RiskTier.CONFIRM and not confirm(tool.name, arguments):
        raise PermissionDenied(f"{tool.name!r} requires confirmation, which was not granted")


# ---------------------------------------------------------------------------
# Model-agnostic backend interface.
# ---------------------------------------------------------------------------


class Backend(Protocol):
    def generate(self, messages: list[dict[str, str]], stop: list[str]) -> str: ...


class FakeBackend:
    """A scripted, fully deterministic backend for offline testing.

    Returns one entry of `script` per call, in order, regardless of what's in
    `messages` -- the loop, parsing, grounding, permission, and compaction
    logic can all be exercised with no GPU, no API key, and no network.
    `honor_stop=False` simulates a backend that ignores the stop sequence
    (an old API, a bug, a model that just keeps generating), so
    `enforce_grounding`'s second layer is what has to catch a hallucinated
    Observation instead of the `stop` parameter doing it for free.
    """

    def __init__(self, script: Sequence[str], honor_stop: bool = True) -> None:
        self.script = list(script)
        self.honor_stop = honor_stop
        self.calls = 0

    def generate(self, messages: list[dict[str, str]], stop: list[str]) -> str:
        if self.calls >= len(self.script):
            raise IndexError(f"FakeBackend script exhausted after {self.calls} calls")
        text = self.script[self.calls]
        self.calls += 1
        if self.honor_stop:
            for token in stop:
                idx = text.find(token)
                if idx != -1:
                    text = text[:idx]
        return text


class OpenAICompatibleBackend:
    """Points at the model served by stage 05, or any OpenAI-compatible chat
    completions endpoint. Base URL, model id, and API key are all
    constructor/environment arguments, never hardcoded -- swapping which
    model backs the harness is configuration, not a code change.
    """

    def __init__(
        self, base_url: str, model: str, api_key: str | None = None, timeout: float = 60.0
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def generate(self, messages: list[dict[str, str]], stop: list[str]) -> str:
        import urllib.request

        payload = json.dumps(
            {"model": self.model, "messages": messages, "stop": stop, "temperature": 0}
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions", data=payload, headers=headers, method="POST"
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = json.loads(response.read())
        return body["choices"][0]["message"]["content"]


DEMO_SCRIPT = [
    "Thought: let's see what's in the sandbox root.\nAction: list_dir\nAction Input: {\"path\": \".\"}",
    (
        "Thought: harness.py looks like the main file, let's read it.\n"
        'Action: read_file\nAction Input: {"path": "harness.py"}'
    ),
    (
        "Thought: I've seen enough to answer.\n"
        "Final Answer: The sandbox root contains harness.py (the agent loop) and "
        "tools.py (the tool definitions)."
    ),
]

# Demonstrates the grounding rule doing real work: the first entry fabricates
# its own "Observation:" and "Final Answer:" in one generate() call, as if the
# backend ignored the stop sequence. enforce_grounding truncates everything
# from "Observation:" onward before parsing, so only the list_dir action
# survives -- the fabricated final answer never reaches the loop.
GROUNDING_DEMO_SCRIPT = [
    (
        "Thought: I will check the directory.\n"
        'Action: list_dir\nAction Input: {"path": "."}\n'
        "Observation: harness.py, tools.py, README.md\n"
        "Thought: now I know enough.\n"
        "Final Answer: There are three files -- fabricated, I never actually ran list_dir."
    ),
    (
        "Thought: the harness gave me the real observation above; that's what I'll use.\n"
        "Final Answer: done"
    ),
]

DEFAULT_TASK = "List what's in this directory and summarize the main file."


def backend_from_env(demo: str = "basic") -> Backend:
    """The one place environment variables are read.

    `AGENT_BASE_URL` unset -> a FakeBackend running a canned script, so
    `python harness.py` needs neither a GPU nor an API key. Set
    `AGENT_BASE_URL` (and `AGENT_MODEL`, optionally `AGENT_API_KEY`) to point
    at stage 05's served model or any OpenAI-compatible endpoint instead.
    """
    base_url = os.environ.get("AGENT_BASE_URL")
    if not base_url:
        script = GROUNDING_DEMO_SCRIPT if demo == "grounding" else DEMO_SCRIPT
        return FakeBackend(script, honor_stop=(demo != "grounding"))
    return OpenAICompatibleBackend(
        base_url=base_url,
        model=os.environ.get("AGENT_MODEL", "default"),
        api_key=os.environ.get("AGENT_API_KEY"),
    )


# ---------------------------------------------------------------------------
# The loop.
# ---------------------------------------------------------------------------


@dataclass
class StepRecord:
    step: int
    raw_response: str
    grounding_triggered: bool
    parsed: ParsedStep
    observation: str | None = None
    permission_denied: bool = False


@dataclass
class AgentResult:
    status: Literal["done", "max_steps"]
    final_answer: str | None
    steps: list[StepRecord] = field(default_factory=list)


def build_system_prompt(tools: dict[str, Tool]) -> str:
    tool_lines = [
        f"- {t.name} ({t.risk.value}): {t.description}\n  parameters: {json.dumps(t.parameters)}"
        for t in tools.values()
    ]
    return (
        "You solve tasks by repeating Thought / Action / Action Input, then waiting "
        "for an Observation the harness supplies. Never write your own Observation "
        "line -- the harness stops your generation there and fills in the real one.\n\n"
        "Available tools:\n" + "\n".join(tool_lines) + "\n\n"
        "Format exactly:\n"
        "Thought: <reasoning>\nAction: <tool name>\nAction Input: <JSON object>\n\n"
        "When you have the final answer, instead write:\n"
        "Thought: <reasoning>\nFinal Answer: <answer>\n"
    )


def run_agent(
    task: str,
    tools: dict[str, Tool],
    backend: Backend,
    *,
    max_steps: int = 8,
    token_budget: int = 4000,
    confirm: ConfirmFn = default_confirm,
) -> AgentResult:
    """observe -> decide -> act -> observe.

    Explicit stop conditions: a `Final Answer` from the model (done), or
    `max_steps` reached with neither a final answer nor a way to make
    progress (max_steps). There is no third way out -- a loop with an
    implicit stop condition is a loop that hangs the first time the model
    doesn't cooperate.
    """
    ctx = ContextManager(system_prompt=build_system_prompt(tools), token_budget=token_budget)
    ctx.add("user", task)
    steps: list[StepRecord] = []

    for step_index in range(1, max_steps + 1):
        raw = backend.generate(ctx.wire_messages(), stop=["Observation:"])
        clean, grounding_triggered = enforce_grounding(raw)
        parsed = parse_response(clean)
        ctx.add("assistant", clean)

        if parsed.kind == "final":
            steps.append(StepRecord(step_index, raw, grounding_triggered, parsed))
            return AgentResult("done", parsed.final_answer, steps)

        if parsed.kind == "unparsed":
            observation = f"Observation: could not parse a tool call -- {parsed.error}"
            ctx.add("user", observation)
            steps.append(StepRecord(step_index, raw, grounding_triggered, parsed, observation))
            continue

        tool = tools.get(parsed.tool_name)
        if tool is None:
            observation = f"Observation: no such tool {parsed.tool_name!r}; available: {sorted(tools)}"
            ctx.add("user", observation)
            steps.append(StepRecord(step_index, raw, grounding_triggered, parsed, observation))
            continue

        try:
            check_permission(tool, confirm, parsed.arguments)
            result = execute_tool(tools, parsed.tool_name, parsed.arguments)
            observation = f"Observation: {result}"
            read_path = parsed.arguments.get("path") if tool.name == "read_file" else None
            ctx.add("user", observation, read_file_path=read_path)
            steps.append(StepRecord(step_index, raw, grounding_triggered, parsed, observation))
        except PermissionDenied as e:
            observation = f"Observation: permission denied -- {e}"
            ctx.add("user", observation)
            steps.append(
                StepRecord(step_index, raw, grounding_triggered, parsed, observation, True)
            )
        except ToolError as e:
            observation = f"Observation: tool error -- {e}"
            ctx.add("user", observation)
            steps.append(StepRecord(step_index, raw, grounding_triggered, parsed, observation))

    return AgentResult("max_steps", None, steps)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="sandbox root for tool execution (default: this file's directory)",
    )
    ap.add_argument("--task", default=DEFAULT_TASK)
    ap.add_argument("--max-steps", type=int, default=6)
    ap.add_argument("--token-budget", type=int, default=4000)
    ap.add_argument(
        "--demo",
        choices=["basic", "grounding"],
        default="basic",
        help="which canned FakeBackend script to run when AGENT_BASE_URL is unset",
    )
    args = ap.parse_args()

    tools = build_tools(args.root)
    backend = backend_from_env(demo=args.demo)

    result = run_agent(
        args.task, tools, backend, max_steps=args.max_steps, token_budget=args.token_budget
    )

    for record in result.steps:
        print(f"--- step {record.step} ---")
        print(record.raw_response.strip())
        if record.grounding_triggered:
            print("[grounding] truncated a hallucinated Observation before parsing")
        if record.observation:
            print(record.observation)
        print()

    print(f"status: {result.status}")
    if result.final_answer:
        print(f"final answer: {result.final_answer}")


if __name__ == "__main__":
    main()
