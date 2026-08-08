"""Read a real query log and measure session-level recovery.

Input: a directory containing the canonical AOL 2006 user-ct collection
(user-ct-test-collection-01.txt and user-ct-test-collection-02..10.txt.gz),
one tab-separated line per query: AnonID, Query, QueryTime, ItemRank,
ClickURL.  ItemRank is empty for zero-click queries.

The read answers one question: of the queries a per-query report counts as
failures (zero clicks), how many are actually recovered sessions -- the
user reformulated and the reformulation clicked?  It also splits the read by
query frequency (head / body / tail) and by the recovery channel (a typo
fix within edit distance 2 versus a semantic reformulation), which is the
read stage 19's correction claims rest on.

Definitions, fixed before the run:
- session: consecutive queries of one user separated by at most 30 minutes
  (the standard fixed timeout; Jones and Klinkner, CIKM 2008);
- reformulation: a later query in the same session that shares a token with
  the earlier query, or is within edit distance 2 of it (query
  reformulation heuristics of the kind Huang and Efthimiadis, CIKM 2009,
  classify);
- recovered: a zero-click query with a later clicked reformulation in the
  same session;
- abandoned: a zero-click query with no later reformulation in the session.

Only aggregates are printed.  Raw queries are never emitted: this is a
public research log containing real users' searches, and the chapter that
owns this read reports distributions, not rows.
"""

from __future__ import annotations

import gzip
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

SESSION_TIMEOUT_S = 30 * 60
HEAD_FREQ = 1000
MID_FREQ = 10
TYPO_EDIT = 2
RECOVERY_WINDOW = 25


def query_time(fields: list[str]) -> int:
    """Parse AOL's YYYY-MM-DD HH:MM:SS into a UTC epoch second."""
    return int(
        datetime.strptime(fields[2], "%Y-%m-%d %H:%M:%S")
        .replace(tzinfo=UTC)
        .timestamp()
    )


def normalize(query: str) -> str:
    return query.strip().lower()


def tokens(query: str) -> set[str]:
    """Alphanumeric runs, lowercased.  A query is its own token set."""
    out: set[str] = set()
    current: list[str] = []
    for ch in query:
        if ch.isalnum():
            current.append(ch)
        elif current:
            out.add("".join(current))
            current = []
    if current:
        out.add("".join(current))
    return out


def edit_distance_bounded(a: str, b: str, cap: int = TYPO_EDIT) -> int:
    """Levenshtein distance, computed only within a band of width `cap`.

    Rows outside the band cannot improve on the cap, so the DP runs in
    O(len * cap) instead of O(len^2) and returns early once the distance is
    provably above the cap.
    """
    n, m = len(a), len(b)
    if abs(n - m) > cap:
        return cap + 1
    prev = [i for i in range(m + 1)]
    for i in range(1, n + 1):
        lo = max(1, i - cap)
        hi = min(m, i + cap)
        row = [cap + 1] * (m + 1)  # out-of-band cells cannot beat the cap
        row[0] = i
        for j in range(lo, hi + 1):
            row[j] = min(
                row[j - 1] + 1,
                prev[j] + 1,
                prev[j - 1] + (a[i - 1] != b[j - 1]),
            )
        prev = row
    return prev[m]


def reformulates(
    a: str, b: str, tok_cache: dict[str, frozenset[str]] | None = None
) -> bool:
    """True when b is a plausible reformulation of a (distinct, related)."""
    if a == b or not a or not b:
        return False
    ta = tok_cache.get(a) if tok_cache is not None else None
    if ta is None:
        ta = frozenset(tokens(a))
        if tok_cache is not None:
            tok_cache[a] = ta
    tb = tok_cache.get(b) if tok_cache is not None else None
    if tb is None:
        tb = frozenset(tokens(b))
        if tok_cache is not None:
            tok_cache[b] = tb
    if ta & tb:
        return True
    if abs(len(a) - len(b)) <= TYPO_EDIT:
        return edit_distance_bounded(a, b) <= TYPO_EDIT
    return False


def typo_channel(a: str, b: str) -> bool:
    """The recovery went through a near-edit fix, not a semantic rewrite."""
    return (
        abs(len(a) - len(b)) <= TYPO_EDIT
        and edit_distance_bounded(a, b) <= TYPO_EDIT
    )


def iter_lines(data_dir: Path):
    """Yield parsed rows from the collection in file order 01..10."""
    files = sorted(
        data_dir.glob("user-ct-test-collection-*.txt*"),
        key=lambda p: p.name,
    )
    for path in files:
        try:
            opener = gzip.open if path.suffix == ".gz" else open
            with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
                for raw in handle:
                    if raw.startswith("AnonID\t"):
                        continue  # one header row per file
                    yield path.name, raw
        except (EOFError, gzip.BadGzipFile) as exc:
            print(
                f"warning: truncated file skipped: {path.name} ({exc})",
                file=sys.stderr,
            )


