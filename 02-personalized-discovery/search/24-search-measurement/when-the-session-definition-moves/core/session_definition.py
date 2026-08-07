"""The session definition that moves, read: one log, two funnels.

Stage 24 measures the search funnel from logs, and the funnel starts
with a session boundary. The failure mode this chapter reads is the
definition itself: segment the same log two ways — a fixed timeout
versus topic continuation — and the funnel numbers change, so two
teams with two definitions disagree about whether search improved.

Run:
    uv run python core/session_definition.py
"""

from __future__ import annotations

# (query, minutes since log start, clicked)
EVENTS = [
    ("heaphones", 0, False),
    ("headphones", 5, True),
    ("running shoes", 45, False),
    ("trail runners", 50, True),
    ("headphones", 70, True),
    ("gaming chair", 80, False),
]


def timeout_sessions(events: list[tuple[str, int, bool]], gap: int = 30) -> list[list[int]]:
    sessions: list[list[int]] = []
    for i, (_, ts, _) in enumerate(events):
        if not sessions or ts - events[sessions[-1][-1]][1] > gap:
            sessions.append([i])
        else:
            sessions[-1].append(i)
    return sessions


def topic_sessions(events: list[tuple[str, int, bool]]) -> list[list[int]]:
    sessions: list[list[int]] = []
    for i, (query, _, _) in enumerate(events):
        for s in sessions:
            if any(events[j][0] == query for j in s):
                s.append(i)
                break
        else:
            sessions.append([i])
    return sessions


def funnel(sessions: list[list[int]], events: list[tuple[str, int, bool]]) -> dict[str, float]:
    clicked = sum(1 for s in sessions if any(events[j][2] for j in s))
    zero_q = sum(1 for i, (_, _, c) in enumerate(events) if not c)
    return {
        "sessions": len(sessions),
        "success": clicked / len(sessions),
        "zero_result_sessions": sum(1 for s in sessions if not any(events[j][2] for j in s)) / len(sessions),
        "queries_per_session": len(events) / len(sessions),
        "zero_queries": zero_q / len(events),
    }


def main() -> None:
    a = funnel(timeout_sessions(EVENTS), EVENTS)
    b = funnel(topic_sessions(EVENTS), EVENTS)
    print("session definition, read (one 6-event log, two segmentations):")
    for name, f in (("30-min timeout", a), ("topic continuation", b)):
        print(f"  {name:<20} sessions {f['sessions']}  success {f['success']:.0%}  "
              f"zero-sessions {f['zero_result_sessions']:.0%}  "
              f"queries/session {f['queries_per_session']:.1f}")
    print("\nreading: the same log yields 2 sessions under a 30-minute")
    print("timeout and 5 under topic continuation. The timeout merges")
    print("four distinct topics into one session and reports 100%")
    print("success; the topic splitter exposes the failed queries as")
    print("60% zero-result sessions. Two teams with two definitions")
    print("disagree about whether search improved. The funnel is a")
    print("statement about the definition, so the definition has to be")
    print("owned, documented, and frozen before the numbers mean")
    print("anything.")


if __name__ == "__main__":
    main()
