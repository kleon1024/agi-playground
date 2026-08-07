# Run — supervisor-and-workers orchestrator demo, CPU only

**Date:** 2026-07-27
**Hardware:** Apple M1 Pro (arm64), macOS 15.6.1, CPU only. No GPU was used or
needed — the "backend" is a Python dict of scripted strings.
**Software:** Python 3.11.14, stdlib only (no third-party packages).
**Wall-clock:** 0.05s real (`user 0.03s`, `sys 0.01s`), measured with
`/usr/bin/time -p`.
**Cost:** \$0 (local lane).

## Command

```bash
cd 01-language-model/06-agent/would-a-second-agent-help/core
python3 orchestrator.py
```

## Metrics, as produced

```
schedule (batches run in order; tasks within a batch run concurrently):
  batch 0: ['scan_a', 'scan_b']
  batch 1: ['merge']
  batch 2: ['rescan_a']

per-task results:
  scan_a: ok -- 3 TODOs found in module_a  (184 tokens)
  scan_b: ok -- 1 TODO found in module_b  (184 tokens)
  merge: ok -- report.md written, 4 TODOs total  (183 tokens)
  rescan_a: UNUSABLE RETURN -- expected STATUS: and ARTIFACT: lines, the parent cannot act on: 'Looks like module a still has a couple of TODOs, seems fine overall.'  (186 tokens, spent anyway)

wall-clock: 3 batches vs 4 sequential single-agent steps
lossy handoffs: 8
supervisor+workers total tokens: 737
single-agent equivalent cost:    97
multi-agent cost is 7.60x the single-agent baseline for the identical underlying work
```

## Notes

**What this establishes.** Two things, both structural: the scheduler
(`schedule`/`independent` in `core/orchestrator.py`) correctly refuses to
batch `rescan_a` alongside `scan_a` even though nothing in the task graph
declares `rescan_a` as depending on `scan_a` — the conflict is caught purely
from the shared write to `report_a`, which is the parallel-safety rule
working on a case designed to be easy to miss by hand. Separately, the
structured-return parser correctly flags `rescan_a`'s response as unusable
— a human reading "Looks like module a still has a couple of TODOs, seems
fine overall" would understand it fine, but the supervisor cannot safely
act on it, and the 186 tokens it cost were spent regardless of that failure.

**What this does not establish.** The backend is a hand-scripted dict of
fixed strings, not a model of any kind. The 184/184/183/186-token per-task
figures are `len(text) // 4` applied to fixed strings this file wrote, and
the 737 / 97 / 7.60x totals are arithmetic over `SUPERVISOR_OVERHEAD_TOKENS
= 40` and `HANDOFF_TAX_TOKENS = 60`, two constants chosen for this demo, not
measured from any deployed system. Change either constant and the ratio
moves — it is a property of this toy's fixed per-handoff tax, not a claim
about what delegation costs in general, and it says nothing about whether a
real supervisor-and-workers system produces a better *answer* than a single
agent at matched spend. This run demonstrates that the parallel-safety rule
and the structured-return contract are checkable properties of a task graph
and a worker response. It does not demonstrate that multi-agent
orchestration helps on real work — no real agent, real model, or real task
was involved, and the chapter's `status: draft` reflects that this run does
not promote it.
