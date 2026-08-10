"""Creative selection, read: the ad's look decides the click.

Stage 26 picks which creative of an ad to show. This script reads
creative CTR by context and the winner the selection picks.

Run:
    uv run python core/creative_choice.py
"""

from __future__ import annotations


def main() -> None:
    # (creative, ctr on mobile, ctr on desktop)
    creatives = [
        ("video", 0.07, 0.03),
        ("image", 0.04, 0.05),
        ("text", 0.02, 0.02),
    ]
    print("creative selection, read:")
    for name, mobile, desktop in creatives:
        best = "mobile" if mobile > desktop else "desktop"
        print(f"  {name}: mobile {mobile:.2f} desktop {desktop:.2f} -> {best}")
    print("\nreading: the video creative wins on mobile, the image on")
    print("desktop. Selecting by context instead of a global average lifts")
    print("the click rate per placement — the creative is part of the")
    print("ad's expected value, which is why it feeds eCPM.")


if __name__ == "__main__":
    main()
