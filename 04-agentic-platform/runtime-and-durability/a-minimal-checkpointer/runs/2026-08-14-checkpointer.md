# Checkpoint-and-resume, crash simulated on the mission's real task list

Deterministic multi-step run with a simulated crash, demonstrating that a
completed-work checkpoint resumes without redoing finished steps.

## Command

```bash
cd 04-agentic-platform/runtime-and-durability/a-minimal-checkpointer/core
python3 checkpointer.py --tasks ../../../tasks/private.jsonl \
    --checkpoint /tmp/ckpt.json --crash-at 1
python3 checkpointer.py --tasks ../../../tasks/private.jsonl \
    --checkpoint /tmp/ckpt.json
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
run 1:  [done]    private-b81c414 -> 1dde1588e568
        [crash]   simulated crash before step 1 (private-354c352)   exit=3
run 2:  [resumed] private-b81c414 already done
        [done]    private-354c352 -> feb10d2d8284

all 2 steps complete; attempts=3 (resumed steps are not redone)
```

The checkpoint stores completed work (`{"done": [...]}`), not loop
position, so resume is idempotent. `attempts=3` counts the crash attempt;
the resumed step was not redone.

## Honesty note

The per-step work is a hash — deliberately trivial — so the demo isolates
durability mechanics from task difficulty. Production agents checkpoint
conversation state, not just step ids; that is the stage's survey topic.
