"""A minimal SQLite memory store, fed by this mission's recorded runs.

The memory question this file demonstrates is the two-layer split that
production coding agents converged on: a static instruction layer (the
AGENTS.md / CLAUDE.md file a human writes) and a generated layer (what the
agent itself learned and promoted). The generated layer is what a store
like this holds. Every fact below is taken from this mission's `runs/`
records — no number is invented, and the source file is named on each row.

The demo shows three operations:

1. **write** — lessons land in a `lessons` table with a source, a claim,
   and keywords.
2. **recall** — a decision question is matched against keywords, and the
   matching lessons are returned, oldest-promoted first.
3. **promote** — a lesson that is recalled for a second decision moves from
   `ephemeral` to `durable`. This is the memory-hygiene rule in miniature:
   promotion on repeat use, not on sentiment.

No model is called. Recall is `LIKE` keyword matching, which is exactly the
limitation this chapter is about — it is why the industry moved to vector
retrieval for open-ended recall and kept keyword stores for exact facts.

Run:
    python sqlite_memory.py --db /tmp/mem.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Lesson:
    source: str
    claim: str
    keywords: str


# Facts from this mission's recorded runs; source is the runs/ file that
# measured each one. No number here is estimated.
SEED_LESSONS = [
    Lesson(
        source="no-harness/runs/2026-08-06-blind-call-read.md",
        claim="haiku resolves 0/6 on the blind-call arm; opus 3/6 at $1.09 per resolved",
        keywords="haiku blind-call resolve tier opus cost-per-resolved",
    ),
    Lesson(
        source="agent-loop/runs/2026-07-29-harness-end-to-end.md",
        claim="the test-tampering guardrail fires only on the diff, because deleting a failing target test is invisible to regression checks",
        keywords="guardrail tamper diff test-file regression",
    ),
    Lesson(
        source="cheap-or-expensive/runs/",
        claim="the full harness resolved 18/18 across all tiers at $0.16-$0.82 per resolved; the cheap tier's patches hid latent defects the metric cannot see",
        keywords="routing tier cost resolve-rate latent-defect",
    ),
    Lesson(
        source="closing-the-loop/runs/",
        claim="showing a model its own failed diff plus the real error moved pooled resolve from 0/12 to 2/12, only where a rejected diff became applicable",
        keywords="feedback retry diff-apply resolve closing-the-loop",
    ),
    Lesson(
        source="how-it-fails/runs/2026-08-06-failure-costs.md",
        claim="11 of 12 no-harness failures never produced a diff git apply would accept; the failure concentrates on identity checks",
        keywords="no-harness patch-apply failure identity-check",
    ),
    Lesson(
        source="how-it-fails/runs/2026-08-01-failure-taxonomy.md",
        claim="the harness arm is 0/18 in every failure category across 42+ real attempts; never-firing is a property of this task set, not a proof of safety",
        keywords="zero-failure taxonomy guardrail task-set boundary",
    ),
]


class SqliteMemory:
    def __init__(self, db: Path) -> None:
        self.db = db
        self.conn = sqlite3.connect(db)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY,
                source TEXT NOT NULL,
                claim TEXT NOT NULL,
                keywords TEXT NOT NULL,
                tier TEXT NOT NULL DEFAULT 'ephemeral',
                recalls INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self.conn.commit()

    def seed(self) -> int:
        count = self.conn.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
        if count:
            return count
        for lesson in SEED_LESSONS:
            self.conn.execute(
                "INSERT INTO lessons (source, claim, keywords) VALUES (?, ?, ?)",
                (lesson.source, lesson.claim, lesson.keywords),
            )
        self.conn.commit()
        return len(SEED_LESSONS)

    def recall(self, question: str, limit: int = 3) -> list[dict]:
        """Keyword recall: rows whose keywords appear in the question."""
        rows = self.conn.execute(
            """
            SELECT id, source, claim, tier, recalls, keywords FROM lessons
            ORDER BY (tier = 'durable') DESC, recalls DESC, id ASC
            """
        ).fetchall()
        hits = []
        for row in rows:
            lesson_id, source, claim, tier, recalls, keywords = row
            if any(kw in question.lower() for kw in keywords.split()):
                hits.append(
                    {"id": lesson_id, "source": source, "claim": claim,
                     "tier": tier, "recalls": recalls}
                )
        return hits[:limit]

    def promote(self, lesson_id: int) -> str:
        """Promotion on the second recall — the two-incident rule, minus the
        incident: a durable lesson is one the store kept producing."""
        row = self.conn.execute(
            "SELECT tier, recalls FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        tier, recalls = row[0], row[1] + 1
        new_tier = "durable" if (tier == "ephemeral" and recalls >= 2) else tier
        self.conn.execute(
            "UPDATE lessons SET recalls = ?, tier = ? WHERE id = ?",
            (recalls, new_tier, lesson_id),
        )
        self.conn.commit()
        return new_tier

    def snapshot(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, source, claim, tier, recalls FROM lessons ORDER BY id"
        ).fetchall()
        return [
            {"id": r[0], "source": r[1], "claim": r[2], "tier": r[3], "recalls": r[4]}
            for r in rows
        ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default="/tmp/mem.db")
    ap.add_argument("--out", help="write the run record as JSON")
    args = ap.parse_args()

    started = time.monotonic()
    mem = SqliteMemory(Path(args.db))
    seeded = mem.seed()

    # Two decision questions, to trigger the promotion rule.
    questions = [
        "new bug report: which tier should resolve it, and what does the blind-call baseline say?",
        "another report came in; is the resolve rate still believable when nothing failed?",
    ]
    timeline = []
    for q in questions:
        hits = mem.recall(q, limit=3)
        promoted = [mem.promote(h["id"]) for h in hits]
        timeline.append(
            {"question": q, "recalled": [h["id"] for h in hits],
             "tiers_after": promoted}
        )

    record = {
        "operation": "sqlite-memory demo",
        "seeded_lessons": seeded,
        "timeline": timeline,
        "snapshot": mem.snapshot(),
        "wall_clock_s": round(time.monotonic() - started, 3),
        "model_calls": 0,
    }
    print(json.dumps(record, indent=2, ensure_ascii=False))
    if args.out:
        Path(args.out).write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
