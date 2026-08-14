# SQLite memory, six seeded lessons, two recalls, no model in the loop

Mechanism demo for the context-and-memory stage: a SQLite `lessons` table
seeded from this mission's recorded runs, keyword recall against two
decision questions, and promotion on second recall.

## Command

```bash
cd 04-agentic-platform/context-and-memory/a-sqlite-memory/core
python3 sqlite_memory.py --db /tmp/mem.db --out record.json
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS arm64 |
| Python | 3.11 (system) |
| Model | none — no API key, no network |
| Cost | \$0 |

## Results

Full record: [2026-08-14-sqlite-memory.json](2026-08-14-sqlite-memory.json)

Six lessons seeded, each naming its source `runs/` file. Two questions:

| Question | Recalled lessons | After |
|---|---|---|
| "which tier should resolve it; what does the blind-call say?" | 1, 3, 4 | all still ephemeral |
| "is the resolve rate still believable when nothing failed?" | 1, 4 | 1 and 4 promoted to durable |

Promotion follows the two-recall rule: a lesson is durable only after it
has been produced by recall twice. Lessons 2, 5, 6 were recalled zero times
and remain ephemeral.

## Reading

The store did not decide which lessons matter; recall did. Lesson 2 (the
guardrail claim) was never recalled because neither question mentioned
tampering or guardrails — which is the same failure mode an unpruned
instruction file has, where every instruction is durable because nothing is
ever filtered. Recall quality, not storage, is the memory bottleneck.

## Honesty note

All six seeded claims are real, measured results from this mission's
`runs/`; the two questions and the promotion rule are synthetic. The demo
proves the mechanics of a generated memory layer, not that memory improves
resolve rate — the mission's closing-the-loop stage measured that question
in its smallest form (0/12 to 2/12), and the stage's surveys cover the
production claims.
