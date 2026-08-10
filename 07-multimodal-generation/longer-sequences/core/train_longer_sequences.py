"""Does stage 02's feasibility finding hold at 16 frames instead of 8?

Stage 03's report measured stage 02's real headroom: 152.5s against a
1800s ceiling, 8.5% used. It also flagged, without testing, that the
tokenizer's per-frame conv cost scales roughly linearly with frame count
while the sequence model's attention cost scales quadratically -- negligible
at 9 tokens, not necessarily negligible further out. This stage spends part
of that headroom to find out, on real hardware, at N_FRAMES = 16 (double
stage 00-02's clip length), still single-object, still procedurally
generated.

Nothing in `video_codec.py` or `video_lm.py` is reimplemented. Both files'
classes and functions already read frame count from the data (`Encoder`/
`Decoder` take `B, T = frames.shape[:2]` at call time; `build_lm_dataset`/
`build_lm_config`/`train_lm`/`generate_greedy` all derive their shapes from
the tensors and config they are given, never a hardcoded 8) -- only two
`assert N_FRAMES == 8` guards existed to record that stage 00-02's own
numbers assume 8, and both were relaxed to `assert N_FRAMES >= 1` (see
01-video-tokenizer/core/video_codec.py and
02-generation-model/core/video_lm.py) since the change makes no functional
difference to the existing verified stage 00-02 result -- their own runs
still default to N_FRAMES == 8, satisfying `>= 1` exactly the same as `== 8`
did.

This stage reuses every one of those functions completely unmodified. It
sets `generate_video_dataset.N_FRAMES = 16` and `train_video_codec.DATA_DIR`
to this stage's own data directory -- both plain module globals every reused
function already reads dynamically at call time, not at import time -- then
calls stage 00's own dataset-generation functions and stage 02's own
`train_generation.run()` exactly as stage 02 does. Same codec architecture,
same LM architecture, same training loop, same evaluation, same
frame-repeat baseline, only the clip length is different.

Usage:
    python train_longer_sequences.py --frames 16 --codec-steps 800 --lm-steps 400 \
        --prompt-frames 8 --seed 0
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

STAGE_DIR = Path(__file__).resolve().parent
DATASET_CORE = STAGE_DIR.parents[1] / "00-synthetic-video-dataset" / "core"
CODEC_CORE = STAGE_DIR.parents[1] / "01-video-tokenizer" / "core"
LM_CORE = STAGE_DIR.parents[1] / "02-generation-model" / "core"
for p in (DATASET_CORE, CODEC_CORE, LM_CORE):
    sys.path.insert(0, str(p))

import generate_video_dataset as dataset_mod


def generate_dataset(n_frames: int, speed: int, train_n: int, eval_n: int, out_dir: Path) -> dict:
    """Reuses stage 00's own sample_clip/render_clip/make_example/write_jsonl/
    make_eval_set_disjoint_from/check_disjoint/distribution functions
    unmodified, with N_FRAMES (and, necessarily, SPEED) patched before any of
    them run -- they all read these as module globals at call time (bare
    names resolved against the module's own namespace), not values captured
    at import time, so this is a real, correctly-scoped extension, not a
    partial one.

    SPEED cannot stay at stage 00's default of 2: `_start_range`'s travel
    distance is `unit * SPEED * (N_FRAMES - 1)`, and at N_FRAMES=16 with
    SPEED=2 that is up to 30px on a 32px canvas -- `randint(x_lo, x_hi)`
    raised `ValueError: empty range` the first time this ran, confirmed by
    hand: for a half-size-5 shape moving at unit speed 2 for 15 steps,
    `hi = 32 - 1 - 5 - 30 = -4 < lo = 5`, no valid start position exists for
    several direction/size combinations. Halving SPEED to 1 keeps travel at
    `1 * 1 * 15 = 15`, close to stage 00's own `1 * 2 * 7 = 14`, restoring a
    non-empty valid range for every direction and half-size this dataset
    samples."""
    dataset_mod.N_FRAMES = n_frames
    dataset_mod.SPEED = speed

    t0 = time.perf_counter()
    train = [dataset_mod.make_example(s) for s in range(train_n)]
    train_dupes = len(train) - len({ex["clip_hash"] for ex in train})
    eval_, rejected = dataset_mod.make_eval_set_disjoint_from(train, eval_n, seed_start=100_000)
    elapsed = time.perf_counter() - t0

    out_dir.mkdir(parents=True, exist_ok=True)
    dataset_mod.write_jsonl(train, out_dir / "train.jsonl")
    dataset_mod.write_jsonl(eval_, out_dir / "eval.jsonl")
    collisions = dataset_mod.check_disjoint(train, eval_)

    return {
        "n_frames": n_frames,
        "speed": speed,
        "train_clips": len(train),
        "eval_clips": len(eval_),
        "wall_clock_s": elapsed,
        "train_internal_duplicates": train_dupes,
        "eval_rejected_for_collision": rejected,
        "train_eval_collisions": collisions,
        "train_distribution": dataset_mod.distribution(train),
        "eval_distribution": dataset_mod.distribution(eval_),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frames", type=int, default=16)
    ap.add_argument("--speed", type=int, default=1)
    ap.add_argument("--train-clips", type=int, default=800)
    ap.add_argument("--eval-clips", type=int, default=150)
    ap.add_argument("--codec-steps", type=int, default=800)
    ap.add_argument("--lm-steps", type=int, default=400)
    ap.add_argument("--lm-lr", type=float, default=3e-3)
    ap.add_argument("--prompt-frames", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("../runs"))
    args = ap.parse_args()

    data_dir = STAGE_DIR.parent / "data" / "raw"
    dataset_report = generate_dataset(args.frames, args.speed, args.train_clips, args.eval_clips, data_dir)
    assert dataset_report["train_eval_collisions"] == 0, "train/eval leakage -- stop"

    # Both reused modules read N_FRAMES / DATA_DIR as plain globals at call
    # time, so patching them here (after dataset_mod.N_FRAMES is already 16)
    # correctly propagates to every function stage 01/02 already wrote.
    import train_video_codec as codec_train_mod

    codec_train_mod.DATA_DIR = data_dir

    import train_generation as gen_mod

    generation_result = gen_mod.run(
        codec_steps=args.codec_steps,
        lm_steps=args.lm_steps,
        lm_lr=args.lm_lr,
        prompt_frames=args.prompt_frames,
        seed=args.seed,
        out=args.out,
    )

    result = {
        "stage": "04-longer-sequences",
        "frames": args.frames,
        "dataset": dataset_report,
        "generation": generation_result,
        "tokenizer_still_binding_constraint": generation_result.get("verdict") == "MET"
        and generation_result["compute"]["ceiling_exceeded"] is False,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    out_path = args.out / f"longer-sequences-frames{args.frames}-seed{args.seed}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
