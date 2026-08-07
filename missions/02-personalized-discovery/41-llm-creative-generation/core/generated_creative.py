"""LLM creative generation, read: variants scored before they run.

Stage 41 is the frontier of creative selection: an LLM generates ad
variants, and the platform scores them before spending impressions.
This script reads a scored generation pass.

Run:
    uv run python core/generated_creative.py
"""

from __future__ import annotations


def main() -> None:
    variants = [
        ("v1: 'Run faster, pay less'", 0.08),
        ("v2: 'Marathon shoes, 20% off'", 0.06),
        ("v3: 'New season, new pace'", 0.04),
        ("v4: 'Buy now'", 0.02),
    ]
    print("llm creative generation, read:")
    for text, score in variants:
        print(f"  {score:.2f}  {text}")
    winner = max(variants, key=lambda x: x[1])
    print(f"  selected: {winner[0]}")
    print("\nreading: generation is cheap, impressions are not — the LLM")
    print("produces variants and a scoring model picks before delivery.")
    print("The frontier risk is collapse (identical variants) and surface")
    print("scoring that misses real CTR, which the detours price.")


if __name__ == "__main__":
    main()