def read_collection(data_dir: Path):
    """Pass 1: counts per normalized query, plus corpus totals."""
    freq: Counter[str] = Counter()
    totals = Counter()
    last_file = None
    for _file, raw in iter_lines(data_dir):
        if _file != last_file:
            print(f"pass 1: reading {_file}", file=sys.stderr)
            last_file = _file
        fields = raw.rstrip("\n").split("\t")
        totals["lines"] += 1
        if len(fields) < 4:
            totals["malformed"] += 1
            continue
        query = normalize(fields[1])
        if query:
            freq[query] += 1
        totals["queries"] += 1
        if len(fields) > 3 and fields[3].strip():
            totals["clicks"] += 1
    return freq, totals


def bucket(freq: Counter[str], query: str) -> str:
    count = freq.get(query, 0)
    if count >= HEAD_FREQ:
        return "head"
    if count >= MID_FREQ:
        return "body"
    return "tail"


def classify_session(
    queries: list[tuple[int, str, bool]], freq: Counter[str]
) -> tuple[Counter, Counter, Counter]:
    """Run the outcome rules over one session; return verdict, bucket, channel."""
    verdict: Counter[str] = Counter()
    bucket_verdict: Counter[str] = Counter()
    channel: Counter[str] = Counter()
    tok_cache: dict[str, frozenset[str]] = {}
    for i, (_t, q_i, clicked) in enumerate(queries):
        if clicked:
            verdict["clicked"] += 1
            bucket_verdict[f"clicked:{bucket(freq, q_i)}"] += 1
            continue
        first_clicked_ref: str | None = None
        any_ref = False
        any_typo_ref = False
        window = queries[i + 1 : i + 1 + RECOVERY_WINDOW]
        for _t, q_j, c_j in window:
            if not reformulates(q_i, q_j, tok_cache):
                continue
            any_ref = True
            if typo_channel(q_i, q_j):
                any_typo_ref = True
            if c_j and first_clicked_ref is None:
                first_clicked_ref = q_j
                break
        if first_clicked_ref is not None:
            verdict["recovered"] += 1
            bucket_verdict[f"recovered:{bucket(freq, q_i)}"] += 1
            if typo_channel(q_i, first_clicked_ref):
                channel["recovered:typo"] += 1
            else:
                channel["recovered:semantic"] += 1
        elif any_ref:
            verdict["reformulated_no_click"] += 1
            bucket_verdict[f"reformulated_no_click:{bucket(freq, q_i)}"] += 1
            if any_typo_ref:
                channel["fix_offered_still_nothing"] += 1
        else:
            verdict["abandoned"] += 1
            bucket_verdict[f"abandoned:{bucket(freq, q_i)}"] += 1
            if any_typo_ref:
                channel["fix_offered_still_nothing"] += 1
    return verdict, bucket_verdict, channel


def analyze(data_dir: Path, freq: Counter[str]) -> tuple[Counter, Counter, Counter]:
    """Pass 2: per-user, per-session outcome classification (streaming)."""
    verdict: Counter[str] = Counter()
    bucket_verdict: Counter[str] = Counter()
    channel: Counter[str] = Counter()
    current_user: str | None = None
    buffer: list[tuple[int, str, bool]] = []
    prev_id: str | None = None
    unsorted = 0
    last_file = None

    def flush() -> None:
        nonlocal buffer
        buffer.sort(key=lambda row: row[0])
        sessions: list[list[tuple[int, str, bool]]] = []
        for row in buffer:
            if sessions and row[0] - sessions[-1][-1][0] > SESSION_TIMEOUT_S:
                sessions.append([row])
            else:
                if sessions:
                    sessions[-1].append(row)
                else:
                    sessions.append([row])
        for session in sessions:
            v, b, c = classify_session(session, freq)
            verdict.update(v)
            bucket_verdict.update(b)
            channel.update(c)
        verdict["sessions"] += len(sessions)
        buffer = []

    for _file, raw in iter_lines(data_dir):
        if _file != last_file:
            print(f"pass 2: reading {_file}", file=sys.stderr)
            last_file = _file
        fields = raw.rstrip("\n").split("\t")
        if len(fields) < 4:
            continue
        user = fields[0]
        if prev_id is not None and user < prev_id:
            unsorted += 1
        prev_id = user
        if current_user is not None and user != current_user:
            flush()
        current_user = user
        query = normalize(fields[1])
        if not query:
            continue
        clicked = bool(fields[3].strip()) if len(fields) > 3 else False
        buffer.append((query_time(fields), query, clicked))
    if buffer:
        flush()
    verdict["unsorted_rows"] = unsorted
    return verdict, bucket_verdict, channel


