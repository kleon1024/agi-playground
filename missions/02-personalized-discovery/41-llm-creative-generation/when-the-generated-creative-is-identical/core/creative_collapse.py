"""Creative collapse, read: the generator that repeats itself.

Stage 41 generates creative variants with an LLM. This script reads the
failure where generation collapses to near-identical variants.

Run:
    uv run python core/creative_collapse.py
"""

from __future__ import annotations


def main() -> None:
    variants = [
        "'Run faster, pay less'",
        "'Run faster. Pay less.'",
        "'run faster pay less",
    ]
    unique = len({v.replace("'", "").replace(".", "").lower() for v in variants})
    print("creative collapse, read (3 generated variants):")
    for v in variants:
        print(f"  {v}")
    print(f"  distinct after normalization: {unique}")
    print("\nreading: three variants collapse to two distinct messages, so")
    print("selection is choosing between a copy and a punctuation edit —")
    print("the scoring model cannot find real creative distance.")
    print("LLM generation needs a diversity control (temperature, ")
    print("repetition penalty) or the creative space shrinks to the")
    print("mode the model prefers.")


if __name__ == "__main__":
    main()
