"""Run one mined task through Claude Code and keep the step-by-step trace.

`claude_arm.py` runs the same task but throws the trace away: it records
turns, cost, and verdict, not what the agent actually did. This file keeps
the thing a tutorial needs — the sequence of decisions, tool calls, and
observed results that made the verdict true. It reuses the same
materialize/score path, so the trace is anchored to the same real task and
the same guardrail as every other run in this stage.

The trace is captured from `claude -p --output-format stream-json
--include-partial-messages --verbose`, which emits one JSON object per line.
Each assistant message's content blocks become the model's text and tool
calls; each user message's tool_result blocks become the observations.

Run:
    python trace_task.py --task-id private-354c352 --model haiku \
        --out runs/2026-08-14-trace.md --raw runs/2026-08-14-trace.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path

import scoring
from claude_arm import ALLOWED_TOOLS, DENIED_TOOLS
from run_task import DEFAULT_MANIFEST, PROMPT, _miner_for

# A bare `$` opens KaTeX math in Docusaurus, and emoji is banned in published
# prose. The raw stream is preserved in the .jsonl; the markdown is the
# published form and gets both cleaned.
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u2705\u274C\u2B50\u2757\u2764]"
)


def sanitize(text: str) -> str:
    text = re.sub(r"(?<!\\)\$", r"\\$", text)
    return EMOJI_RE.sub("", text)


def invoke_stream(prompt: str, work: Path, model: str, timeout: float) -> list[dict]:
    """Run Claude Code headless and return every stream event as a dict."""
    command = [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "stream-json",
        "--include-partial-messages",
        "--verbose",
        "--permission-mode",
        "acceptEdits",
        "--allowedTools",
        *ALLOWED_TOOLS,
        "--disallowedTools",
        *DENIED_TOOLS,
    ]
    proc = subprocess.run(
        command, cwd=work, capture_output=True, text=True, timeout=timeout, check=False
    )
    events: list[dict] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if proc.returncode != 0 and not events:
        return [{"type": "result", "is_error": True, "result": (proc.stdout + proc.stderr)[-2000:]}]
    return events


def build_trace(events: list[dict]) -> list[dict]:
    """Collapse the event stream into steps: model text, tool call, observation."""
    steps: list[dict] = []
    current: dict | None = None

    for event in events:
        etype = event.get("type")
        if etype == "assistant":
            message = event.get("message", {})
            for block in message.get("content", []):
                btype = block.get("type")
                if btype == "text":
                    current = {"text": block.get("text", "").strip(), "action": None, "observation": None}
                    steps.append(current)
                elif btype == "tool_use":
                    current = {
                        "text": None,
                        "action": {"name": block.get("name"), "input": block.get("input", {})},
                        "observation": None,
                    }
                    steps.append(current)
        elif etype == "user":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_result":
                    content = block.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(
                            c.get("text", "") for c in content if isinstance(c, dict)
                        )
                    observation = str(content).strip()
                    for step in reversed(steps):
                        if step["action"] and step["observation"] is None:
                            step["observation"] = observation
                            break
    # Drop assistant text blocks that carry no content: a final answer appears
    # both as an assistant text block and in the result event, and an empty
    # text block is not a step.
    return [s for s in steps if s["text"] or s["action"]]


def model_of(events: list[dict]) -> str:
    for event in events:
        if event.get("type") == "assistant":
            model = event.get("message", {}).get("model")
            if model:
                return model
    return "?"


def summarize_result(events: list[dict]) -> dict:
    for event in events:
        if event.get("type") == "result":
            return event
    return {"is_error": True, "result": "no result event"}


def render_markdown(
    task: dict, steps: list[dict], result: dict, cost: float, model: str
) -> str:
    lines = [
        f"# Trace: {task['task_id']} — {task['subject']}",
        "",
        f"Model: {model} · turns: {result.get('num_turns', '?')} · cost: \\${cost:.4f}",
        "",
    ]
    for i, step in enumerate(steps, start=1):
        if step["text"] and step["text"].startswith("## Final Answer"):
            continue  # the final answer is rendered once, from the result event
        lines.append(f"## Step {i}")
        if step["text"]:
            lines.append("")
            lines.append(sanitize(step["text"]))
        if step["action"]:
            lines.append("")
            lines.append(f"**Tool:** {step['action']['name']}")
            lines.append("")
            lines.append(f"```json\n{json.dumps(step['action']['input'], indent=2)}\n```")
        if step["observation"]:
            lines.append("")
            lines.append("**Observed:**")
            lines.append("")
            lines.append(f"```text\n{sanitize(step['observation'][:3000])}\n```")
        lines.append("")
    lines.append("## Final")
    lines.append("")
    lines.append(sanitize(str(result.get("result", ""))[:2000]))
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--out", type=Path, help="write the markdown trace here")
    ap.add_argument("--raw", type=Path, help="write the raw event stream here")
    args = ap.parse_args()

    tasks = [json.loads(x) for x in args.manifest.read_text().splitlines() if x]
    task = next((t for t in tasks if t["task_id"] == args.task_id), None)
    if not task:
        raise SystemExit(f"no task {args.task_id!r} in {args.manifest}")

    miner = _miner_for(task)
    task_obj = miner.Task(**task)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "task"
        junit = Path(tmp) / "out.xml"
        miner.materialize(task_obj, work)
        try:
            target_cmd = scoring.instrument(task_obj.test_command, junit)
            suite_cmd = scoring.instrument(task_obj.test_command, junit, targets=["tests"])
            target_before, failure = scoring.run_and_collect(target_cmd, work, junit)
            if not target_before or not any(
                s in ("failure", "error") for s in target_before.values()
            ):
                raise SystemExit(
                    f"{task_obj.task_id}: target tests do not fail at base state; "
                    f"the manifest is stale or the environment cannot run them.\n{failure[-1500:]}"
                )
            suite_before, _ = scoring.run_and_collect(suite_cmd, work, junit)

            prompt = PROMPT.format(command=" ".join(task_obj.test_command), failure=failure)
            events = invoke_stream(prompt, work, args.model, args.timeout)
            if args.raw:
                with args.raw.open("w") as fh:
                    for event in events:
                        fh.write(json.dumps(event) + "\n")

            steps = build_trace(events)
            result = summarize_result(events)
            cost = result.get("total_cost_usd", 0.0)
            model = model_of(events)

            changed = scoring.changed_paths(work)
            target_after, _ = scoring.run_and_collect(target_cmd, work, junit)
            suite_after, _ = scoring.run_and_collect(suite_cmd, work, junit)
            verdict = scoring.score(
                task_obj.task_id, changed, target_before, target_after, suite_before, suite_after
            )
        finally:
            miner.cleanup(work)

    print(
        f"{verdict.verdict:<22} {task['task_id']}  {len(steps)} trace steps  "
        f"{round(time.perf_counter() - started, 1)}s  ${cost:.4f}"
    )
    if verdict.tampered:
        print(f"  GUARDRAIL FIRED: patch touched {verdict.tampered}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        md = render_markdown(task, steps, result, cost, model)
        md += (
            f"\n\n## Verdict\n\n`{verdict.verdict}` — resolved: {verdict.resolved}; "
            f"changed {verdict.changed}; tampered {verdict.tampered}.\n"
        )
        args.out.write_text(md)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
