"""Do the two hard axes compose, or does one of them dominate?

Stage 04 doubled the clip length and held the scene at one object. Stage 05
doubled the object count and held the clip at 8 frames. Both cleared the
frame-repeat baseline, and both said in as many words that the combination
was untested. `mission.yaml` names the follow-on as "longer sequences
(16-32 frames) **and/or** multi-object scenes", so the combination is
inside the declared scope, not an extension of it.

This stage runs 16 frames and 2 occluding objects at once, so that stage 02
(8 frames, 1 object), stage 04 (16 frames, 1 object), stage 05 (8 frames,
2 objects), and this stage form a 2x2 grid. With all four corners measured,
a degradation can be attributed: if the combined cost is close to the sum of
the two individual costs, the difficulties are roughly independent; if it is
much worse, they interact.

Nothing about clip rendering, the codec, or the sequence model is
reimplemented. Stage 05's `make_multi_example`, `composite`, and
`occlusion_stats` produce the clips; stage 01's codec and stage 02's
`train_generation.run()` consume them exactly as every prior stage does.

## The import-order trap this stage had to solve

`generate_multi_object_dataset` does `from generate_video_dataset import
N_FRAMES`, and `video_codec` does the same, and `train_video_codec` and
`train_generation` in turn do `from video_codec import N_FRAMES`. A
from-import copies the *value* into the importing module's namespace at
import time; it does not create a live view of the exporting module's
global. So setting `generate_video_dataset.N_FRAMES = 16` after any of those
modules is imported changes nothing for them.

Stage 04 got away with patching the one module because it imported the rest
afterwards. This stage cannot: stage 05's dataset module has to be imported
to be patched, and it re-exports its own copy. The fix below patches the
source global *before* importing the multi-object module, then patches that
module's own copy as well, and only then imports the codec and generation
modules -- so all four bindings agree on 16. `assert_frame_count_agrees`
checks that rather than trusting it, because a silent disagreement here
would render 16-frame clips and then reshape them as 8-frame tensors.

Usage:
    python train_longer_and_multi_object.py --frames 16 --speed 1 \
        --prompt-frames 8 --codec-steps 800 --lm-steps 400 --seed 0
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
MULTI_CORE = STAGE_DIR.parents[1] / "05-multi-object" / "core"
for p in (DATASET_CORE, CODEC_CORE, LM_CORE, MULTI_CORE):
    sys.path.insert(0, str(p))

# Import order is load-bearing -- see the module docstring. `generate_video_dataset`
# is the single source of N_FRAMES; everything downstream takes a copy.
import generate_video_dataset as dataset_mod


def patch_frame_count(n_frames: int, speed: int):
    """Set the frame count everywhere a copy of it will be taken.

    SPEED cannot stay at stage 00's default of 2 for the same reason stage 04
    found: `_start_range`'s travel distance is `unit * SPEED * (N_FRAMES - 1)`,
    which at 16 frames and speed 2 leaves no valid start position on a 32px
    canvas for several shape/direction combinations. Stage 04 halved it to 1;
    this stage uses the same value so the two are comparable.
    """
    dataset_mod.N_FRAMES = n_frames
    dataset_mod.SPEED = speed

    import generate_multi_object_dataset as multi_mod

    # `multi_mod` took its own copy of N_FRAMES at import time (one line
    # above). `composite` and `occlusion_stats` read that copy, so it needs
    # setting too -- the assignment above does not reach it.
    multi_mod.N_FRAMES = n_frames
    return multi_mod


def assert_frame_count_agrees(n_frames: int, multi_mod) -> dict:
    """Four modules hold four independent copies of this number. Check them.

    A disagreement is not a crash: `load_clips` would reshape a 16-frame clip
    as if it were 8 frames and train on silently corrupted tensors.
    """
    import train_generation as gen_mod
    import train_video_codec as codec_train_mod
    import video_codec as codec_mod

    seen = {
        "generate_video_dataset": dataset_mod.N_FRAMES,
        "generate_multi_object_dataset": multi_mod.N_FRAMES,
        "video_codec": codec_mod.N_FRAMES,
        "train_video_codec": codec_train_mod.N_FRAMES,
        "train_generation": gen_mod.N_FRAMES,
    }
    disagree = {k: v for k, v in seen.items() if v != n_frames}
    assert not disagree, f"frame count disagrees in {disagree}, expected {n_frames} everywhere"
    return seen


def generate_dataset(multi_mod, train_n: int, eval_n: int, out_dir: Path) -> dict:
    t0 = time.perf_counter()
    train = [multi_mod.make_multi_example(s) for s in range(train_n)]
    train_dupes = len(train) - len({ex["clip_hash"] for ex in train})
    eval_, rejected = multi_mod.make_eval_set_disjoint_from(train, eval_n, seed_start=100_000)
    elapsed = time.perf_counter() - t0

    out_dir.mkdir(parents=True, exist_ok=True)
    multi_mod.write_jsonl(train, out_dir / "train.jsonl")
    multi_mod.write_jsonl(eval_, out_dir / "eval.jsonl")

    frame_counts = {ex["n_frames"] for ex in train} | {ex["n_frames"] for ex in eval_}

    return {
        "n_objects": multi_mod.N_OBJECTS,
        "n_frames": multi_mod.N_FRAMES,
        "clip_frame_counts_written": sorted(frame_counts),
        "train_clips": len(train),
        "eval_clips": len(eval_),
        "wall_clock_s": elapsed,
        "train_internal_duplicates": train_dupes,
        "eval_rejected_for_collision": rejected,
        "train_eval_collisions": multi_mod.check_disjoint(train, eval_),
        "train_occlusion": multi_mod.occlusion_summary(train),
        "eval_occlusion": multi_mod.occlusion_summary(eval_),
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

    multi_mod = patch_frame_count(args.frames, args.speed)

    data_dir = STAGE_DIR.parent / "data" / "raw"
    dataset_report = generate_dataset(multi_mod, args.train_clips, args.eval_clips, data_dir)
    assert dataset_report["train_eval_collisions"] == 0, "train/eval leakage -- stop"
    assert dataset_report["clip_frame_counts_written"] == [args.frames], (
        f"clips were written with {dataset_report['clip_frame_counts_written']} frames, "
        f"expected [{args.frames}]"
    )

    import train_video_codec as codec_train_mod

    codec_train_mod.DATA_DIR = data_dir

    import train_generation as gen_mod

    frame_count_bindings = assert_frame_count_agrees(args.frames, multi_mod)

    generation_result = gen_mod.run(
        codec_steps=args.codec_steps,
        lm_steps=args.lm_steps,
        lm_lr=args.lm_lr,
        prompt_frames=args.prompt_frames,
        seed=args.seed,
        out=args.out,
    )

    result = {
        "stage": "06-longer-and-multi-object",
        "frames": args.frames,
        "n_objects": multi_mod.N_OBJECTS,
        "frame_count_bindings": frame_count_bindings,
        "dataset": dataset_report,
        "generation": generation_result,
        "tokenizer_still_binding_constraint": generation_result.get("verdict") == "MET"
        and generation_result["compute"]["ceiling_exceeded"] is False,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    out_path = args.out / f"longer-and-multi-object-seed{args.seed}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