def pct(part: int, whole: int) -> str:
    return f"{100.0 * part / whole:5.1f}" if whole else "  0.0"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: uv run python core/session_recovery.py <aol-collection-dir>")
        return 2
    data_dir = Path(sys.argv[1])
    if not data_dir.is_dir():
        print(f"not a directory: {data_dir}")
        return 2

    print("== 1. the corpus, read ==")
    freq, totals = read_collection(data_dir)
    file_count = len(list(data_dir.glob("user-ct-test-collection-*.txt*")))
    print(f"files {file_count} of user-ct-test-collection-01..10 | lines {totals['lines']:,}")
    print(f"queries {totals['queries']:,} | clicks {totals['clicks']:,} "
          f"| zero-click {totals['queries'] - totals['clicks']:,} "
          f"| malformed {totals['malformed']:,}")
    print(f"unique normalized queries {len(freq):,} "
          f"| head >= {HEAD_FREQ} | body {MID_FREQ}..{HEAD_FREQ - 1} | tail < {MID_FREQ}")

    print()
    print("== 2. the session read: per-query verdict vs session verdict ==")
    verdict, bucket_verdict, channel = analyze(data_dir, freq)
    queries = totals["queries"]
    zero_click = verdict["recovered"] + verdict["reformulated_no_click"] + verdict["abandoned"]
    print(f"queries classified {sum(verdict[k] for k in ('clicked', 'recovered', 'reformulated_no_click', 'abandoned')):,} "
          f"| sessions {verdict['sessions']:,} | 30-min timeout | unsorted rows {verdict['unsorted_rows']}")
    print()
    print(f"{'verdict':<24}{'queries':>12}{'pct of all':>12}{'pct of zero-click':>18}")
    rows = [
        ("clicked", verdict["clicked"]),
        ("zero-click: recovered", verdict["recovered"]),
        ("zero-click: reformulated, no click", verdict["reformulated_no_click"]),
        ("zero-click: abandoned", verdict["abandoned"]),
    ]
    for label, value in rows:
        if label == "clicked":
            print(f"{label:<24}{value:>12,}{pct(value, queries):>11}%{'n/a':>18}")
        else:
            print(f"{label:<24}{value:>12,}{pct(value, queries):>11}%{pct(value, zero_click):>17}%")

    per_query_failure = 100.0 * zero_click / queries
    recovery_of_failures = 100.0 * verdict["recovered"] / zero_click
    print()
    print(f"per-query report counts {per_query_failure:.1f}% of queries as failures "
          f"(zero clicks); the session read reclassifies {recovery_of_failures:.1f}% of "
          "those as recovered sessions")

    print()
    print("== 3. the distribution read: recovery by query frequency ==")
    print(f"{'stratum':<10}{'queries':>12}{'traffic':>10}{'zero-click':>12}{'of zero-click recovered':>24}{'of zero-click abandoned':>24}")
    for stratum in ("head", "body", "tail"):
        stratum_queries = sum(
            bucket_verdict[f"{k}:{stratum}"]
            for k in ("clicked", "recovered", "reformulated_no_click", "abandoned")
        )
        stratum_zero = (
            bucket_verdict[f"recovered:{stratum}"]
            + bucket_verdict[f"reformulated_no_click:{stratum}"]
            + bucket_verdict[f"abandoned:{stratum}"]
        )
        recovered = bucket_verdict[f"recovered:{stratum}"]
        abandoned = bucket_verdict[f"abandoned:{stratum}"]
        print(
            f"{stratum:<10}{stratum_queries:>12,}{pct(stratum_queries, queries):>9}%"
            f"{pct(stratum_zero, stratum_queries):>11}%"
            f"{pct(recovered, stratum_zero):>23}%"
            f"{pct(abandoned, stratum_zero):>23}%"
        )

    print()
    print("== 4. the correction channel: what recovers, and what never does ==")
    typo_recovered = channel["recovered:typo"]
    semantic_recovered = channel["recovered:semantic"]
    print(f"recovered via near-edit typo fix (edit distance <= {TYPO_EDIT}): "
          f"{typo_recovered:,} ({pct(typo_recovered, verdict['recovered'])}% of recovered)")
    print(f"recovered via semantic reformulation: "
          f"{semantic_recovered:,} ({pct(semantic_recovered, verdict['recovered'])}% of recovered)")
    fix_offered = channel["fix_offered_still_nothing"]
    no_repair = zero_click - verdict["recovered"] - fix_offered
    print(f"fix offered, still nothing (a near-edit reformulation existed in the "
          f"session, none clicked): {fix_offered:,} ({pct(fix_offered, zero_click)}% of zero-click)")
    print(f"no repair attempted in session: {no_repair:,} ({pct(no_repair, zero_click)}% of zero-click)")
    print("(a query whose recovering reformulation is a near-edit fix is "
          "the stage-19 correction channel; a semantic reformulation is not)")

    print()
    print("== verdict ==")
    if recovery_of_failures > 10:
        print("RECOVERED SESSION: the per-query failure rate overstates loss; "
              f"the session read reclassifies {recovery_of_failures:.1f}% of zero-click "
              "queries as recovered sessions.")
    else:
        print("no headline split: fewer than 10% of zero-click queries recover in-session.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
