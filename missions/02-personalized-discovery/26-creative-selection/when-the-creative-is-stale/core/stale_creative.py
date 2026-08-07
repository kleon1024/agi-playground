"""The stale creative, read: what won yesterday loses today.

Stage 26 selects creatives from logged CTR. This script reads a creative
whose click value decays as users see it.

Run:
    uv run python core/stale_creative.py
"""

from __future__ import annotations


def main() -> None:
    ctrs = {"creative_a": 0.06, "creative_b": 0.04, "creative_c": 0.03}
    print("stale creative, read:")
    for name, ctr in sorted(ctrs.items(), key=lambda kv: -kv[1]):
        print(f"  {name}: logged ctr {ctr:.2f}")
    print("  creative_a has run 200,000 times; users have seen it")
    print("  creative_c is new; logged ctr is a cold-start estimate")
    print("\nreading: logged CTR mixes the creative's quality with its")
    print("wear. A stale winner keeps winning the selection on history")
    print("while its true value decays — selection needs recency-aware")
    print("estimates, not just averages.")


if __name__ == "__main__":
    main()
