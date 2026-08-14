"""A minimal JSON-RPC-style tool protocol, three tools, real tasks.

The tools-and-protocols stage claims a tool protocol buys discoverability:
an agent can ask what tools exist, invoke one, and get a structured error
back — the same three primitives MCP formalizes (tools, resources, prompts)
on JSON-RPC 2.0. This file is the smallest honest instance: a server
exposing three tools over a plain function call, a client that discovers
and invokes, and a deliberately broken call to show the error path.

The three tools operate on the mission's task records: `list_tasks`,
`get_task`, and `target_tests`. No model, no network, no filesystem beyond
reading the task JSONL.

Run:
    python tool_server.py --tasks ../../../tasks/private.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TOOL_SCHEMAS = {
    "list_tasks": {
        "description": "List task ids in the task set.",
        "parameters": {"source": {"type": "string", "description": "private or public"}},
    },
    "get_task": {
        "description": "Fetch one task record by id.",
        "parameters": {"task_id": {"type": "string"}},
    },
    "target_tests": {
        "description": "List the tests a task must satisfy.",
        "parameters": {"task_id": {"type": "string"}},
    },
}


class ToolServer:
    def __init__(self, tasks: list[dict]) -> None:
        self.tasks = {t["task_id"]: t for t in tasks}

    def handle(self, method: str, params: dict) -> dict:
        if method == "list_tasks":
            source = params.get("source", "private")
            ids = [tid for tid, t in self.tasks.items() if t.get("source") == source]
            return {"result": {"task_ids": ids}}
        if method == "get_task":
            task = self.tasks.get(params.get("task_id", ""))
            if task is None:
                return {"error": {"code": -32602, "message": "unknown task_id"}}
            return {"result": task}
        if method == "target_tests":
            task = self.tasks.get(params.get("task_id", ""))
            if task is None:
                return {"error": {"code": -32602, "message": "unknown task_id"}}
            return {"result": {"target_tests": task.get("target_tests", [])}}
        return {"error": {"code": -32601, "message": f"method not found: {method}"}}

    def discover(self) -> dict:
        return {"result": {"tools": TOOL_SCHEMAS}}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", required=True)
    args = ap.parse_args()

    tasks = [json.loads(l) for l in Path(args.tasks).read_text().splitlines() if l.strip()]
    server = ToolServer(tasks)

    # 1. discovery
    print("== discovery ==")
    print(json.dumps(server.discover(), indent=2, ensure_ascii=False)[:400])

    # 2. invoke
    task_id = next(iter(server.tasks))
    print("== get_task ==")
    got = server.handle("get_task", {"task_id": task_id})
    print(json.dumps({"task_id": got["result"]["task_id"],
                      "subject": got["result"]["subject"]}, ensure_ascii=False))

    # 3. target tests
    print("== target_tests ==")
    print(json.dumps(server.handle("target_tests", {"task_id": task_id}), ensure_ascii=False))

    # 4. error path
    print("== error path ==")
    print(json.dumps(server.handle("get_task", {"task_id": "nope"}), ensure_ascii=False))
    print(json.dumps(server.handle("no_such_method", {}), ensure_ascii=False))

    # 5. a method that is not in the protocol
    print("== method outside the protocol ==")
    print(json.dumps(server.handle("delete_task", {}), ensure_ascii=False))


if __name__ == "__main__":
    main()
