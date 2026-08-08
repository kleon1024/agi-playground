"""Audit: does the dataset builder serve the speakers it was asked for?

Measures the served per-speaker mix of the naive speaker-major builder
(`speech_data.build_dataset`) against the balanced builder
(`multi_speaker_data.build_balanced_dataset`) at the exact sizes the stages
use. This is the case-finding step for the "the mix is not what you asked
for" failure mode: count served speakers per split, never trust the
requested list.

Runs entirely from the git-ignored LibriSpeech cache that stages 03 and 04
already populated (130 decoded `.8k.wav` files), so it needs no network and
no new ffmpeg decode. Output is a per-probe table printed to stdout and a
JSON record written to `runs/`.
"""

from __future__ import annotations

import collections
import json
import sys
import time
from pathlib import Path

import torch  # noqa: F401  (speech_data imports it at module scope)

HERE = Path(__file__).resolve().parent
STAGE03_CORE = HERE.parents[2] / "03-real-speech-and-network" / "core"
STAGE04_CORE = HERE.parents[1] / "core"
sys.path.insert(0, str(STAGE03_CORE))
sys.path.insert(0, str(STAGE04_CORE))

import multi_speaker_data as msd
import speech_data as sd


def served_speaker_counts(clips: list) -> dict[str, int]:
    return dict(sorted(collections.Counter(c.speaker_id for c in clips).items()))


def main() -> None:
    results: dict = {
        "date": "2026-08-08",
        "cache_state": "all probes served from the existing git-ignored LibriSpeech cache",
    }

    # Mechanism, no decode: the first `max_utterances` files of the
    # speaker-major list, which is what the naive builder slices.
    flac_files = sd._extract_speakers(msd.TEN_SPEAKERS)[:40]
    slice_speakers = dict(
        sorted(
            collections.Counter(
                p.parts[p.parts.index("dev-clean") + 1] for p in flac_files
            ).items()
        )
    )
    results["probe_0_slice_mechanism"] = {
        "requested_speakers": list(msd.TEN_SPEAKERS),
        "first_40_utterances_by_speaker": slice_speakers,
    }

    # Probe A: stage 03's exact recorded call ("1-2 speakers").
    t0 = time.perf_counter()
    train, eval_ = sd.build_dataset(
        256, 60, seed=0, speakers=("2277", "2035"), max_utterances=40
    )
    results["probe_a_stage03_call"] = {
        "requested_speakers": ["2277", "2035"],
        "served_train": served_speaker_counts(train),
        "served_eval": served_speaker_counts(eval_),
        "wall_clock_s": round(time.perf_counter() - t0, 3),
    }

    # Probe B1: naive 10-speaker call at the stage's own sizes. Either it
    # raises (misleading guidance) or completes silently on one speaker.
    try:
        sd.build_dataset(400, 100, seed=0, speakers=msd.TEN_SPEAKERS, max_utterances=40)
        results["probe_b1_naive_10spk_at_stage_sizes"] = {"outcome": "completed"}
    except RuntimeError as exc:
        results["probe_b1_naive_10spk_at_stage_sizes"] = {
            "outcome": "raised",
            "message": str(exc),
        }

    # Probe B2: a naive 10-speaker call small enough to complete. Serves the
    # same 40 utterances as the slice probe, so the split shows one speaker.
    t0 = time.perf_counter()
    train, eval_ = sd.build_dataset(
        200, 50, seed=0, speakers=msd.TEN_SPEAKERS, max_utterances=40
    )
    results["probe_b2_naive_10spk_completing"] = {
        "requested_speakers": list(msd.TEN_SPEAKERS),
        "served_train": served_speaker_counts(train),
        "served_eval": served_speaker_counts(eval_),
        "wall_clock_s": round(time.perf_counter() - t0, 3),
    }

    # Probe C: the balanced builder, same request, same sizes as stage 04.
    t0 = time.perf_counter()
    train, eval_ = msd.build_balanced_dataset(
        400, 100, seed=0, speakers=msd.TEN_SPEAKERS, per_speaker_utterances=10
    )
    results["probe_c_balanced_10spk"] = {
        "requested_speakers": list(msd.TEN_SPEAKERS),
        "per_speaker_utterances": 10,
        "served_train": served_speaker_counts(train),
        "served_eval": served_speaker_counts(eval_),
        "wall_clock_s": round(time.perf_counter() - t0, 3),
    }

    results["verdict"] = {
        "requested_speakers": 10,
        "naive_first_40_utterance_speakers": len(results["probe_0_slice_mechanism"]["first_40_utterances_by_speaker"]),
        "naive_completing_call_train_speakers": len(results["probe_b2_naive_10spk_completing"]["served_train"]),
        "naive_completing_call_eval_speakers": len(results["probe_b2_naive_10spk_completing"]["served_eval"]),
        "balanced_train_speakers": len(results["probe_c_balanced_10spk"]["served_train"]),
        "balanced_eval_speakers": len(results["probe_c_balanced_10spk"]["served_eval"]),
    }

    print("probe 0  slice mechanism : requested 10 speakers, first 40 utterances ->", results["probe_0_slice_mechanism"]["first_40_utterances_by_speaker"])
    print("probe A  stage-03 call    : requested [2277, 2035], served train ->", results["probe_a_stage03_call"]["served_train"])
    print("                            served eval ->", results["probe_a_stage03_call"]["served_eval"])
    print("probe B1 naive @500 clips :", results["probe_b1_naive_10spk_at_stage_sizes"]["outcome"])
    if results["probe_b1_naive_10spk_at_stage_sizes"]["outcome"] == "raised":
        print("                            message:", results["probe_b1_naive_10spk_at_stage_sizes"]["message"])
    print("probe B2 naive completing : requested 10 speakers, served train ->", results["probe_b2_naive_10spk_completing"]["served_train"])
    print("                            served eval ->", results["probe_b2_naive_10spk_completing"]["served_eval"])
    print("probe C  balanced         : requested 10 speakers, served train ->", results["probe_c_balanced_10spk"]["served_train"])
    print("                            served eval ->", results["probe_c_balanced_10spk"]["served_eval"])
    print("verdict:", results["verdict"])

    runs_dir = HERE.parent / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "2026-08-08-mix-audit.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
