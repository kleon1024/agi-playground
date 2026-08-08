"""Real speech, in place of stage 00's procedural tones: LibriSpeech
`dev-clean` (Panayotov et al., 2015; CC BY 4.0), sliced to a bounded
utterance count so training stays comparable in wall-clock to the existing
procedural-tone runs. Downloaded once via stdlib `urllib`/`tarfile` (same pattern
`03-quantitative-research/00-market-data/core/point_in_time.py`
uses for its own external fetch), cached under a git-ignored `.cache/`
directory next to this file -- never committed.

Note on the served mix: `build_dataset` slices the first `max_utterances`
files off a speaker-major list, so with two or more speakers requested the
served data collapses toward the first speaker in the request order. This
stage's recorded runs requested speakers 2277 and 2035 and were served
speaker 2277 only (a [mix audit](../../04-multi-speaker/when-the-mix-is-not-what-you-asked/)
replays the call); stage 04's `build_balanced_dataset` bounds utterances per
speaker instead.

FLAC has no stdlib decoder, so this is the one stage in this mission that
shells out to an external binary (`ffmpeg`, already present on this host) to
convert each clip to 8kHz mono 16-bit PCM WAV, which stdlib `wave` (the same
module `audio_data.write_wav` uses) can then read directly. Everything after
that decode step -- resampling target, chunking, tensor conversion -- is
plain Python/torch, no audio library dependency.

Kept at the exact same `SAMPLE_RATE`/`CLIP_LEN` as
`00-audio-codec/core/audio_data.py` so stage 00's `Codec`/`CodecConfig`
(DOWNSAMPLE=64 baked into 6 stride-2 conv layers) apply unchanged -- the
whole point of this stage is the same architecture on harder input, not a
resized one.
"""

from __future__ import annotations

import subprocess
import tarfile
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path

import torch

SAMPLE_RATE = 8000
CLIP_LEN = 4096  # matches audio_data.CLIP_LEN so the stage-00 codec applies unchanged

ARCHIVE_URL = "https://www.openslr.org/resources/12/dev-clean.tar.gz"
CACHE_DIR = Path(__file__).resolve().parent / ".cache" / "librispeech"
ARCHIVE_PATH = CACHE_DIR / "dev-clean.tar.gz"
DEFAULT_SPEAKERS = ("2277", "2035")


@dataclass
class SpeechClip:
    waveform: torch.Tensor  # (CLIP_LEN,), float32 in [-1, 1]
    speaker_id: str
    utterance_id: str
    chunk_index: int


def _download_archive() -> None:
    if ARCHIVE_PATH.exists():
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(ARCHIVE_URL, timeout=120) as response:
        ARCHIVE_PATH.write_bytes(response.read())


def _extract_speakers(speakers: tuple[str, ...]) -> list[Path]:
    extract_root = CACHE_DIR / "extracted"
    speaker_root = extract_root / "LibriSpeech" / "dev-clean"
    if not speaker_root.exists() or not all((speaker_root / s).exists() for s in speakers):
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tf:
            members = [
                m
                for m in tf.getmembers()
                if any(m.name.startswith(f"LibriSpeech/dev-clean/{s}/") for s in speakers)
            ]
            tf.extractall(extract_root, members=members)
    flac_files: list[Path] = []
    for s in speakers:
        flac_files.extend(sorted((speaker_root / s).rglob("*.flac")))
    return flac_files


def _decode_flac_to_wav(flac_path: Path) -> Path:
    wav_path = flac_path.with_suffix(".8k.wav")
    if not wav_path.exists():
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", str(flac_path),
                "-ar", str(SAMPLE_RATE), "-ac", "1", "-sample_fmt", "s16",
                str(wav_path),
            ],
            check=True,
        )
    return wav_path


def _load_wav_as_tensor(wav_path: Path) -> torch.Tensor:
    with wave.open(str(wav_path), "rb") as f:
        assert f.getframerate() == SAMPLE_RATE, f"expected {SAMPLE_RATE}Hz, got {f.getframerate()}"
        assert f.getnchannels() == 1
        raw = f.readframes(f.getnframes())
    samples = torch.frombuffer(bytearray(raw), dtype=torch.int16).float() / 32768.0
    return samples


def _chunk(waveform: torch.Tensor, speaker_id: str, utterance_id: str) -> list[SpeechClip]:
    n_chunks = waveform.shape[0] // CLIP_LEN
    clips = []
    for i in range(n_chunks):
        chunk = waveform[i * CLIP_LEN : (i + 1) * CLIP_LEN]
        peak = chunk.abs().max()
        if peak < 1e-4:  # skip near-silent chunks (leading/trailing padding, inter-word gaps)
            continue
        chunk = chunk / (peak + 1e-6) * 0.9
        clips.append(SpeechClip(waveform=chunk, speaker_id=speaker_id, utterance_id=utterance_id, chunk_index=i))
    return clips


def build_dataset(
    n_train: int, n_eval: int, seed: int, speakers: tuple[str, ...] = DEFAULT_SPEAKERS, max_utterances: int = 40
) -> tuple[list[SpeechClip], list[SpeechClip]]:
    """Downloads (if not cached), decodes, and chunks real speech into the
    same fixed-length clip format `audio_data.build_dataset` produces, so
    every downstream consumer (`Codec`, `audio_lm`, `streaming_decode`)
    needs zero changes. `max_utterances` bounds wall-clock -- this mission's
    guardrail is "a bounded utterance set, minutes not hours," not "use the
    whole corpus."
    """
    _download_archive()
    flac_files = _extract_speakers(speakers)[:max_utterances]

    all_clips: list[SpeechClip] = []
    for flac_path in flac_files:
        wav_path = _decode_flac_to_wav(flac_path)
        waveform = _load_wav_as_tensor(wav_path)
        speaker_id = flac_path.parts[flac_path.parts.index("dev-clean") + 1]
        all_clips.extend(_chunk(waveform, speaker_id=speaker_id, utterance_id=flac_path.stem))

    generator = torch.Generator().manual_seed(seed)
    perm = torch.randperm(len(all_clips), generator=generator).tolist()
    shuffled = [all_clips[i] for i in perm]

    total_needed = n_train + n_eval
    if len(shuffled) < total_needed:
        raise RuntimeError(
            f"only {len(shuffled)} real-speech clips available from {len(flac_files)} utterances "
            f"({speakers}); need {total_needed}. Raise max_utterances or add a speaker."
        )
    return shuffled[:n_train], shuffled[n_train : n_train + n_eval]
