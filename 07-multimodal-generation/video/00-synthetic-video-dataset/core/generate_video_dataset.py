"""Generate a synthetic short-video dataset, from scratch: one shape moving
in a straight line across a plain canvas, for a fixed number of frames.

This extends mission 05's synthetic image generator along a time axis rather
than building a new renderer. The single-frame drawing primitives
(`_draw_circle`, `_draw_square`, `_draw_triangle`, `to_ppm_bytes`, the shape
and color tables) are imported unmodified from
`01-language-model/vision/00-image-caption-task/core/generate_dataset.py`
-- the same cross-mission `sys.path.insert` convention mission 07 uses to
reuse mission 01's serving engine. What is genuinely new here is temporal:
picking a start position and a direction such that the shape stays fully on
the canvas for every frame of the clip, and rendering the resulting sequence.

Each clip's condition is a `(shape, color, direction)` triple, expressible as
a short prompt ("a red circle moving down_right"), matching the job
`mission.yaml` states: "given a short prompt or seed condition ... generate a
short sequence of frames consistent with that condition." Direction is one of
8 fixed unit vectors (4 cardinal, 4 diagonal) at a constant fixed speed --
deterministic bounds arithmetic replaces any collision or clipping code.

Two disjoint seed ranges produce train and eval; a SHA-256 hash of each
clip's full concatenated frame bytes checks, programmatically, that no eval
clip is byte-identical to any training clip -- same guardrail, same rejection-
sampling fix mission 05 stage 00 already needed for its single-frame case,
now applied to whole clips.

Usage:
    python generate_video_dataset.py dataset --train 800 --eval 150 --out ../data/raw
    python generate_video_dataset.py fixtures --fixtures 6 --out ../fixtures
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

IMAGE_CORE = (
    Path(__file__).resolve().parents[4]
    / "01-language-model"
    / "vision"
    / "00-image-caption-task"
    / "core"
)
sys.path.insert(0, str(IMAGE_CORE))
from generate_dataset import (
    BACKGROUND,
    COLOR_NAMES,
    COLORS,
    SHAPES,
    _draw_circle,
    _draw_square,
    _draw_triangle,
    to_ppm_bytes,
)

WIDTH = HEIGHT = 32
N_FRAMES = 8
SPEED = 2
HALF_SIZES = (3, 4, 5)

_DRAW = {"square": _draw_square, "circle": _draw_circle, "triangle": _draw_triangle}

# 8 fixed unit directions: 4 cardinal, 4 diagonal. (dx, dy); +y is down, matching
# the pixel-buffer row-major convention `to_ppm_bytes` already assumes.
DIRECTIONS = {
    "right": (1, 0),
    "left": (-1, 0),
    "down": (0, 1),
    "up": (0, -1),
    "down_right": (1, 1),
    "down_left": (-1, 1),
    "up_right": (1, -1),
    "up_left": (-1, -1),
}
DIRECTION_NAMES = list(DIRECTIONS)


@dataclass
class MotionClip:
    shape: str
    color: str
    half: int
    direction: str
    speed: int
    x0: int
    y0: int


def _start_range(unit: int, half: int, span: int) -> tuple[int, int]:
    """Valid start-coordinate range so the shape stays on-canvas for every
    frame, given a fixed per-frame step of `unit * SPEED` over `N_FRAMES`."""
    travel = unit * SPEED * (N_FRAMES - 1)
    lo, hi = half, span - 1 - half
    if travel > 0:
        hi -= travel
    elif travel < 0:
        lo -= travel
    return lo, hi


def sample_clip(rng) -> MotionClip:
    shape = rng.choice(SHAPES)
    color = rng.choice(COLOR_NAMES)
    half = rng.choice(HALF_SIZES)
    direction = rng.choice(DIRECTION_NAMES)
    ux, uy = DIRECTIONS[direction]
    x_lo, x_hi = _start_range(ux, half, WIDTH)
    y_lo, y_hi = _start_range(uy, half, HEIGHT)
    return MotionClip(
        shape=shape,
        color=color,
        half=half,
        direction=direction,
        speed=SPEED,
        x0=rng.randint(x_lo, x_hi),
        y0=rng.randint(y_lo, y_hi),
    )


def render_clip(clip: MotionClip) -> list[list[tuple[int, int, int]]]:
    ux, uy = DIRECTIONS[clip.direction]
    frames = []
    for t in range(N_FRAMES):
        pixels = [BACKGROUND] * (WIDTH * HEIGHT)
        cx = clip.x0 + ux * clip.speed * t
        cy = clip.y0 + uy * clip.speed * t
        _DRAW[clip.shape](pixels, cx, cy, clip.half, COLORS[clip.color])
        frames.append(pixels)
    return frames


def clip_hash(frames: list[list[tuple[int, int, int]]]) -> str:
    h = hashlib.sha256()
    for frame in frames:
        h.update(bytes(b for px in frame for b in px))
    return h.hexdigest()


def make_example(seed: int) -> dict:
    import random

    rng = random.Random(seed)
    clip = sample_clip(rng)
    frames = render_clip(clip)
    return {
        "id": f"vid-{seed}",
        "seed": seed,
        "width": WIDTH,
        "height": HEIGHT,
        "n_frames": N_FRAMES,
        "prompt": f"a {clip.color} {clip.shape} moving {clip.direction}",
        "motion": asdict(clip),
        "clip_hash": clip_hash(frames),
        "frames_pixels_rgb": [[list(px) for px in frame] for frame in frames],
    }


def write_jsonl(examples: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for ex in examples:
            fh.write(json.dumps(ex) + "\n")


def make_eval_set_disjoint_from(train: list[dict], n: int, seed_start: int) -> tuple[list[dict], int]:
    """Same rejection-sampling fix mission 05 stage 00 needed: disjoint seed
    ranges do not imply disjoint clips when the render space is this small,
    so keep drawing past the starting seed and skip any clip whose full-clip
    hash already exists in train or in the eval set built so far."""
    train_hashes = {ex["clip_hash"] for ex in train}
    eval_hashes: set[str] = set()
    eval_examples: list[dict] = []
    rejected = 0
    seed = seed_start
    while len(eval_examples) < n:
        ex = make_example(seed)
        if ex["clip_hash"] in train_hashes or ex["clip_hash"] in eval_hashes:
            rejected += 1
        else:
            eval_hashes.add(ex["clip_hash"])
            eval_examples.append(ex)
        seed += 1
    return eval_examples, rejected


def check_disjoint(train: list[dict], eval_: list[dict]) -> int:
    train_hashes = {ex["clip_hash"] for ex in train}
    eval_hashes = {ex["clip_hash"] for ex in eval_}
    return len(train_hashes & eval_hashes)


def distribution(examples: list[dict]) -> dict:
    counts = {"direction": {}, "shape": {}, "color": {}}
    for ex in examples:
        m = ex["motion"]
        counts["direction"][m["direction"]] = counts["direction"].get(m["direction"], 0) + 1
        counts["shape"][m["shape"]] = counts["shape"].get(m["shape"], 0) + 1
        counts["color"][m["color"]] = counts["color"].get(m["color"], 0) + 1
    return counts


def cmd_dataset(args: argparse.Namespace) -> None:
    t0 = time.perf_counter()
    train = [make_example(s) for s in range(args.train_start, args.train_start + args.train)]
    train_dupes = len(train) - len({ex["clip_hash"] for ex in train})
    eval_, rejected = make_eval_set_disjoint_from(train, args.eval, args.eval_start)
    elapsed = time.perf_counter() - t0

    out = Path(args.out)
    write_jsonl(train, out / "train.jsonl")
    write_jsonl(eval_, out / "eval.jsonl")

    collisions = check_disjoint(train, eval_)

    print(f"train clips    : {len(train)}")
    print(f"eval clips     : {len(eval_)}")
    print(f"frames/clip    : {N_FRAMES}")
    print(f"wall-clock     : {elapsed:.3f}s")
    print(f"train-internal clip-hash duplicates: {train_dupes}")
    print(f"eval candidates rejected for colliding with train (or a prior eval draw): {rejected}")
    print(f"clip-hash collisions between train and eval (must be 0): {collisions}")
    print("\ntrain distribution:")
    print(json.dumps(distribution(train), indent=2))
    print("\neval distribution:")
    print(json.dumps(distribution(eval_), indent=2))


def cmd_fixtures(args: argparse.Namespace) -> None:
    out = Path(args.out)
    frames_dir = out / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for seed in range(args.fixtures):
        ex = make_example(seed + args.fixtures_seed_start)
        frame_paths = []
        for t, frame in enumerate(ex["frames_pixels_rgb"]):
            pixels = [tuple(px) for px in frame]
            ppm_path = frames_dir / f"{ex['id']}_frame{t}.ppm"
            ppm_path.write_bytes(to_ppm_bytes(pixels))
            frame_paths.append(f"frames/{ppm_path.name}")
        manifest.append(
            {
                "id": ex["id"],
                "seed": ex["seed"],
                "prompt": ex["prompt"],
                "motion": ex["motion"],
                "frames": frame_paths,
                "clip_hash": ex["clip_hash"],
            }
        )
    write_jsonl(manifest, out / "manifest.jsonl")
    print(f"wrote {len(manifest)} fixture clips ({N_FRAMES} frames each) to {frames_dir}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    dataset = sub.add_parser("dataset", help="generate the full train/eval manifests")
    dataset.add_argument("--train", type=int, default=800)
    dataset.add_argument("--eval", type=int, default=150)
    dataset.add_argument("--train-start", type=int, default=0)
    dataset.add_argument("--eval-start", type=int, default=100000)
    dataset.add_argument("--out", type=Path, default=Path("../data/raw"))
    dataset.set_defaults(func=cmd_dataset)

    fixtures = sub.add_parser("fixtures", help="write a small committed sample with real .ppm frames")
    fixtures.add_argument("--fixtures", type=int, default=6)
    fixtures.add_argument("--fixtures-seed-start", type=int, default=0)
    fixtures.add_argument("--out", type=Path, default=Path("../fixtures"))
    fixtures.set_defaults(func=cmd_fixtures)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
