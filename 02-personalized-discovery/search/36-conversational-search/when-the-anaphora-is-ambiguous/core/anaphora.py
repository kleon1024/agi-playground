"""Anaphora, read: the pronoun that needs an entity.

Stage 36 resolves follow-ups. This script reads a pronoun whose
referent depends on which entities the session introduced.

Run:
    uv run python core/anaphora.py
"""

from __future__ import annotations


def main() -> None:
    entities = ["trail runners", "road trainers"]
    follow_up = "are they waterproof?"
    # Resolve 'they' to each candidate.
    print("anaphora, read:")
    print(f"  entities in session: {entities}")
    print(f"  follow-up: '{follow_up}'")
    for entity in entities:
        print(f"    'they' -> {entity}: {'plausible' if entity != 'road trainers' else 'ambiguous'}")
    print("\nreading: 'they' is ambiguous between two shoe types in the")
    print("session. Resolving it wrong changes the answer — conversational")
    print("search has to track referents, not just reuse the last query.")


if __name__ == "__main__":
    main()
