"""Long context, read: the first-turn grounding falls out of the window.

Stage 36 resolves follow-ups through session context. This script reads
what happens as the session grows past the window: truncation drops the
oldest turns first, and the first-turn topic — exactly the grounding a
follow-up like "back to the first pair" needs — falls out first.

Run:
    uv run python core/long_context.py
"""

from __future__ import annotations

WINDOW = 8


def turn1_kept(session_turns: int) -> bool:
    """Turn 1 stays in the window while the session fits in it."""
    return session_turns <= WINDOW


def resolution(session_turns: int) -> float:
    """Resolution of 'back to the first pair': 1.0 while turn 1 is kept,
    then falls as the dropped grounding recedes."""
    if turn1_kept(session_turns):
        return 1.0
    dropped = session_turns - WINDOW
    return round(max(0.1, 1.0 - dropped * 0.2), 1)


def main() -> None:
    print("long context, read (first-turn grounding vs window):")
    print("  session turns  turn-1 kept  resolution")
    for turns in (4, 8, 9, 12, 24):
        print(
            f"  {turns:<14} {'yes' if turn1_kept(turns) else 'no':<11} "
            f"{resolution(turns)}"
        )
    print("\nreading: truncation drops the oldest turns first, so the")
    print("first-turn topic is the first grounding to fall out of the")
    print("window. A follow-up that says 'back to the first pair' needs")
    print("exactly that turn — pin it, or compress the middle turns")
    print("instead of dropping the oldest.")


if __name__ == "__main__":
    main()
