# The three-tool protocol transcript, on the mission's real tasks

JSON-RPC-style server (discovery, invoke, structured error) over the
mission's task records. No model, no network.

## Command

```bash
cd 04-agentic-platform/tools-and-protocols/a-minimal-tool-protocol/core
python3 tool_server.py --tasks ../../../tasks/private.jsonl
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS arm64 |
| Python | 3.11 (system) |
| Model | none |
| Cost | \$0 |

## Results

| Call | Outcome |
|---|---|
| `discover` | three tool schemas returned |
| `get_task private-b81c414` | task record returned with subject |
| `target_tests private-b81c414` | `tests/test_decode_correctness.py` |
| `get_task nope` | `{"error": {"code": -32602, "message": "unknown task_id"}}` |
| `no_such_method` | `{"error": {"code": -32601, "message": "method not found"}}` |
| `delete_task` | `{"error": {"code": -32601, "message": "method not found"}}` |

The protocol distinguishes bad parameters (-32602) from unknown methods
(-32601) and refuses methods outside the schema — the auditable-surface
property the stage attributes to MCP.

## Honesty note

In-process function calls, not a transport. The demo shows the contract
shape; transports, auth, and ecosystem are survey topics.
