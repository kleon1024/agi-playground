"""Two independently-moving shapes per clip, composited onto one frame
sequence with real occlusion -- the other half of mission.yaml's named
follow-on ("longer sequences (16-32 frames) and/or multi-object scenes
(2+ moving shapes, occlusion)"), companion to stage 04 which tested the
frame-count half of that same sentence.

Nothing about single-object rendering is reimplemented. `sample_clip` and
`render_clip` are imported unmodified from stage 00 -- `sample_clip` is
called once per object to get an independent `MotionClip`, and
`render_clip` is called once per object to get that object's own full
8-frame sequence against stage 00's plain white background. What is new
here is `composite`: layering two such single-object frame stacks into one
scene, later-sampled object on top, and `occlusion_stats`: a real,
computed measure of how often the two objects' shapes actually overlap,
since a multi-object test that never produces overlapping shapes would not
test occlusion at all.

Usage:
    python generate_multi_object_dataset.py dataset --train 800 --eval 150 --out ../data/raw
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import asdict
from pathlib import Path

DATASET_CORE = (
    Path(__file__).resolve().parents[2] / "00-synthetic-video-dataset" / "core"
)
sys.path.insert(0, str(DATASET_CORE))
from generate_video_dataset import (
    BACKGROUND,
    HEIGHT,
    N_FRAMES,
    WIDTH,
    render_clip,
    sample_clip,
)

N_OBJECTS = 2


def composite(per_object_frames: list[list[list[tuple[int, int, int]]]]) -> list[list[tuple[int, int, int]]]:
    """Layer each object's own rendered frame stack into one scene, later
    object on top. A pixel keeps the topmost object's color wherever that
    object drew something other than background; otherwise it falls through
    to the next object down, or to background if none drew there."""
    frames = []
    for t in range(N_FRAMES):
        scene = [BACKGROUND] * (WIDTH * HEIGHT)
        for obj_frames in per_object_frames:  # bottom to top
            frame = obj_frames[t]
            for i, px in enumerate(frame):
                if px != BACKGROUND:
                    scene[i] = px
        frames.append(scene)
    return frames


def occlusion_stats(per_object_frames: list[list[list[tuple[int, int, int]]]]) -> dict:
    """How often does more than one object draw the same pixel in the same
    frame -- the only thing that makes this a real occlusion test rather
    than two shapes that happen never to touch."""
    overlapping_pixels = 0
    total_pixels = 0
    frames_with_overlap = 0
    for t in range(N_FRAMES):
        frame_has_overlap = False
        for i in range(WIDTH * HEIGHT):
            n_drawn = sum(1 for obj_frames in per_object_frames if obj_frames[t][i] != BACKGROUND)
            total_pixels += 1
            if n_drawn >= 2:
                overlapping_pixels += 1
                frame_has_overlap = True
        if frame_has_overlap:
            frames_with_overlap += 1
    return {
        "overlapping_pixel_fraction": overlapping_pixels / total_pixels,
        "frames_with_any_overlap": frames_with_overlap,
        "n_frames": N_FRAMES,
        "any_frame_overlap": frames_with_overlap > 0,
    }


def make_multi_example(seed: int, n_objects: int = N_OBJECTS) -> dict:
    rng = random.Random(seed)
    clips = [sample_clip(rng) for _ in range(n_objects)]
    per_object_frames = [render_clip(c) for c in clips]
    frames = composite(per_object_frames)
    occlusion = occlusion_stats(per_object_frames)
    prompt = " and ".join(f"a {c.color} {c.shape} moving {c.direction}" for c in clips)
    return {
        "id": f"multivid-{seed}",
        "seed": seed,
        "width": WIDTH,
        "height": HEIGHT,
        "n_frames": N_FRAMES,
        "n_objects": n_objects,
        "prompt": prompt,
        "motion": [asdict(c) for c in clips],
        "clip_hash": clip_hash(frames),
        "occlusion": occlusion,
        "frames_pixels_rgb": [[list(px) for px in frame] for frame in frames],
    }


def clip_hash(frames: list[list[tuple[int, int, int]]]) -> str:
    import hashlib

    h = hashlib.sha256()
    for frame in frames:
        h.update(bytes(b for px in frame for b in px))
    return h.hexdigest()


def write_jsonl(examples: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for ex in examples:
            fh.write(json.dumps(ex) + "\n")


def make_eval_set_disjoint_from(train: list[dict], n: int, seed_start: int) -> tuple[list[dict], int]:
    """Same rejection-sampling fix stage 00 already needed, reapplied here
    since a multi-object clip-hash collision is exactly as possible as a
    single-object one."""
    train_hashes = {ex["clip_hash"] for ex in train}
    eval_hashes: set[str] = set()
    eval_examples: list[dict] = []
    rejected = 0
    seed = seed_start
    while len(eval_examples) < n:
        ex = make_multi_example(seed)
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


def occlusion_summary(examples: list[dict]) -> dict:
    fractions = [ex["occlusion"]["overlapping_pixel_fraction"] for ex in examples]
    any_overlap = [ex["occlusion"]["any_frame_overlap"] for ex in examples]
    return {
        "n_clips": len(examples),
        "clips_with_any_occluded_frame": sum(any_overlap),
        "clips_with_any_occluded_frame_fraction": sum(any_overlap) / len(examples),
        "mean_overlapping_pixel_fraction": sum(fractions) / len(examples),
        "max_overlapping_pixel_fraction": max(fractions),
    }


def cmd_dataset(args: argparse.Namespace) -> None:
    t0 = time.perf_counter()
    train = [make_multi_example(s) for s in range(args.train_start, args.train_start + args.train)]
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
    print(f"objects/clip   : {N_OBJECTS}")
    print(f"wall-clock     : {elapsed:.3f}s")
    print(f"train-internal clip-hash duplicates: {train_dupes}")
    print(f"eval candidates rejected for colliding with train (or a prior eval draw): {rejected}")
    print(f"clip-hash collisions between train and eval (must be 0): {collisions}")
    print("\ntrain occlusion:")
    print(json.dumps(occlusion_summary(train), indent=2))
    print("\neval occlusion:")
    print(json.dumps(occlusion_summary(eval_), indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dataset")
    d.add_argument("--train", type=int, default=800)
    d.add_argument("--train-start", type=int, default=0)
    d.add_argument("--eval", type=int, default=150)
    d.add_argument("--eval-start", type=int, default=100_000)
    d.add_argument("--out", type=Path, default=Path("../data/raw"))
    d.set_defaults(func=cmd_dataset)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
