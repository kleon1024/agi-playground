"""The queue you disable is the target you lose.

Stage 02's multi-queue recall assigns each target a provenance — the queue
that alone can find it — and the core's `--disable` flag demonstrates one
queue's loss at a time. This script runs the full sweep: the baseline
coverage with all queues, then coverage with each queue disabled, plus how
many of that queue's own targets the *other* queues recover incidentally.
The claim the stage makes in prose — recall is the one stage downstream
ranking cannot repair — becomes a table.

Everything is imported from the stage's core.

Run:
    uv run python core/queue_disable_sweep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from recall import (
    QUEUE_NAMES,
    build_catalogue,
    build_users,
    run_queues,
    target_coverage,
    union_queues,
)


def main() -> None:
    items = build_catalogue(400, 5, seed=0)
    users = build_users(items, 20, 5, seed=0)
    items_by_id = {it.id: it for it in items}

    def coverage_with(enabled_names: set[str]) -> tuple[float, dict[str, tuple[int, int]]]:
        enabled = {name: name in enabled_names for name in QUEUE_NAMES}
        coverages = []
        per_prov = {name: [0, 0] for name in QUEUE_NAMES}
        for user in users:
            results = run_queues(user, items, items_by_id, 25, enabled)
            candidates = union_queues(results)
            coverages.append(target_coverage(user.targets, candidates))
            for target_id, provenance in user.targets.items():
                per_prov[provenance][1] += 1
                if target_id in candidates:
                    per_prov[provenance][0] += 1
        return sum(coverages) / len(coverages), per_prov

    base, base_prov = coverage_with(set(QUEUE_NAMES))
    print(f"baseline (all queues): mean target coverage {base:.2f}\n")
    print(f"{'disabled queue':<16} {'coverage':>10} {'its targets found':>18} {'recovered by others':>20}")
    for name in QUEUE_NAMES:
        if base_prov[name][1] == 0:
            continue
        cov, prov = coverage_with(set(QUEUE_NAMES) - {name})
        found, total = prov[name]
        recovered = base_prov[name][0] - found
        print(f"{name:<16} {cov:>10.2f} {found:>8}/{total:<8} {recovered:>20}")


if __name__ == "__main__":
    main()
