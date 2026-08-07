"""Real PNG thumbnails for the README, from data this stage already trains
and evaluates on -- no new pixels, no placeholder images.

Two synthetic fixtures (stage 00's `vqa-{0,2}.ppm`) and two real photographs
(stage 03's downsampled COCO/VQA-v2 `pixels_rgb` arrays) are decoded and
re-encoded with `02-report/core/png_encode.py`'s stdlib PNG encoder -- the
same encoder stage 02 uses to hand images to a hosted API, reused rather than
reimplemented.

Run:
    python3 make_thumbnails.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "02-report" / "core"))
from png_encode import encode_png

FIXTURES_DIR = HERE.parents[1] / "00-image-caption-task" / "fixtures"
REAL_PHOTO_DIR = HERE.parents[1] / "03-real-photo-task" / "data" / "raw"
OUT_DIR = HERE.parent / "runs"

FIXTURE_PICKS = ("vqa-0", "vqa-2")
REAL_PHOTO_PICKS = (2, 4)  # eval.jsonl row indices: zebras, baseball


def load_ppm(path: Path) -> tuple[list[tuple[int, int, int]], int, int]:
    """Minimal binary-PPM (P6) reader for the fixed 32x32 fixtures this
    repository writes -- no external image library, matching the stdlib-only
    convention `png_encode.py` itself follows."""
    data = path.read_bytes()
    assert data[:2] == b"P6", f"{path} is not a binary PPM (P6)"
    idx = 2
    tokens: list[int] = []
    while len(tokens) < 3:
        while data[idx : idx + 1].isspace():
            idx += 1
        if data[idx : idx + 1] == b"#":
            while data[idx : idx + 1] not in (b"\n", b""):
                idx += 1
            continue
        start = idx
        while not data[idx : idx + 1].isspace():
            idx += 1
        tokens.append(int(data[start:idx]))
    idx += 1  # single whitespace byte separating the header from binary data
    width, height, maxval = tokens
    assert maxval == 255
    raw = data[idx : idx + width * height * 3]
    pixels = [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]
    return pixels, width, height


def dump(pixels: list[tuple[int, int, int]], width: int, height: int, out_path: Path, label: str) -> None:
    out_path.write_bytes(encode_png(pixels, width, height))
    print(f"wrote {out_path}  ({label})")


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)

    manifest = {}
    with (FIXTURES_DIR / "manifest.jsonl").open() as f:
        for line in f:
            d = json.loads(line)
            manifest[d["id"]] = d

    for fixture_id in FIXTURE_PICKS:
        pixels, w, h = load_ppm(FIXTURES_DIR / "images" / f"{fixture_id}.ppm")
        question = manifest[fixture_id]["qa"][0]["question"]
        dump(pixels, w, h, OUT_DIR / f"thumb-{fixture_id}.png", question)

    real_raw = [json.loads(line) for line in (REAL_PHOTO_DIR / "eval.jsonl").read_text().splitlines() if line]
    for i in REAL_PHOTO_PICKS:
        ex = real_raw[i]
        pixels = [tuple(p) for p in ex["pixels_rgb"]]
        question = ex["qa"][0]["question"]
        dump(pixels, ex["width"], ex["height"], OUT_DIR / f"thumb-{ex['id']}.png", question)


if __name__ == "__main__":
    main()
