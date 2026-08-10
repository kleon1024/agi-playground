"""The click as a label, read: why implicit labels are biased.

Search ranking in production rarely has human relevance grades — it has
clicks. But clicks are not relevance: a result at position 1 gets clicked
more than an identical result at position 5, because position itself
drives exposure. This script quantifies the bias and shows what an
unbiased estimator must remove.

Run:
    uv run python core/click_label_read.py
"""

from __future__ import annotations


def main() -> None:
    # True relevance per item; observed clicks are relevance * exposure.
    relevance = {"A": 0.8, "B": 0.6, "C": 0.4}
    exposure = {1: 1.0, 2: 0.5, 3: 0.25}
    print("clicks as labels, read:")
    for item, rel in relevance.items():
        print(f"  item {item}: true relevance {rel}")
    print("\n  observed clicks = relevance x exposure:")
    for pos, (item, rel) in enumerate(zip(relevance, relevance.values()), start=1):
        obs = rel * exposure[pos]
        print(f"    pos {pos} item {item}: observed {obs:.2f} "
              f"(relevance {rel} x exposure {exposure[pos]})")
    print("\nreading: the same item clicked more at pos 1 than pos 3 is")
    print("exposure, not relevance. A ranker trained on raw clicks learns")
    print("to put anything at the top — the position bias. Correcting it")
    print("(e.g. inverse-propensity weighting) is what makes clicks usable")
    print("as relevance labels.")


if __name__ == "__main__":
    main()
