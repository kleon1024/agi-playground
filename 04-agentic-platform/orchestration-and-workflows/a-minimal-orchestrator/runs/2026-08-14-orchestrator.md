# The deterministic orchestrator dispatch, on the mission's real tasks

Two deterministic workers per task, fixed dispatch plan, recorded summary.
No model in the loop.

## Command

```bash
cd 04-agentic-platform/orchestration-and-workflows/a-minimal-orchestrator/core
python3 orchestrator.py --tasks ../../../tasks/private.jsonl
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS arm64 |
| Python | 3.11 (system) |
| Model | none |
| Cost | \$0 |

## Results

```text
[PASS] private-b81c414: task-record=True; verification-contract=True
[PASS] private-354c352: task-record=True; verification-contract=True

2/2 tasks passed all deterministic gates; no model called.
```

The skeleton is the record: each worker owns a bounded check, the
orchestrator dispatches and collects, and termination is structural — the
opposite of the non-terminating-conversation failure mode the stage
documents for free multi-agent systems.

## Honesty note

The workers are deterministic checks, not LLM cells. The demo shows the
skeleton the stage argues production workflows need; quality claims are
survey topics.
