"""Does the feasibility finding survive two independently-moving, occluding
shapes per clip instead of one?

Stage 04 tested the other half of mission.yaml's named follow-on (longer
sequences); this stage tests the half stage 04 explicitly left open:
multi-object scenes with occlusion, still 8 frames, still procedurally
generated. The real risk here is different in kind from stage 04's: doubling
frame count changed a shape parameter every reused function already read
dynamically, but two objects sharing one 32-dimensional per-frame latent
(stage 01's `Encoder` output) and one 64-entry codebook token is a genuine
capacity question -- nothing about `video_codec.py` or `video_lm.py`
guarantees a single per-frame token can represent two shapes' positions at
once, and mission.yaml's own acceptance criteria treat an honest `NOT_MET`
here as a legitimate, mission-complete outcome, not a failure to hide.

Nothing in `video_codec.py`, `train_video_codec.py`, or `video_lm.py` is
reimplemented. The codec's `Encoder`/`Decoder` operate on raw `(B, T, 3, H, W)`
pixel tensors and have no notion of "how many shapes" produced those pixels;
the LM's `build_lm_dataset`/`train_lm`/`generate_greedy` operate on codec
tokens and a `Config`, equally agnostic to scene content. This stage's own
`generate_multi_object_dataset.py` produces clips in the exact same JSONL
schema stage 00 does (`frames_pixels_rgb`, `n_frames`, `clip_hash`, ...), so
`train_video_codec.load_clips` reads them unmodified once `DATA_DIR` is
patched to this stage's own data directory -- the same monkeypatch-then-call
pattern stage 04 established.

Usage:
    python train_multi_object.py --train-clips 800 --eval-clips 150 \
        --codec-steps 800 --lm-steps 400 --prompt-frames 4 --seed 0
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

import generate_multi_object_dataset as multi_mod


def generate_dataset(train_n: int, eval_n: int, out_dir: Path) -> dict:
    t0 = time.perf_counter()
    train = [multi_mod.make_multi_example(s) for s in range(train_n)]
    train_dupes = len(train) - len({ex["clip_hash"] for ex in train})
    eval_, rejected = multi_mod.make_eval_set_disjoint_from(train, eval_n, seed_start=100_000)
    elapsed = time.perf_counter() - t0

    out_dir.mkdir(parents=True, exist_ok=True)
    multi_mod.write_jsonl(train, out_dir / "train.jsonl")
    multi_mod.write_jsonl(eval_, out_dir / "eval.jsonl")
    collisions = multi_mod.check_disjoint(train, eval_)

    return {
        "n_objects": multi_mod.N_OBJECTS,
        "train_clips": len(train),
        "eval_clips": len(eval_),
        "wall_clock_s": elapsed,
        "train_internal_duplicates": train_dupes,
        "eval_rejected_for_collision": rejected,
        "train_eval_collisions": collisions,
        "train_occlusion": multi_mod.occlusion_summary(train),
        "eval_occlusion": multi_mod.occlusion_summary(eval_),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train-clips", type=int, default=800)
    ap.add_argument("--eval-clips", type=int, default=150)
    ap.add_argument("--codec-steps", type=int, default=800)
    ap.add_argument("--lm-steps", type=int, default=400)
    ap.add_argument("--lm-lr", type=float, default=3e-3)
    ap.add_argument("--prompt-frames", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=Path("../runs"))
    args = ap.parse_args()

    data_dir = STAGE_DIR.parent / "data" / "raw"
    dataset_report = generate_dataset(args.train_clips, args.eval_clips, data_dir)
    assert dataset_report["train_eval_collisions"] == 0, "train/eval leakage -- stop"

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
        "stage": "05-multi-object",
        "n_objects": multi_mod.N_OBJECTS,
        "dataset": dataset_report,
        "generation": generation_result,
        "tokenizer_still_binding_constraint": generation_result.get("verdict") == "MET"
        and generation_result["compute"]["ceiling_exceeded"] is False,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    out_path = args.out / f"multi-object-seed{args.seed}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
