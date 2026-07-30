"""Generate a synthetic image + question + answer dataset, from scratch.

No PIL, no numpy, no torch -- this repository's default dependency group has
none of them, and a 32x32 canvas of filled shapes needs nothing beyond
`random` and integer arithmetic. Images are raw RGB pixel buffers, serialized
as PPM (P6, binary) -- a header of three lines followed by raw bytes, the
simplest image format that exists and the reason it was picked here.

Each image is a 2x2 grid of 16x16 cells (left/right x top/bottom). Between one
and three cells are occupied by a filled shape (circle, square, or triangle)
in one of four colors; the rest stay blank. Placing shapes on a fixed grid
guarantees no two shapes overlap without any collision-detection code.

Why question templates are conditionally applicable, not always asked: a
dataset where the same question always has the same shape of answer lets a
model (or a baseline) guess correctly without ever looking at the image. This
is the leakage trap mission 05's mission.yaml names directly. So:

  - "How many shapes/{type}s are there?" is always askable, and the count is
    randomized (0-3), so the answer distribution has real entropy.
  - "What color is the {type}?" is askable ONLY when the image contains
    exactly one instance of that shape type -- otherwise the question is
    ambiguous and is skipped for this image rather than given a made-up
    answer.
  - "What shape is on the {left/right}?" is askable ONLY when exactly one
    shape sits in that column -- same reasoning.
  - "Is there a {type}?" is a yes/no question whose answer is genuinely
    balanced across the dataset, since shape counts and types are randomized
    per image.

Two disjoint seed ranges produce train and eval; a SHA-256 hash of each
image's raw pixel bytes is used to check, programmatically, that no eval
image is byte-identical to any training image (the guardrail mission.yaml
names: "checked programmatically, so no eval instance is a near-duplicate of
a training instance").

Usage:
    python generate_dataset.py --train 2000 --eval 400 --out ../data/raw
    python generate_dataset.py --fixtures 8 --out ../fixtures
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

WIDTH = HEIGHT = 32
CELL = 16
SHAPES = ("circle", "square", "triangle")
COLORS = {
    "red": (220, 40, 40),
    "green": (40, 160, 60),
    "blue": (40, 90, 220),
    "yellow": (230, 200, 40),
}
COLOR_NAMES = list(COLORS)
BACKGROUND: tuple[int, int, int] = (255, 255, 255)

# Grid cells as (row, col) -> (row_label, col_label). (0, 0) is top-left.
CELLS = [(r, c) for r in range(2) for c in range(2)]
ROW_LABEL = {0: "top", 1: "bottom"}
COL_LABEL = {0: "left", 1: "right"}


HALF_SIZES = (3, 4, 5)  # max half+|offset| = 5+2 = 7, safely inside a 16px cell
OFFSETS = (-2, -1, 0, 1, 2)


@dataclass
class ShapePlacement:
    shape: str
    color: str
    row: int
    col: int
    half: int
    dx: int
    dy: int


def _set_pixel(pixels: list[tuple[int, int, int]], x: int, y: int, color: tuple[int, int, int]) -> None:
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        pixels[y * WIDTH + x] = color


def _draw_square(pixels: list, cx: int, cy: int, half: int, color: tuple) -> None:
    for y in range(cy - half, cy + half + 1):
        for x in range(cx - half, cx + half + 1):
            _set_pixel(pixels, x, y, color)


def _draw_circle(pixels: list, cx: int, cy: int, r: int, color: tuple) -> None:
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                _set_pixel(pixels, x, y, color)


def _draw_triangle(pixels: list, cx: int, cy: int, half: int, color: tuple) -> None:
    # Upward-pointing triangle inscribed in a (2*half+1)-tall box, one scanline
    # at a time -- the row width grows linearly from a point at the top.
    top = cy - half
    bottom = cy + half
    for y in range(top, bottom + 1):
        frac = (y - top) / max(1, (bottom - top))
        row_half = round(frac * half)
        for x in range(cx - row_half, cx + row_half + 1):
            _set_pixel(pixels, x, y, color)


_DRAW = {"square": _draw_square, "circle": _draw_circle, "triangle": _draw_triangle}


def render(shapes: list[ShapePlacement]) -> list[tuple[int, int, int]]:
    pixels = [BACKGROUND] * (WIDTH * HEIGHT)
    for s in shapes:
        cx = s.col * CELL + CELL // 2 + s.dx
        cy = s.row * CELL + CELL // 2 + s.dy
        _DRAW[s.shape](pixels, cx, cy, s.half, COLORS[s.color])
    return pixels


def to_ppm_bytes(pixels: list[tuple[int, int, int]]) -> bytes:
    header = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")
    body = bytearray()
    for r, g, b in pixels:
        body += bytes((r, g, b))
    return header + bytes(body)


def sample_shapes(rng: random.Random) -> list[ShapePlacement]:
    # Size and position jitter widen the per-cell state space from 12 options
    # (3 shapes x 4 colors) to 12 x 3 x 5 x 5 = 900. Without it, a single-shape
    # image has only 4 cells x 12 = 48 possible states -- far fewer than the
    # ~700 single-shape images this dataset draws -- and the first real run of
    # this generator (see runs/) hit exactly that: train exhausted nearly the
    # whole n=1 state space, so every fresh eval draw in that bucket collided
    # with an existing training image and the rejection sampler silently
    # dropped n=1 out of eval entirely.
    n = rng.randint(1, 3)
    cells = rng.sample(CELLS, n)
    return [
        ShapePlacement(
            shape=rng.choice(SHAPES),
            color=rng.choice(COLOR_NAMES),
            row=r,
            col=c,
            half=rng.choice(HALF_SIZES),
            dx=rng.choice(OFFSETS),
            dy=rng.choice(OFFSETS),
        )
        for (r, c) in cells
    ]


def build_questions(rng: random.Random, shapes: list[ShapePlacement]) -> list[dict]:
    candidates: list[dict] = []

    # Always askable: total count, entropy comes from randint(1, 3) above.
    candidates.append(
        {"type": "total_count", "question": "How many shapes are in the image?", "answer": str(len(shapes))}
    )

    # Always askable: per-type count, including zero -- the answer is not
    # implied by the question wording since the type asked about is random.
    asked_type = rng.choice(SHAPES)
    count = sum(1 for s in shapes if s.shape == asked_type)
    candidates.append(
        {
            "type": "shape_count",
            "question": f"How many {asked_type}s are there?",
            "answer": str(count),
        }
    )

    # Always askable: presence, balanced because shape sets are randomized.
    present_type = rng.choice(SHAPES)
    present = any(s.shape == present_type for s in shapes)
    candidates.append(
        {
            "type": "presence",
            "question": f"Is there a {present_type} in the image?",
            "answer": "yes" if present else "no",
        }
    )

    # Conditionally askable: color of a uniquely-present shape type only.
    for shape_type in SHAPES:
        matches = [s for s in shapes if s.shape == shape_type]
        if len(matches) == 1:
            candidates.append(
                {
                    "type": "shape_color",
                    "question": f"What color is the {shape_type}?",
                    "answer": matches[0].color,
                }
            )

    # Conditionally askable: shape on a column that holds exactly one shape.
    for col, label in COL_LABEL.items():
        matches = [s for s in shapes if s.col == col]
        if len(matches) == 1:
            candidates.append(
                {
                    "type": "column_shape",
                    "question": f"What shape is on the {label}?",
                    "answer": matches[0].shape,
                }
            )

    # Two questions per image, biased toward the conditional (harder) kind
    # when available, so the dataset is not dominated by the always-askable
    # count/presence templates.
    conditional = [c for c in candidates if c["type"] in ("shape_color", "column_shape")]
    always = [c for c in candidates if c["type"] not in ("shape_color", "column_shape")]
    chosen: list[dict] = []
    if conditional:
        chosen.append(rng.choice(conditional))
    remaining_pool = [c for c in candidates if c not in chosen]
    chosen.append(rng.choice(remaining_pool if remaining_pool else always))
    return chosen


def make_example(seed: int) -> dict:
    rng = random.Random(seed)
    shapes = sample_shapes(rng)
    pixels = render(shapes)
    qa = build_questions(rng, shapes)
    digest = hashlib.sha256(bytes(b for px in pixels for b in px)).hexdigest()
    return {
        "id": f"vqa-{seed}",
        "seed": seed,
        "width": WIDTH,
        "height": HEIGHT,
        "pixels_rgb": [list(px) for px in pixels],
        "pixel_hash": digest,
        "shapes": [asdict(s) for s in shapes],
        "qa": qa,
    }


def write_jsonl(examples: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for ex in examples:
            fh.write(json.dumps(ex) + "\n")


def check_disjoint(train: list[dict], eval_: list[dict]) -> int:
    train_hashes = {ex["pixel_hash"] for ex in train}
    eval_hashes = {ex["pixel_hash"] for ex in eval_}
    return len(train_hashes & eval_hashes)


def make_eval_set_disjoint_from(
    train: list[dict], n: int, seed_start: int
) -> tuple[list[dict], int]:
    """Draw `n` eval examples whose pixel hash never appears in `train`.

    The first real run of this generator (2,000 train + 400 eval, seeds drawn
    from disjoint ranges) still produced 116 pixel-identical collisions
    between the two sets: with 3 shapes x 4 colors x 4 cells x 1-3 occupied
    cells, the image space is only a few thousand points wide, and a few
    thousand random draws from it hit the same point by the birthday paradox
    -- disjoint SEED ranges do not imply disjoint IMAGES when the underlying
    space is this small. Rejection sampling fixes it unconditionally, without
    having to enlarge the render space: keep advancing the eval seed past its
    starting range and skip any candidate whose hash already exists in train
    or in the eval set built so far, until `n` genuinely-unique examples are
    collected. Returns the eval set and how many candidates were rejected,
    since that count is itself the honest measure of how crowded the space is.
    """
    train_hashes = {ex["pixel_hash"] for ex in train}
    eval_hashes: set[str] = set()
    eval_examples: list[dict] = []
    rejected = 0
    seed = seed_start
    while len(eval_examples) < n:
        ex = make_example(seed)
        if ex["pixel_hash"] in train_hashes or ex["pixel_hash"] in eval_hashes:
            rejected += 1
        else:
            eval_hashes.add(ex["pixel_hash"])
            eval_examples.append(ex)
        seed += 1
    return eval_examples, rejected


def distribution(examples: list[dict]) -> dict:
    counts = {"num_shapes": {}, "shape_type": {}, "color": {}, "question_type": {}}
    for ex in examples:
        n = len(ex["shapes"])
        counts["num_shapes"][n] = counts["num_shapes"].get(n, 0) + 1
        for s in ex["shapes"]:
            counts["shape_type"][s["shape"]] = counts["shape_type"].get(s["shape"], 0) + 1
            counts["color"][s["color"]] = counts["color"].get(s["color"], 0) + 1
        for q in ex["qa"]:
            counts["question_type"][q["type"]] = counts["question_type"].get(q["type"], 0) + 1
    return counts


def cmd_dataset(args: argparse.Namespace) -> None:
    t0 = time.perf_counter()
    train = [make_example(s) for s in range(args.train_start, args.train_start + args.train)]
    train_dupes = len(train) - len({ex["pixel_hash"] for ex in train})
    eval_, rejected = make_eval_set_disjoint_from(train, args.eval, args.eval_start)
    elapsed = time.perf_counter() - t0

    out = Path(args.out)
    write_jsonl(train, out / "train.jsonl")
    write_jsonl(eval_, out / "eval.jsonl")

    collisions = check_disjoint(train, eval_)

    print(f"train examples : {len(train)}")
    print(f"eval examples  : {len(eval_)}")
    print(f"wall-clock     : {elapsed:.3f}s")
    print(f"train-internal pixel-hash duplicates: {train_dupes}")
    print(f"eval candidates rejected for colliding with train (or a prior eval draw): {rejected}")
    print(f"pixel-hash collisions between train and eval (must be 0): {collisions}")
    print("\ntrain distribution:")
    print(json.dumps(distribution(train), indent=2))
    print("\neval distribution:")
    print(json.dumps(distribution(eval_), indent=2))


def cmd_fixtures(args: argparse.Namespace) -> None:
    out = Path(args.out)
    images_dir = out / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for seed in range(args.fixtures):
        ex = make_example(seed + args.fixtures_seed_start)
        ppm_path = images_dir / f"{ex['id']}.ppm"
        pixels = [tuple(px) for px in ex["pixels_rgb"]]
        ppm_path.write_bytes(to_ppm_bytes(pixels))
        manifest.append(
            {
                "id": ex["id"],
                "seed": ex["seed"],
                "image": f"images/{ex['id']}.ppm",
                "shapes": ex["shapes"],
                "qa": ex["qa"],
                "pixel_hash": ex["pixel_hash"],
            }
        )
    write_jsonl(manifest, out / "manifest.jsonl")
    print(f"wrote {len(manifest)} fixture images to {images_dir}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    dataset = sub.add_parser("dataset", help="generate the full train/eval manifests")
    dataset.add_argument("--train", type=int, default=2000)
    dataset.add_argument("--eval", type=int, default=400)
    dataset.add_argument("--train-start", type=int, default=0)
    dataset.add_argument("--eval-start", type=int, default=100000)
    dataset.add_argument("--out", type=Path, default=Path("../data/raw"))
    dataset.set_defaults(func=cmd_dataset)

    fixtures = sub.add_parser("fixtures", help="write a small committed sample with real .ppm files")
    fixtures.add_argument("--fixtures", type=int, default=8)
    fixtures.add_argument("--fixtures-seed-start", type=int, default=0)
    fixtures.add_argument("--out", type=Path, default=Path("../fixtures"))
    fixtures.set_defaults(func=cmd_fixtures)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
