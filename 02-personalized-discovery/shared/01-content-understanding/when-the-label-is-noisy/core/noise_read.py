"""Label noise, read: the threshold inherits the label's error.

Stage 01 classifies content by a confidence threshold. This script labels
items with a noisy oracle and shows what the noise does to the items the
threshold keeps.

Run:
    uv run python core/noise_read.py
"""

from __future__ import annotations


def main() -> None:
    # (item, true class, noisy label, confidence)
    items = [
        ("a", "recipe", "recipe", 0.91),
        ("b", "recipe", "recipe", 0.84),
        ("c", "news", "recipe", 0.78),
        ("d", "recipe", "news", 0.74),
        ("e", "news", "news", 0.62),
    ]
    threshold = 0.7
    kept = [item for item in items if item[3] >= threshold]
    correct = sum(1 for i in kept if i[1] == i[2])
    print("label noise, read (threshold 0.70):")
    for name, true, label, conf in items:
        kept_flag = "kept" if conf >= threshold else "cut"
        ok = "ok" if true == label else "WRONG"
        print(f"  {name}: true={true} label={label} conf={conf:.2f} {kept_flag} {ok}")
    print(f"\nreading: {correct}/{len(kept)} kept items carry a correct label.")
    print("The threshold gates confidence, not truth — noise in the label")
    print("passes through it. Precision is a property of the label source")
    print("first, and of the threshold second.")


if __name__ == "__main__":
    main()
