# The rule-based intent decomposer, on the mission's three task sets

Rule-based decomposer (no model) turning the mission's mined task records
into a topology-derived task tree: verifiability check, shared-file lanes,
coupling warnings, and a DAG-width verdict.

## Command

```bash
cd 04-agentic-platform/intent-to-plan/decomposing-a-large-intent/core
python3 decomposer.py --tasks ../../../tasks/candidates.jsonl \
    --intent "Make the repository's correctness signals green again"
python3 decomposer.py --tasks ../../../tasks/private.jsonl \
    --intent "Make the repository's correctness signals green again"
python3 decomposer.py --tasks ../../../tasks/public-candidates.jsonl \
    --intent "Harden the itertools library against edge cases"
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS arm64 |
| Python | 3.11 (system) |
| Model | none — rule-based, no API key |
| Cost | \$0 |
| Wall clock | < 1 s total (three runs) |

## Results

| Set | Leaves | Lanes | Coupled pairs | DAG width |
|---|---:|---:|---:|---:|
| private (`private.jsonl`) | 2 | 2 | 0 | 2 |
| private candidates (`candidates.jsonl`) | 4 | 2 | 3 | 2 |
| public candidates (`public-candidates.jsonl`) | 6 | 1 | 15 | 1 |

Every leaf in every set passes the verifiability invariant (has both
`target_tests` and `test_command`).

### The private candidates run, in full

```text
INTENT: Make the repository's correctness signals green again

Lane 1 · touches missions/01-language-model-agent/05-serve/core/engine.py (1 leaf) · independent
└── private-b81c414  fix(serve): attend past the first token in every cached decode step  [done: tests/test_decode_correctness.py]

Lane 2 · shares site/sync-docs.py (3 leaves) · coupled -> serial
├── private-354c352  fix(site): stop escaping angle brackets inside inline code  [done: tests/test_sync_docs.py]
├── private-642074a  fix(site): restore the pages the explicit sidebar dropped  [done: tests/test_sync_docs.py]
└── private-be65ef6  fix(site): drop generated numbers from titles and order indexes correctly  [done: tests/test_sync_docs.py]

Invariant 1 — leaves independently verifiable: 4/4
Invariant 2 — explicit dependencies: 2 lanes, 3 coupled pair(s) flagged
Invariant 3 — collective sufficiency: not mechanically checkable without a constraint list for the intent; reviewer's call
Invariant 4 — QA separated from completion: no order assigned inside a lane; no correctness claim
DAG width (parallel lanes): 2

Coupled pairs (overlap >= 0.30):
  private-354c352 <-> private-642074a  overlap 0.50  shared ['site/sync-docs.py']
  private-354c352 <-> private-be65ef6  overlap 0.50  shared ['site/sync-docs.py']
  private-642074a <-> private-be65ef6  overlap 0.33  shared ['site/sync-docs.py']
Recommendation: do not fan these out; merge into one lane or split by layer after the design doc exists (marcus #267).
```

## What the run establishes

- The four decomposition invariants are checkable mechanically on real task
  records: done-condition presence (invariant 1), shared-file lanes and
  coupling flags (invariant 2), and the refusal to assign lane order or
  claim correctness (invariant 4).
- The topology finding is real, not manufactured: the three site tasks in
  the private candidate set all touch `site/sync-docs.py` and all target
  `tests/test_sync_docs.py`, so a noun-based split ("fix escaping", "fix the
  sidebar", "fix ordering") would fan out three agents onto one file — the
  snake-game failure of marcus #267. The decomposer merges them into one
  serial lane, width 2 total.
- The public candidate set is starker: all six touch `more_itertools/more.py`
  (pairwise overlap 1.00), so the intent "harden the itertools library"
  decomposes to width 1 — a single lane, not a tree. Tree width is a property
  of the code topology, not of the intent's size.

## Honesty note

The decomposer proves the *shape* (lanes, coupling, width). It does not
prove the split is correct: ordering inside a lane is left to the design
review, and collective sufficiency (does the tree cover the intent?) is
declared not mechanically checkable without a constraint list. No
resolve-rate or quality claim is made — the frontier question of how good a
decomposition is stays with the reviewer and with LLM-based decomposition
quality evals, not with this rule-based demo.
